"""
Production-Grade FastAPI Backend for SEO Platform
Integrates: PageAuditor, HumanizationValidator, LLMService, DatabasePool, EdgeCaseHandler, Monitoring

Requirements:
    fastapi, uvicorn, sqlalchemy, pydantic, redis, openai, sentry-sdk, datadog, python-json-logger

Usage:
    uvicorn api:app --host 0.0.0.0 --port 8000 --workers 4 --log-level info
"""

from __future__ import annotations

import os
import logging
import json
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, cast, TYPE_CHECKING
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, Query
from fastapi.responses import JSONResponse, FileResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, validator
import sqlalchemy as sa
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.types import Event, Hint
import csv
from io import StringIO
from urllib.parse import urlparse

from seo_audit import crawl_page, extract_metrics, calculate_score, generate_suggestions

# Import custom modules
# Notes:
# - We provide runtime stubs when optional imports fail so type checkers
#   (Pylance) don't report "possibly unbound" for service types.
# - If imports fail, the endpoints will raise HTTP 500 via the require_* helpers.
try:
    from page_auditor import ComprehensivePageAuditor
    from humanization_validator import HumanizationValidator
    from llm_service import RobustLLMService
    from database_pool import DatabasePoolManager
    from edge_case_handler import EdgeCaseHandler
    from monitoring_config import MetricsCollector, AlertingSystem, HealthChecker
except ImportError as e:
    logging.warning(f"Custom module import warning: {e}")

    # Runtime typing stubs (only used to satisfy type checkers).
    ComprehensivePageAuditor = object  # type: ignore[assignment, misc]
    HumanizationValidator = object  # type: ignore[assignment, misc]
    RobustLLMService = object  # type: ignore[assignment, misc]
    DatabasePoolManager = object  # type: ignore[assignment, misc]
    EdgeCaseHandler = object  # type: ignore[assignment, misc]
    # Fallbacks only for type-checking. If monitoring_config import fails,
    # the app will fail at runtime anyway, but we avoid constructor-signature
    # errors in Pylance.
    # IMPORTANT: don't use `Any` here—Pylance treats `Any()` as invalid because
    # `Any` cannot be instantiated.
    MetricsCollector = object  # type: ignore[assignment]
    AlertingSystem = object  # type: ignore[assignment]
    HealthChecker = object  # type: ignore[assignment]

# ============================================================================
# CONFIGURATION
# ============================================================================

# Environment Configuration
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
DEBUG = ENVIRONMENT == "development"
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Database Configuration
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    DATABASE_URL = "sqlite:///./seo_platform.db"
    print("No DATABASE_URL configured, using local SQLite database for development.")

# LLM Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
LLM_DAILY_COST_LIMIT = float(os.getenv("LLM_DAILY_COST_LIMIT", "100.0"))
LLM_MAX_CALLS_PER_MINUTE = int(os.getenv("LLM_MAX_CALLS_PER_MINUTE", "60"))

# Redis Configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Monitoring Configuration
SENTRY_DSN = os.getenv("SENTRY_DSN", "")
DATADOG_API_KEY = os.getenv("DATADOG_API_KEY", "")
SLACK_WEBHOOK = os.getenv("SLACK_WEBHOOK", "")

# ============================================================================
# LOGGING SETUP
# ============================================================================

logging.basicConfig(
    level=LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# SENTRY INTEGRATION
# ============================================================================

def _filter_pii(event: Event, _hint: Hint) -> Event | None:
    """Filter PII from Sentry events (mutate and keep the event)."""
    # `Event` is a TypedDict-like structure; treat it as mutable for filtering.
    event_dict = cast(Dict[str, Any], event)

    request = event_dict.get("request")
    if isinstance(request, dict):
        headers = request.get("headers")
        if isinstance(headers, dict):
            headers.pop("Authorization", None)

    extra = event_dict.get("extra")
    if isinstance(extra, dict):
        extra.pop("user_email", None)
        extra.pop("api_key", None)

    return event

if SENTRY_DSN:
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[FastApiIntegration()],
        traces_sample_rate=0.1 if ENVIRONMENT == "production" else 1.0,
        environment=ENVIRONMENT,
        before_send=_filter_pii,
    )
    logger.info("Sentry initialized")

# ============================================================================
# DATABASE SETUP
# ============================================================================

