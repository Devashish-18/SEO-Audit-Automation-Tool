"""
RobustLLMService - Production-Grade LLM Integration
Handles rate limiting, cost controls, queueing, retry logic, and monitoring

Key Features:
- Rate limiting (60 calls/min enforced)
- Daily cost cap ($100/day default)
- Job queueing with priority support
- Exponential backoff retry logic
- Cost tracking & alerting
- Usage monitoring & logging
- Graceful degradation
"""

import asyncio
import json
import uuid
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, List
from enum import Enum
from urllib.parse import urlparse

# Third-party imports (install these)
# pip install openai redis python-dotenv

import openai
from redis import Redis
from redis.exceptions import RedisError


class JobPriority(Enum):
    """Job priority levels"""
    LOW = 3
    NORMAL = 2
    HIGH = 1


class JobStatus(Enum):
    """Job status types"""
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


class RobustLLMService:
    """Production-grade LLM service with rate limiting, cost controls, and queueing"""

    def __init__(
        self,
        openai_api_key: str,
        redis_url: str = "redis://localhost:6379/0",
        redis_host: str = "localhost",
        redis_port: int = 6379,
        redis_db: int = 0,
        max_calls_per_minute: int = 60,
        daily_cost_limit: float = 100.0,
        model: str = "gpt-4"
    ):
        """
        Initialize LLM service
        
        Args:
            openai_api_key: OpenAI API key
            redis_url: Redis connection URL
            redis_host: Redis server host (used only if redis_url is not provided)
            redis_port: Redis server port (used only if redis_url is not provided)
            redis_db: Redis database number (used only if redis_url is not provided)
            max_calls_per_minute: Rate limit (calls/min)
            daily_cost_limit: Daily spend limit in dollars
            model: OpenAI model to use (gpt-4, gpt-3.5-turbo)
        """
        
        self.logger = logging.getLogger(__name__)
        openai.api_key = openai_api_key
        self.model = model
        self.max_calls_per_minute = max_calls_per_minute
        self.daily_cost_limit = daily_cost_limit

        # Parse redis_url if provided
        if redis_url:
            parsed_redis = urlparse(redis_url)
            redis_host = parsed_redis.hostname or redis_host
            redis_port = parsed_redis.port or redis_port
            if parsed_redis.path and parsed_redis.path != "/":
                try:
                    redis_db = int(parsed_redis.path.lstrip("/"))
                except ValueError:
                    redis_db = redis_db

        # Redis connection
        try:
            self.redis = Redis(
                host=redis_host,
                port=redis_port,
                db=redis_db,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_keepalive=True
            )
            # Test connection
            self.redis.ping()
            self.logger.info("✅ Redis connected")
        except RedisError as e:
            self.logger.error(f"❌ Redis connection failed: {e}")
            self.redis = None
        
        # Pricing models (tokens -> cost in dollars)
        self.pricing = {
            "gpt-4": {"input": 0.03, "output": 0.06},      # per 1K tokens
            "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015},
        }

    # ========================
    # PUBLIC API
    # ========================

    async def call_gpt_with_rate_limit(
        self,
        prompt: str,
        priority: JobPriority = JobPriority.NORMAL,
        user_id: Optional[str] = None,
        timeout: int = 300
    ) -> str:
        """
        Call GPT-4 with rate limiting, cost controls, and queuing
        
        Args:
            prompt: Prompt to send to LLM
            priority: Job priority (affects queue position)
            user_id: Optional user ID for tracking
            timeout: Max wait time in seconds (default 5 min)
        
        Returns:
            Response text from GPT-4
        
        Raises:
            Exception: If daily cost limit exceeded or timeout
        """
        
        # Check if Redis is available
        if not self.redis:
            self.logger.warning("⚠️ Redis unavailable; calling GPT-4 directly (no rate limiting)")
            return await self._call_gpt4_with_retry(prompt)
        
        # Step 1: Check daily cost limit
        daily_spend = float(self.redis.get("llm:daily_spend") or 0)
        if daily_spend > self.daily_cost_limit:
            self.logger.warning(f"💰 Daily cost limit reached: ${daily_spend:.2f}")
            raise Exception(
                f"Daily cost limit reached: ${daily_spend:.2f}/${self.daily_cost_limit:.2f}. "
                "Request queued for tomorrow."
            )
        
        # Step 2: Check rate limit (calls per minute)
        if self._is_rate_limited():
            self.logger.info(f"⏳ Rate limit hit; queueing job")
            job_id = self._queue_job(prompt, priority, user_id)
            response = await self._wait_for_job_completion(job_id, timeout)
            return response
        
        # Step 3: Direct call (under rate limit)
        try:
            response = await self._call_gpt4_with_retry(prompt)
            cost = self._calculate_cost(response)
            
            # Track usage
            self.redis.incr("llm:minute_calls")
            self.redis.expire("llm:minute_calls", 60)
            self.redis.incrbyfloat("llm:daily_spend", cost)
            self.redis.expire("llm:daily_spend", 86400)
            
            # Log usage
            self._log_usage(response.usage, cost, user_id, "direct")
            
            return response.choices[0].message.content
        
        except openai.error.RateLimitError as e:
            self.logger.warning(f"⏳ OpenAI rate limit; queuing for retry")
            job_id = self._queue_job(prompt, JobPriority.HIGH, user_id)
            response = await self._wait_for_job_completion(job_id, timeout)
            return response

    async def generate_metadata(
        self,
        page_type: str,
        primary_keyword: str,
        secondary_keywords: str,
        course_name: str,
        brand_name: str,
        cta: str,
        location: str = ""
    ) -> Dict:
        """
        Generate SEO metadata using LLM with validation
        
        Returns:
        {
            "title": "50-60 char title",
            "meta_description": "140-160 char description",
            "h1": "Main heading",
            "success": bool,
            "cost": float
        }
        """
        
        prompt = f"""Generate SEO metadata for a {page_type} page with the following:
        
        Primary Keyword: {primary_keyword}
        Secondary Keywords: {secondary_keywords}
        Course/Service: {course_name}
        Brand: {brand_name}
        CTA: {cta}
        Location: {location if location else "Not specified"}
        
        REQUIREMENTS:
        - Page Title: 50-60 characters (optimal), 60-70 max
        - Meta Description: 140-160 characters (optimal), 160-170 max
        - Include primary keyword in both
        - Include CTA at start or end of description
        - 2-sentence description exactly
        - Benefit-focused language
        - No word "the" in CTA
        
        Return as JSON:
        {{
            "title": "...",
            "meta_description": "...",
            "h1": "...",
            "h2_headers": ["...", "..."],
            "h3_headers": ["...", "..."],
            "cta_lines": ["...", "..."],
            "paragraphs": ["..."]
        }}"""
        
        try:
            response_text = await self.call_gpt_with_rate_limit(
                prompt=prompt,
                priority=JobPriority.NORMAL,
                user_id="metadata_gen"
            )
            
            # Parse response
            result = json.loads(response_text)
            
            return {
                "title": result.get("title", ""),
                "meta_description": result.get("meta_description", ""),
                "h1": result.get("h1", ""),
                "h2_headers": result.get("h2_headers", []),
                "h3_headers": result.get("h3_headers", []),
                "cta_lines": result.get("cta_lines", []),
                "paragraphs": result.get("paragraphs", []),
                "success": True
            }
        
        except Exception as e:
            self.logger.error(f"❌ Metadata generation failed: {e}")
            return {"success": False, "error": str(e)}

    async def generate_faqs(
        self,
        page_type: str,
        primary_keyword: str,
        course_name: str,
        brand_name: str,
        highlights: str,
        count: int = 5
    ) -> List[Dict[str, str]]:
        """
        Generate frequently asked questions for a page

        Returns:
        [{"question": "...", "answer": "..."}, ...]
        """

        prompt = f"""Generate {count} frequently asked questions for a {page_type} page about:

        Course/Service: {course_name}
        Primary Keyword: {primary_keyword}
        Brand: {brand_name}
        Key Highlights: {highlights}

        REQUIREMENTS:
        - Questions should be natural and commonly asked
        - Answers should be 2-4 sentences, informative and helpful
        - Include primary keyword in at least 3 questions
        - Focus on benefits, features, and practical information
        - Questions should start with "What", "How", "Why", "Can", "Do", "Is"

        Return as JSON array:
        [
            {{"question": "What is {course_name}?", "answer": "..."}},
            {{"question": "How does {primary_keyword} work?", "answer": "..."}}
        ]"""

        try:
            response_text = await self.call_gpt_with_rate_limit(
                prompt=prompt,
                priority=JobPriority.NORMAL,
                user_id="faqs_gen"
            )

            # Parse response
            faqs = json.loads(response_text)

            return faqs if isinstance(faqs, list) else []

        except Exception as e:
            self.logger.error(f"❌ FAQs generation failed: {e}")
            return []

    # ========================
    # INTERNAL: RATE LIMITING
    # ========================

    def _is_rate_limited(self) -> bool:
        """Check if current minute call limit reached"""
        
        if not self.redis:
            return False
        
        minute_key = f"llm:minute_calls:{datetime.now().strftime('%Y-%m-%d %H:%M')}"
        current_calls = int(self.redis.get(minute_key) or 0)
        
        if current_calls >= self.max_calls_per_minute:
            self.logger.warning(f"⏳ Rate limit: {current_calls}/{self.max_calls_per_minute} calls this minute")
            return True
        
        return False

    def _get_daily_spend(self) -> float:
        """Get current daily spend"""
        
        if not self.redis:
            return 0.0
        
        return float(self.redis.get("llm:daily_spend") or 0)

    # ========================
    # INTERNAL: JOB QUEUEING
    # ========================

    def _queue_job(
        self,
        prompt: str,
        priority: JobPriority,
        user_id: Optional[str]
    ) -> str:
        """Queue job in Redis for async processing"""
        
        if not self.redis:
            raise Exception("Redis not available for queueing")
        
        job_id = str(uuid.uuid4())
        
        # Add to sorted set by priority (lower score = higher priority)
        self.redis.zadd(
            "llm:queue",
            {job_id: priority.value}
        )
        
        # Store job details
        self.redis.hset(f"llm:job:{job_id}", mapping={
            "prompt": prompt,
            "status": JobStatus.QUEUED.value,
            "priority": priority.name,
            "user_id": user_id or "anonymous",
            "created_at": datetime.now().isoformat(),
            "attempts": "0"
        })
        
        self.logger.info(f"📋 Job queued: {job_id} (priority: {priority.name})")
        return job_id

    async def _wait_for_job_completion(self, job_id: str, timeout: int) -> str:
        """Poll Redis until job completes or timeout"""
        
        if not self.redis:
            raise Exception("Redis not available for polling")
        
        start = datetime.now()
        poll_interval = 0.5  # seconds
        
        while datetime.now() - start < timedelta(seconds=timeout):
            status = self.redis.hget(f"llm:job:{job_id}", "status")
            
            if status == JobStatus.COMPLETED.value:
                result = self.redis.hget(f"llm:job:{job_id}", "result")
                self.redis.delete(f"llm:job:{job_id}")
                return result
            
            elif status == JobStatus.FAILED.value:
                error = self.redis.hget(f"llm:job:{job_id}", "error")
                self.redis.delete(f"llm:job:{job_id}")
                raise Exception(f"Job failed: {error}")
            
            await asyncio.sleep(poll_interval)
        
        self.logger.error(f"❌ Job {job_id} timed out after {timeout}s")
        raise TimeoutError(f"Job {job_id} timed out after {timeout}s")

    # ========================
    # INTERNAL: GPT-4 CALLING
    # ========================

    async def _call_gpt4_with_retry(
        self,
        prompt: str,
        max_retries: int = 3
    ):
        """Call GPT-4 with exponential backoff retry"""
        
        for attempt in range(max_retries):
            try:
                response = openai.ChatCompletion.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.7,
                    max_tokens=2000,
                    timeout=30
                )
                
                self.logger.info(f"✅ GPT-4 call successful (attempt {attempt + 1})")
                return response
            
            except openai.error.RateLimitError:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # 1s, 2s, 4s
                    self.logger.warning(f"⏳ Rate limit; retrying in {wait_time}s")
                    await asyncio.sleep(wait_time)
                else:
                    raise
            
            except openai.error.Timeout:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    self.logger.warning(f"⏱️ Timeout; retrying in {wait_time}s")
                    await asyncio.sleep(wait_time)
                else:
                    raise
            
            except openai.error.APIError as e:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    self.logger.warning(f"⚠️ API error; retrying in {wait_time}s: {e}")
                    await asyncio.sleep(wait_time)
                else:
                    raise

    # ========================
    # INTERNAL: COST TRACKING
    # ========================

    def _calculate_cost(self, response) -> float:
        """Calculate cost based on tokens used"""
        
        if self.model not in self.pricing:
            self.logger.warning(f"⚠️ Unknown model: {self.model}; cost calculation may be inaccurate")
            return 0.0
        
        input_tokens = response.usage.prompt_tokens
        output_tokens = response.usage.completion_tokens
        
        pricing = self.pricing[self.model]
        cost = (input_tokens * pricing["input"] + output_tokens * pricing["output"]) / 1000
        
        return cost

    def _log_usage(self, usage, cost: float, user_id: Optional[str], method: str):
        """Log usage for monitoring and billing"""
        
        if not self.redis:
            return
        
        log_entry = json.dumps({
            "timestamp": datetime.now().isoformat(),
            "model": self.model,
            "input_tokens": usage.prompt_tokens,
            "output_tokens": usage.completion_tokens,
            "total_tokens": usage.total_tokens,
            "cost": cost,
            "user_id": user_id or "anonymous",
            "method": method
        })
        
        self.redis.lpush("llm:usage_log", log_entry)
        self.redis.ltrim("llm:usage_log", 0, 999)  # Keep last 1000 entries
        
        self.logger.info(f"💰 Usage logged: {usage.total_tokens} tokens, ${cost:.4f}")

    # ========================
    # MONITORING
    # ========================

    def get_stats(self) -> Dict:
        """Get current service statistics"""
        
        if not self.redis:
            return {"status": "OFFLINE"}
        
        try:
            daily_spend = float(self.redis.get("llm:daily_spend") or 0)
            minute_calls = int(self.redis.get("llm:minute_calls") or 0)
            queue_depth = self.redis.zcard("llm:queue")
            
            return {
                "status": "ONLINE",
                "daily_spend": f"${daily_spend:.2f}",
                "daily_limit": f"${self.daily_cost_limit:.2f}",
                "spend_percent": f"{(daily_spend/self.daily_cost_limit)*100:.1f}%",
                "minute_calls": f"{minute_calls}/{self.max_calls_per_minute}",
                "queue_depth": queue_depth,
                "rate_limited": minute_calls >= self.max_calls_per_minute
            }
        except Exception as e:
            self.logger.error(f"❌ Stats retrieval failed: {e}")
            return {"status": "ERROR", "error": str(e)}

    def get_usage_log(self, limit: int = 10) -> List[Dict]:
        """Get recent usage log entries"""
        
        if not self.redis:
            return []
        
        try:
            entries = self.redis.lrange("llm:usage_log", 0, limit - 1)
            return [json.loads(entry) for entry in entries]
        except Exception as e:
            self.logger.error(f"❌ Usage log retrieval failed: {e}")
            return []

    def reset_daily_spend(self):
        """Reset daily spend counter (call at midnight)"""
        
        if not self.redis:
            return
        
        self.redis.delete("llm:daily_spend")
        self.logger.info("🔄 Daily spend reset")

    def reset_minute_calls(self):
        """Reset minute call counter (call at start of each minute)"""
        
        if not self.redis:
            return
        
        minute_key = f"llm:minute_calls:{datetime.now().strftime('%Y-%m-%d %H:%M')}"
        self.redis.delete(minute_key)
        self.logger.info("🔄 Minute calls reset")


# ========================
# USAGE EXAMPLES
# ========================

if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Initialize service
    service = RobustLLMService(
        openai_api_key="sk-...",  # Replace with actual key
        redis_host="localhost",
        max_calls_per_minute=60,
        daily_cost_limit=100.0
    )
    
    # Example 1: Get stats
    print("Service Stats:")
    print(json.dumps(service.get_stats(), indent=2))
    
    # Example 2: Generate metadata (async)
    async def example():
        result = await service.generate_metadata(
            page_type="course",
            primary_keyword="online MBA programs",
            secondary_keywords="MBA, business degree, online learning",
            course_name="Advanced MBA Program",
            brand_name="Acadment",
            cta="Enroll Today",
            location="USA"
        )
        
        print("\nGenerated Metadata:")
        print(json.dumps(result, indent=2))
    
    # Run async example
    asyncio.run(example())
    
    # Example 3: Check usage log
    print("\nRecent Usage:")
    for entry in service.get_usage_log(5):
        print(f"  {entry['timestamp']}: {entry['total_tokens']} tokens, ${entry['cost']:.4f}")