engine_kwargs = {
    "echo": DEBUG,
}

if DATABASE_URL.startswith("sqlite:///"):
    engine_kwargs.update({
        "connect_args": {"check_same_thread": False},
    })
else:
    engine_kwargs.update({
        "pool_size": 20,
        "max_overflow": 40,
        "pool_recycle": 3600,
        "pool_pre_ping": True,
    })

engine = create_engine(DATABASE_URL, **engine_kwargs)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def is_url(value: str) -> bool:
    value = (value or "").strip()
    if not value:
        return False
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def normalize_url(value: str) -> str:
    value = (value or "").strip()
    if not value:
        return ""
    if is_url(value):
        return value
    if value.startswith("www."):
        return f"https://{value}"
    if " " not in value and "." in value:
        return f"https://{value}"
    return value


def fetch_html_from_input(content: str) -> str:
    content = (content or "").strip()
    if not content:
        raise HTTPException(status_code=400, detail="Provide a valid website URL to audit.")

    url = content
    if not is_url(url):
        url = normalize_url(content)
        if not is_url(url):
            raise HTTPException(status_code=400, detail="Must be a valid website URL (e.g., example.com or https://example.com).")

    html = crawl_page(url)
    if isinstance(html, str) and html.startswith("Error crawling"):
        raise HTTPException(status_code=400, detail=html)
    return html

# ============================================================================
# DATABASE MODELS
# ============================================================================

class ContentMetadata(Base):
    """Store generated content metadata"""
    __tablename__ = "content_metadata"
    
    id = sa.Column(sa.Integer, primary_key=True, index=True)
    user_id = sa.Column(sa.String(255), index=True)
    page_type = sa.Column(sa.String(50), index=True)
    primary_keyword = sa.Column(sa.String(255))
    secondary_keywords = sa.Column(sa.Text)
    title = sa.Column(sa.String(70))
    meta_description = sa.Column(sa.String(170))
    h1 = sa.Column(sa.String(255))
    h2_headers = sa.Column(sa.Text)  # JSON
    h3_headers = sa.Column(sa.Text)  # JSON
    content_paragraphs = sa.Column(sa.Text)  # JSON
    cta_lines = sa.Column(sa.Text)  # JSON
    humanization_score = sa.Column(sa.Float)
    audit_results = sa.Column(sa.Text)  # JSON
    created_at = sa.Column(sa.DateTime, default=datetime.utcnow, index=True)
    updated_at = sa.Column(sa.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class AuditLog(Base):
    """Track all API calls for monitoring"""
    __tablename__ = "audit_logs"
    
    id = sa.Column(sa.Integer, primary_key=True, index=True)
    user_id = sa.Column(sa.String(255), index=True)
    endpoint = sa.Column(sa.String(255))
    method = sa.Column(sa.String(10))
    status_code = sa.Column(sa.Integer)
    response_time_ms = sa.Column(sa.Float)
    error_message = sa.Column(sa.Text, nullable=True)
    created_at = sa.Column(sa.DateTime, default=datetime.utcnow, index=True)

class LLMUsageLog(Base):
    """Track LLM API calls for cost monitoring"""
    __tablename__ = "llm_usage_logs"
    
    id = sa.Column(sa.Integer, primary_key=True, index=True)
    user_id = sa.Column(sa.String(255), index=True)
    model = sa.Column(sa.String(50))
    input_tokens = sa.Column(sa.Integer)
    output_tokens = sa.Column(sa.Integer)
    cost = sa.Column(sa.Float)
    daily_total_cost = sa.Column(sa.Float)
    created_at = sa.Column(sa.DateTime, default=datetime.utcnow, index=True)

# Create tables (moved to lifespan event to allow env vars to be set)
# Base.metadata.create_all(bind=engine)
# logger.info("Database tables created")

# ============================================================================
# PYDANTIC MODELS (Request/Response)
# ============================================================================

class GenerateMetadataRequest(BaseModel):
    """Request model for metadata generation"""
    page_type: str = Field(..., description="Type: home, course, contact, about, category, blog, landing")
    primary_keyword: str = Field(..., min_length=3, max_length=100)
    secondary_keywords: Optional[str] = Field(None, description="Comma-separated keywords")
    course_name: Optional[str] = None
    brand_name: Optional[str] = None
    location: Optional[str] = None
    cta: Optional[str] = None
    features: Optional[str] = None
    audience: Optional[str] = None
    user_id: Optional[str] = "anonymous"
    
    @validator('page_type')
    def validate_page_type(cls, v):
        valid_types = ['home', 'course', 'contact', 'about', 'category', 'blog', 'landing']
        if v.lower() not in valid_types:
            raise ValueError(f"page_type must be one of {valid_types}")
        return v.lower()

class GenerateMetadataResponse(BaseModel):
    """Response model for metadata generation"""
    title: str
    meta_description: str
    h1: str
    h2_headers: List[str]
    h3_headers: List[str]
    content_paragraphs: List[str]
    cta_lines: List[str]
    humanization_score: float
    humanization_grade: str
    warnings: List[str] = []
    metadata_id: int

class AuditPageRequest(BaseModel):
    """Request model for page audit"""
    html_content: str = Field(..., description="Raw HTML content to audit")
    primary_keyword: Optional[str] = None
    user_id: Optional[str] = "anonymous"

class AuditPageResponse(BaseModel):
    """Response model for page audit"""
    h1_visibility_score: float
    h1_visible: bool
    semantic_validation: Dict[str, Any]
    image_alt_quality: Dict[str, Any]
    keyword_density: Dict[str, Any]
    schema_validation: Optional[Dict[str, Any]] = None
    overall_audit_grade: str
    recommendations: List[str]

class HealthCheckResponse(BaseModel):
    """Response model for health check"""
    status: str
    timestamp: str
    uptime_seconds: int
    checks: Dict[str, Any]

# New request/response models for tabbed interface
class GenerateMetadataTabRequest(BaseModel):
    """Request model for metadata tab generation"""
    pageType: str = Field(..., description="Page type: home, course, contact, about, category, blog, landing")
    courseName: str = Field(..., description="Course/Service name")
    primaryKeyword: str = Field(..., min_length=1, max_length=100)
    brand: Optional[str] = None
    highlights: Optional[str] = None

class GenerateMetadataTabResponse(BaseModel):
    """Response model for metadata tab generation"""
    title: str
    metaDescription: str

class GenerateHeadersRequest(BaseModel):
    """Request model for headers generation"""
    count: int = Field(..., ge=1, le=20, description="Number of headers to generate")
    pageType: str = Field(..., description="Page type")
    courseName: str = Field(..., description="Course/Service name")
    primaryKeyword: str = Field(..., min_length=1, max_length=100)
    brand: Optional[str] = None
    highlights: Optional[str] = None

class GenerateHeadersResponse(BaseModel):
    """Response model for headers generation"""
    h1: str
    h2: List[str]
    h3: List[str]

class GenerateFAQsRequest(BaseModel):
    """Request model for FAQs generation"""
    count: int = Field(..., ge=1, le=20, description="Number of FAQs to generate")
    pageType: str = Field(..., description="Page type")
    courseName: str = Field(..., description="Course/Service name")
    primaryKeyword: str = Field(..., min_length=1, max_length=100)
    brand: Optional[str] = None
    highlights: Optional[str] = None

class GenerateFAQsResponse(BaseModel):
    """Response model for FAQs generation"""
    faqs: List[Dict[str, str]]

class AuditContentRequest(BaseModel):
    """Request model for content audit"""
    content: str = Field(..., description="Website URL to audit")

    @validator('content')
    def validate_url(cls, v):
        v = (v or "").strip()
        if not v:
            raise ValueError("Provide a valid website URL to audit.")
        if not is_url(v) and not ("." in v and " " not in v):
            raise ValueError("Must be a valid website URL (e.g., example.com or https://example.com).")
        return v

class AuditContentResponse(BaseModel):
    """Response model for content audit"""
    score: int
    issues: List[str]
    recommendations: List[str]
    header_hierarchy: Dict[str, Any]
    image_analysis: Dict[str, Any]
    metadata_analysis: Dict[str, Any]
    keyword_analysis: Dict[str, Any]
    schema_blocks: List[Dict[str, Any]]

# ============================================================================
# LIFESPAN EVENTS
# ============================================================================

# Global service instances
# NOTE: Keep these as `Any` for Pylance correctness.
# The services are initialized via optional runtime imports in a try/except,
# which confuses the type checker into thinking the imported names aren't valid
# type expressions.
llm_service: Optional[Any] = None
page_auditor: Optional[Any] = None
humanization_validator: Optional[Any] = None
edge_case_handler: Optional[Any] = None
metrics_collector: Optional[Any] = None
alerting_system: Optional[Any] = None
health_checker: Optional[Any] = None
start_time: Optional[datetime] = None

def require_llm_service() -> Any:
    if llm_service is None:
        raise HTTPException(status_code=500, detail="LLM service unavailable")
    return llm_service


def require_page_auditor() -> Any:
    if page_auditor is None:
        raise HTTPException(status_code=500, detail="Page auditor unavailable")
    return page_auditor


def require_humanization_validator() -> Any:
    if humanization_validator is None:
        raise HTTPException(status_code=500, detail="Humanization validator unavailable")
    return humanization_validator


def require_edge_case_handler() -> Any:
    if edge_case_handler is None:
        raise HTTPException(status_code=500, detail="Edge case handler unavailable")
    return edge_case_handler


def require_metrics_collector() -> Any:
    if metrics_collector is None:
        raise HTTPException(status_code=500, detail="Metrics not configured")
    return metrics_collector


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    global llm_service, page_auditor, humanization_validator, edge_case_handler
    global metrics_collector, alerting_system, health_checker, start_time

    # Ensure globals are always assigned (helps type checkers like Pylance)
    llm_service = None
    page_auditor = None
    humanization_validator = None
    edge_case_handler = None
    metrics_collector = None
    alerting_system = None
    health_checker = None

    # STARTUP
    logger.info("🚀 Starting SEO Platform API")
    start_time = datetime.utcnow()

    # Create database tables (now that env vars are set)
    Base.metadata.create_all(bind=engine)
    logger.info("✅ Database tables created")

    try:
        # Initialize services
        llm_cls: Any = RobustLLMService
        llm_service = llm_cls(  # type: ignore[call-arg]
            openai_api_key=OPENAI_API_KEY,
            daily_cost_limit=LLM_DAILY_COST_LIMIT,
            max_calls_per_minute=LLM_MAX_CALLS_PER_MINUTE,
            redis_url=REDIS_URL,
        )
        logger.info("✅ LLM Service initialized")
        
        page_auditor = ComprehensivePageAuditor()
        logger.info("✅ Page Auditor initialized")
        
        humanization_validator = HumanizationValidator()
        logger.info("✅ Humanization Validator initialized")
        
        edge_case_handler = EdgeCaseHandler()
        logger.info("✅ Edge Case Handler initialized")
        
        # Datadog monitoring (MetricsCollector takes no constructor args)
        if DATADOG_API_KEY:
            metrics_collector = MetricsCollector()
            logger.info("✅ Metrics Collector initialized")
        
        # Alerting (AlertingSystem requires a MetricsCollector instance)
        if SLACK_WEBHOOK or DATADOG_API_KEY:
            if metrics_collector is not None:
                alerting_system = AlertingSystem(metrics_collector)  # type: ignore[call-arg]
                logger.info("✅ Alerting System initialized")
        
        health_checker = HealthChecker()  # type: ignore[call-arg]
        logger.info("✅ Health Checker initialized")
        
        logger.info("✅ API READY FOR REQUESTS")
        
    except Exception as e:
        logger.error(f"❌ Startup failed: {str(e)}", exc_info=True)
        if SENTRY_DSN:
            sentry_sdk.capture_exception(e)
        raise
    
    yield
    
    # SHUTDOWN
    logger.info("🛑 Shutting down SEO Platform API")
    # Cleanup code here if needed

# ============================================================================
# FASTAPI APP INITIALIZATION
# ============================================================================

app = FastAPI(
    title="SEO Platform API",
    description="Production-grade SEO content generator and auditor",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if DEBUG else None,
    redoc_url="/redoc" if DEBUG else None,
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:3000").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# ENDPOINTS: HEALTH & STATUS
# ============================================================================

@app.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """
    Health check endpoint
    
    Returns system status and component health
    """
    try:
        if health_checker:
            result = health_checker.get_health_status()
            return HealthCheckResponse(
                status="healthy" if result["status"] == "healthy" else "degraded",
                timestamp=result["timestamp"],
                uptime_seconds=int(result.get("uptime_seconds", 0)),
                checks=result["checks"]
            )
        else:
            uptime_seconds = int((datetime.utcnow() - start_time).total_seconds()) if start_time else 0
            return HealthCheckResponse(
                status="healthy",
                timestamp=datetime.utcnow().isoformat(),
                uptime_seconds=uptime_seconds,
                checks={}
            )
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}", exc_info=True)
        if SENTRY_DSN:
            sentry_sdk.capture_exception(e)
        raise HTTPException(status_code=503, detail="Service unavailable")

@app.get("/status")
async def status():
    """Get API status and component metrics"""
    try:
        llm = llm_service
        # Pylance: ensure it is not considered unbound/optional here
        if llm is None:
            llm_stats: Dict[str, Any] = {}
        else:
            llm_stats = llm.get_stats()

        st = start_time
        uptime_seconds = int((datetime.utcnow() - st).total_seconds()) if st else 0

        return {
            "status": "online",
            "environment": ENVIRONMENT,
            "uptime_seconds": uptime_seconds,
            "llm_service": {
                "daily_spend": llm_stats.get("daily_spend", 0),
                "daily_limit": LLM_DAILY_COST_LIMIT,
                "rate_limited": llm_stats.get("rate_limited", False),
                "queue_depth": llm_stats.get("queue_depth", 0),
            }
        }
    except Exception as e:
        logger.error(f"Status endpoint error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get status")


@app.post("/api/audit", response_model=AuditContentResponse)
async def audit_content(
    request: AuditContentRequest,
    db: Session = Depends(get_db)
):
    """Audit a website URL or raw HTML content for SEO issues."""
    start_time_req = datetime.utcnow()
    try:
        html_content = fetch_html_from_input(request.content)
        metrics = extract_metrics(html_content, request.content if is_url(request.content) else "")
        score = calculate_score(metrics)

        issues: List[str] = []
        if not metrics.get("title"):
            issues.append("Missing title tag")
        if not metrics.get("meta_description"):
            issues.append("Missing meta description")
        if metrics.get("h1_count", 0) == 0:
            issues.append("No H1 tag found")
        elif metrics.get("h1_count", 0) > 1:
            issues.append("Multiple H1 tags found")
        if metrics.get("images_without_alt", 0) > 0:
            issues.append(f"{metrics['images_without_alt']} image(s) missing alt text")
        if metrics.get("missing_title", 0) > 0:
            issues.append(f"{metrics['missing_title']} image(s) missing title attributes")
        if not metrics.get("has_viewport"):
            issues.append("Missing viewport meta tag")
        if metrics.get("external_links", 0) > metrics.get("internal_links", 0):
            issues.append("External links outnumber internal links")

        recommendations = generate_suggestions(metrics)

        audit_log = AuditLog(
            user_id="anonymous",
            endpoint="/api/audit",
            method="POST",
            status_code=200,
            response_time_ms=(datetime.utcnow() - start_time_req).total_seconds() * 1000,
        )
        db.add(audit_log)
        db.commit()

        return AuditContentResponse(
            score=score,
            issues=issues,
            recommendations=recommendations,
            header_hierarchy=metrics.get('header_hierarchy', {}),
            image_analysis={
                'total_images': metrics.get('total_images', 0),
                'missing_alt': metrics.get('missing_alt', 0),
                'missing_title': metrics.get('missing_title', 0),
                'details': metrics.get('details', []),
            },
            metadata_analysis=metrics.get('metadata_analysis', {}),
            keyword_analysis=metrics.get('keyword_analysis', {}),
            schema_blocks=metrics.get('schema_blocks', []),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Audit route failed: {str(e)}", exc_info=True)
        if SENTRY_DSN:
            sentry_sdk.capture_exception(e)
        raise HTTPException(status_code=500, detail="Website audit failed")

# ============================================================================
# ENDPOINTS: CONTENT GENERATION
# ============================================================================

@app.post("/api/v1/generate-metadata", response_model=GenerateMetadataResponse)
async def generate_metadata(
    request: GenerateMetadataRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Generate SEO metadata for a page
    
    Takes: page_type, primary_keyword, optional secondary keywords
    Returns: title, meta_description, h1, headers, paragraphs, CTAs
    """
    start_time_req = datetime.utcnow()
    
    try:
        # Validate input
        handler = require_edge_case_handler()
        handler.sanitize_text_input(request.primary_keyword)

        # Generate using LLM
        llm = require_llm_service()
        metadata = llm.generate_metadata(
            page_type=request.page_type,
            primary_keyword=request.primary_keyword,
            secondary_keywords=request.secondary_keywords or "",
            course_name=request.course_name or "",
            brand_name=request.brand_name or "",
            cta=request.cta or "Call Now",
            location=request.location or "",
        )

        # Validate humanization
        validator_obj = require_humanization_validator()
        humanization_result = validator_obj.validate_metadata(
            title=metadata.get("title", ""),
            description=metadata.get("meta_description", ""),
            keyword=request.primary_keyword,
        )
        
        # Store in database
        db_record = ContentMetadata(
            user_id=request.user_id,
            page_type=request.page_type,
            primary_keyword=request.primary_keyword,
            secondary_keywords=request.secondary_keywords or "",
            title=metadata.get("title", ""),
            meta_description=metadata.get("meta_description", ""),
            h1=metadata.get("h1", ""),
            h2_headers=json.dumps(metadata.get("h2_headers", [])),
            h3_headers=json.dumps(metadata.get("h3_headers", [])),
            content_paragraphs=json.dumps(metadata.get("content_paragraphs", [])),
            cta_lines=json.dumps(metadata.get("cta_lines", [])),
            humanization_score=humanization_result.get("score", 0),
        )
        db.add(db_record)
        db.commit()
        db.refresh(db_record)
        
        # Log metrics
        if metrics_collector:
            collector = metrics_collector
            collector.record_generation(
                page_type=request.page_type,
                humanization_score=humanization_result.get("score", 0),
            )
        
        # Log to audit table
        audit_log = AuditLog(
            user_id=request.user_id,
            endpoint="/api/v1/generate-metadata",
            method="POST",
            status_code=200,
            response_time_ms=(datetime.utcnow() - start_time_req).total_seconds() * 1000,
        )
        db.add(audit_log)
        db.commit()
        
        return GenerateMetadataResponse(
            title=metadata.get("title", ""),
            meta_description=metadata.get("meta_description", ""),
            h1=metadata.get("h1", ""),
            h2_headers=metadata.get("h2_headers", []),
            h3_headers=metadata.get("h3_headers", []),
            content_paragraphs=metadata.get("content_paragraphs", []),
            cta_lines=metadata.get("cta_lines", []),
            humanization_score=humanization_result.get("score", 0),
            humanization_grade=humanization_result.get("grade", "B"),
            warnings=humanization_result.get("issues", []),
            metadata_id=cast(int, db_record.id),  # type: ignore[arg-type]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Metadata generation failed: {str(e)}", exc_info=True)
        if SENTRY_DSN:
            sentry_sdk.capture_exception(e)
        raise HTTPException(status_code=500, detail="Metadata generation failed")

# ============================================================================
# ENDPOINTS: PAGE AUDITING
# ============================================================================

@app.post("/api/v1/audit-page", response_model=AuditPageResponse)
async def audit_page(
    request: AuditPageRequest,
    db: Session = Depends(get_db)
):
    """
    Audit a web page for SEO issues
    
    Takes: HTML content, optional primary keyword
    Returns: H1 visibility, semantic validation, image alt quality, keyword density
    """
    start_time_req = datetime.utcnow()
    
    try:
        auditor = require_page_auditor()
        handler = require_edge_case_handler()

        # Sanitize HTML input
        html_content = handler.sanitize_html_input(request.html_content, max_length=100000)

        # Run comprehensive audit
        h1_visibility = auditor.check_h1_visibility(html_content)
        
        # Get H1 tag for semantic validation
        h1_tags = [tag for tag in html_content.lower().split("<h1") if "</h1>" in tag]
        h1_text = h1_tags[0].split(">")[1].split("<")[0] if h1_tags else ""
        
        semantic_validation = auditor.validate_h1_semantic(
            h1_text=h1_text,
            page_title=h1_text,
            primary_keyword=request.primary_keyword or "",
        ) if h1_text else {"valid": False, "score": 0}
        
        # Keyword density analysis
        keyword_density = auditor.analyze_keyword_density(
            html_content=html_content,
            primary_keyword=request.primary_keyword or "",
        ) if request.primary_keyword else {}
        
        # Image alt text analysis
        image_alt_results = auditor.check_image_alt_quality(html_content)
        
        # Calculate overall grade
        scores = [
            h1_visibility.get("score", 0),
            semantic_validation.get("score", 0) if semantic_validation else 0,
            image_alt_results.get("average_score", 0) if image_alt_results else 0,
        ]
        average_score = sum(scores) / len([s for s in scores if s > 0]) if scores else 0
        
        grade_map = {90: "A+", 80: "A", 70: "B", 60: "C", 0: "F"}
        overall_grade = next(g for s, g in sorted(grade_map.items(), reverse=True) if average_score >= s)
        
        # Log audit
        audit_log = AuditLog(
            user_id=request.user_id,
            endpoint="/api/v1/audit-page",
            method="POST",
            status_code=200,
            response_time_ms=(datetime.utcnow() - start_time_req).total_seconds() * 1000,
        )
        db.add(audit_log)
        db.commit()
        
        return AuditPageResponse(
            h1_visibility_score=h1_visibility.get("score", 0),
            h1_visible=h1_visibility.get("visible", False),
            semantic_validation=semantic_validation or {},
            image_alt_quality=image_alt_results or {},
            keyword_density=keyword_density or {},
            overall_audit_grade=overall_grade,
            recommendations=[
                "Add more descriptive image alt text" if image_alt_results and image_alt_results.get("average_score", 0) < 70 else "",
                "Optimize keyword density" if keyword_density and keyword_density.get("primary_status") != "OPTIMAL" else "",
                "Ensure H1 is visible and semantic" if not h1_visibility.get("visible") else "",
            ]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Page audit failed: {str(e)}", exc_info=True)
        if SENTRY_DSN:
            sentry_sdk.capture_exception(e)
        raise HTTPException(status_code=500, detail="Page audit failed")

# ============================================================================
# ENDPOINTS: DATA EXPORT
# ============================================================================

@app.get("/api/v1/export/csv")
async def export_csv(
    user_id: str = Query(..., description="User ID to export"),
    start_date: Optional[str] = Query(None, description="ISO format date"),
    db: Session = Depends(get_db)
):
    """
    Export user's metadata history as CSV
    
    Returns downloadable CSV file with all generated content
    """
    try:
        query = db.query(ContentMetadata).filter(ContentMetadata.user_id == user_id)
        
        if start_date:
            start_dt = datetime.fromisoformat(start_date)
            query = query.filter(ContentMetadata.created_at >= start_dt)
        
        records = query.order_by(ContentMetadata.created_at.desc()).limit(1000).all()
        
        if not records:
            raise HTTPException(status_code=404, detail="No records found")
        
        # Build CSV
        output = StringIO()
        writer = csv.writer(output)
        
        # Header
        writer.writerow([
            "ID", "Page Type", "Primary Keyword", "Title", "Meta Description",
            "H1", "Humanization Score", "Created At"
        ])
        
        # Data
        for record in records:
            writer.writerow([
                record.id,
                record.page_type,
                record.primary_keyword,
                record.title,
                record.meta_description,
                record.h1,
                record.humanization_score,
                record.created_at.isoformat(),
            ])
        
        csv_bytes = output.getvalue().encode("utf-8")
        filename = f"seo-metadata-export-{datetime.utcnow().strftime('%Y%m%d')}.csv"
        headers = {
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
        return StreamingResponse(
            content=iter([csv_bytes]),
            media_type="text/csv",
            headers=headers,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"CSV export failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Export failed")

# ============================================================================
# ENDPOINTS: MONITORING & METRICS
# ============================================================================

@app.get("/api/v1/metrics")
async def get_metrics(
    time_range: str = Query("24h", description="24h or 7d")
):
    """Get platform metrics and usage statistics"""
    try:
        collector = metrics_collector
        if collector is None:
            return {"error": "Metrics not configured"}

        return collector.get_metrics(time_range=time_range)
        
    except Exception as e:
        logger.error(f"Metrics retrieval failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve metrics")

@app.get("/api/v1/llm-stats")
async def get_llm_stats():
    """Get LLM service statistics and cost tracking"""
    try:
        llm = require_llm_service()
        stats = llm.get_stats()
        usage_log = llm.get_usage_log()
        
        return {
            "stats": stats,
            "recent_usage": usage_log,
        }
        
    except Exception as e:
        logger.error(f"LLM stats retrieval failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve LLM stats")

# ============================================================================
# ENDPOINTS: ADMIN
# ============================================================================

@app.post("/api/v1/admin/reset-daily-spend")
async def reset_daily_spend():
    """
    Admin endpoint to reset daily LLM spend counter
    
    Call at midnight UTC daily or on-demand for testing
    """
    try:
        llm = require_llm_service()
        llm.reset_daily_spend()
        logger.info("Daily LLM spend counter reset")
        
        return {"status": "success", "message": "Daily spend reset"}
        
    except Exception as e:
        logger.error(f"Reset failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Reset failed")

# ============================================================================
# NEW TABBED INTERFACE ENDPOINTS
# ============================================================================

@app.post("/api/generate/metadata")
async def generate_metadata_tab(request: GenerateMetadataTabRequest):
    """Generate page title and meta description for metadata tab"""
    try:
        llm = require_llm_service()

        # Generate metadata using LLM service
        metadata = await llm.generate_metadata(
            page_type=request.pageType,
            primary_keyword=request.primaryKeyword,
            course_name=request.courseName,
            brand_name=request.brand or "",
            secondary_keywords=request.highlights or "",
            cta="Call Now",
        )

        return GenerateMetadataTabResponse(
            title=metadata.get("title", ""),
            metaDescription=metadata.get("meta_description", "")
        )

    except Exception as e:
        logger.error(f"Metadata generation failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to generate metadata")

@app.post("/api/generate/headers")
async def generate_headers(request: GenerateHeadersRequest):
    """Generate H1, H2, and H3 headers"""
    try:
        llm = require_llm_service()

        # Generate headers using LLM service
        metadata = await llm.generate_metadata(
            page_type=request.pageType,
            primary_keyword=request.primaryKeyword,
            course_name=request.courseName,
            brand_name=request.brand or "",
            secondary_keywords=request.highlights or "",
            cta="Call Now",
        )

        return GenerateHeadersResponse(
            h1=metadata.get("h1", ""),
            h2=metadata.get("h2_headers", []),
            h3=metadata.get("h3_headers", [])
        )

    except Exception as e:
        logger.error(f"Headers generation failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to generate headers")

@app.post("/api/generate/faqs")
async def generate_faqs(request: GenerateFAQsRequest):
    """Generate frequently asked questions"""
    try:
        llm = require_llm_service()

        # Generate FAQs using LLM service
        faqs = await llm.generate_faqs(
            page_type=request.pageType,
            primary_keyword=request.primaryKeyword,
            course_name=request.courseName,
            brand_name=request.brand or "",
            highlights=request.highlights or "",
            count=request.count,
        )

        return GenerateFAQsResponse(faqs=faqs)

    except Exception as e:
        logger.error(f"FAQs generation failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to generate FAQs")

# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions"""
    if exc.status_code >= 500:
        logger.error(f"HTTP error {exc.status_code}: {exc.detail}")
        if SENTRY_DSN:
            sentry_sdk.capture_message(f"HTTP {exc.status_code}: {exc.detail}")
    
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail},
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle unexpected exceptions"""
    logger.error(f"Unexpected error: {str(exc)}", exc_info=True)
    
    if SENTRY_DSN:
        sentry_sdk.capture_exception(exc)
    
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error"},
    )

# ============================================================================
# ROOT ENDPOINT
# ============================================================================

@app.get("/")
async def root():
    """API root endpoint with documentation"""
    return {
        "name": "SEO Platform API",
        "version": "1.0.0",
        "environment": ENVIRONMENT,
        "endpoints": {
            "health": "/health",
            "status": "/status",
            "docs": "/docs" if DEBUG else "Not available",
            "generate_metadata": "POST /api/v1/generate-metadata",
            "audit_page": "POST /api/v1/audit-page",
            "export": "GET /api/v1/export/csv",
            "metrics": "GET /api/v1/metrics",
        }
    }

# ============================================================================
# RUN
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        app,
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "8000")),
        workers=int(os.getenv("WORKERS", "4")),
        log_level=LOG_LEVEL.lower(),
    )
    print("=" * 50)
    # app.run is not valid for FastAPI; use uvicorn above.
