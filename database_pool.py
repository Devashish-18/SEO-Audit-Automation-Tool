"""
Database Connection Pool Optimization & Management
Production-grade configuration with monitoring for PostgreSQL/MySQL

Key Features:
- Optimized connection pooling (QueuePool)
- Connection health checks (pool_pre_ping)
- Automatic connection recycling
- Monitoring & alerting thresholds
- Query timeout protection
- Connection leak detection
"""

from sqlalchemy import create_engine, event, pool
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.exc import ArgumentError, SQLAlchemyError
from sqlalchemy.pool import QueuePool, NullPool, StaticPool
import logging
from typing import Dict, Optional
from datetime import datetime
import psycopg2

logger = logging.getLogger(__name__)


class DatabasePoolManager:
    """Manages database connection pool with monitoring"""
    
    # Thresholds for alerting
    ALERT_THRESHOLD_ACTIVE_PERCENT = 0.80  # Alert at 80% utilization
    ALERT_THRESHOLD_QUEUE_WAIT = 5.0  # Alert if waiting >5s for connection
    
    def __init__(
        self,
        database_url: str,
        pool_size: int = 20,
        max_overflow: int = 40,
        pool_recycle: int = 3600,
        echo: bool = False,
        environment: str = "development"
    ):
        """
        Initialize database engine with optimized pool
        
        Args:
            database_url: SQLAlchemy connection string
            pool_size: Size of connection pool (keep ~10 connections per worker)
            max_overflow: Additional connections allowed beyond pool_size
            pool_recycle: Seconds before recycling connections (default 1 hour)
            echo: Enable SQL logging
            environment: 'development', 'staging', 'production'
        """
        
        self.database_url = database_url
        self.pool_size = pool_size
        self.max_overflow = max_overflow
        self.pool_recycle = pool_recycle
        self.environment = environment
        self.stats = {
            "connections_created": 0,
            "connections_recycled": 0,
            "connections_invalidated": 0,
            "max_active_connections": 0
        }
        
        logger.info(f"🔧 Initializing database pool: size={pool_size}, overflow={max_overflow}")
        
        # Create engine with optimized pool
        self.engine = self._create_engine(echo)
        
        # Setup event listeners for monitoring
        self._setup_listeners()
        
        logger.info(f"✅ Database pool initialized")

    def _create_engine(self, echo: bool):
        """Create engine with production-grade pool configuration"""
        
        # Select pool class based on environment
        if self.environment == "testing":
            poolclass = StaticPool  # Use in-memory DB for tests
        else:
            poolclass = QueuePool  # Standard for production
        
        engine = create_engine(
            self.database_url,
            
            # Connection pooling configuration
            poolclass=poolclass,
            pool_size=self.pool_size,
            max_overflow=self.max_overflow,
            pool_recycle=self.pool_recycle,
            pool_pre_ping=True,  # Test connection before reusing
            
            # Performance tuning
            echo=echo,
            future=True,
            connect_args={
                "connect_timeout": 10,
                "application_name": "seo_platform",
                "options": "-c statement_timeout=30000"  # 30-second query timeout
            },
            
            # Connection lifecycle
            pool_size_threshold=self.pool_size * 0.8,  # Alert at 80% capacity
        )
        
        return engine

    def _setup_listeners(self):
        """Setup SQLAlchemy event listeners for monitoring"""
        
        @event.listens_for(self.engine, "connect")
        def receive_connect(dbapi_conn, connection_record):
            """Log new connection"""
            self.stats["connections_created"] += 1
            logger.debug(f"🔌 New connection created (total: {self.stats['connections_created']})")
        
        @event.listens_for(self.engine, "checkin")
        def receive_checkin(dbapi_conn, connection_record):
            """Log connection returned to pool"""
            logger.debug(f"♻️ Connection returned to pool")
        
        @event.listens_for(self.engine, "checkout")
        def receive_checkout(dbapi_conn, connection_record, connection_proxy):
            """Log connection checked out from pool"""
            active = self._get_active_connections()
            if active > self.stats["max_active_connections"]:
                self.stats["max_active_connections"] = active
                logger.info(f"📈 New peak: {active} active connections")
            
            # Alert if approaching capacity
            capacity_percent = active / (self.pool_size + self.max_overflow)
            if capacity_percent > self.ALERT_THRESHOLD_ACTIVE_PERCENT:
                logger.warning(f"⚠️ ALERT: {capacity_percent:.1%} pool utilization ({active} of {self.pool_size + self.max_overflow})")
        
        @event.listens_for(self.engine, "detach")
        def receive_detach(dbapi_conn, connection_record):
            """Log connection invalidation"""
            self.stats["connections_invalidated"] += 1
            logger.warning(f"🔴 Connection invalidated (total: {self.stats['connections_invalidated']})")

    # ========================
    # POOL MONITORING
    # ========================

    def get_pool_status(self) -> Dict:
        """Get detailed pool status"""
        
        pool = self.engine.pool
        active = pool.checkedout()
        idle = pool.size() - active
        overflow = pool.overflow()
        total_capacity = self.pool_size + self.max_overflow
        
        utilization = (active + overflow) / total_capacity
        utilization_percent = f"{utilization * 100:.1f}%"
        
        status = {
            "timestamp": datetime.now().isoformat(),
            "active_connections": active,
            "idle_connections": idle,
            "overflow_connections": overflow,
            "total_capacity": total_capacity,
            "utilization_percent": utilization_percent,
            "healthy": utilization < self.ALERT_THRESHOLD_ACTIVE_PERCENT,
            "stats": self.stats
        }
        
        # Add health warnings
        if utilization > self.ALERT_THRESHOLD_ACTIVE_PERCENT:
            status["alert"] = f"⚠️ High utilization: {utilization_percent}"
        
        if self.stats["connections_invalidated"] > 5:
            status["warning"] = f"⚠️ {self.stats['connections_invalidated']} connections invalidated"
        
        return status

    def _get_active_connections(self) -> int:
        """Get number of active connections"""
        
        try:
            pool = self.engine.pool
            return pool.checkedout()
        except Exception as e:
            logger.error(f"❌ Failed to get active connections: {e}")
            return 0

    def print_pool_status(self):
        """Pretty-print pool status to logs"""
        
        status = self.get_pool_status()
        logger.info(
            f"🔋 Pool Status: "
            f"Active={status['active_connections']}, "
            f"Idle={status['idle_connections']}, "
            f"Overflow={status['overflow_connections']}, "
            f"Utilization={status['utilization_percent']}"
        )
        
        if "alert" in status:
            logger.warning(status["alert"])
        if "warning" in status:
            logger.warning(status["warning"])

    # ========================
    # SESSION MANAGEMENT
    # ========================

    def create_session_factory(self):
        """Create thread-local session factory"""
        
        Session = scoped_session(sessionmaker(
            bind=self.engine,
            expire_on_commit=False,
            autoflush=False
        ))
        
        return Session

    def get_session(self):
        """Get database session"""
        
        return self.create_session_factory()()

    def dispose_pool(self):
        """Close all connections in pool (use for graceful shutdown)"""
        
        self.engine.dispose()
        logger.info("🛑 Connection pool disposed")

    # ========================
    # SCALING RECOMMENDATIONS
    # ========================

    def get_scaling_recommendations(self) -> Dict:
        """Provide scaling recommendations based on current usage"""
        
        status = self.get_pool_status()
        active = status["active_connections"]
        capacity = status["total_capacity"]
        utilization = active / capacity
        
        recommendations = {
            "current_peak": self.stats["max_active_connections"],
            "current_capacity": capacity,
            "current_utilization": f"{utilization * 100:.1f}%",
            "recommendations": []
        }
        
        # Scale if hitting 80% capacity frequently
        if utilization > 0.8:
            new_size = self.pool_size + 10
            new_overflow = self.max_overflow + 10
            recommendations["recommendations"].append(
                f"🚀 Scale up: Increase pool_size from {self.pool_size} to {new_size}"
            )
            recommendations["recommendations"].append(
                f"🚀 Scale up: Increase max_overflow from {self.max_overflow} to {new_overflow}"
            )
        
        # Alert if invalidations are high
        if self.stats["connections_invalidated"] > 10:
            recommendations["recommendations"].append(
                "⚠️ High connection invalidation; check network stability and query timeouts"
            )
        
        # Check connection leak
        if self.stats["max_active_connections"] > self.pool_size * 1.5:
            recommendations["recommendations"].append(
                "🔴 Possible connection leak; audit application code for unclosed connections"
            )
        
        return recommendations


# ========================
# USAGE EXAMPLES & FACTORY
# ========================

class DatabaseFactory:
    """Factory for creating database connections"""
    
    _instance = None
    
    @classmethod
    def initialize(
        cls,
        database_url: str,
        pool_size: int = 20,
        max_overflow: int = 40,
        environment: str = "development"
    ):
        """Initialize database factory (singleton)"""
        
        cls._instance = DatabasePoolManager(
            database_url=database_url,
            pool_size=pool_size,
            max_overflow=max_overflow,
            environment=environment
        )
        
        return cls._instance
    
    @classmethod
    def get_engine(self):
        """Get database engine"""
        
        if not self._instance:
            raise RuntimeError("DatabaseFactory not initialized")
        return self._instance.engine
    
    @classmethod
    def get_session(self):
        """Get database session"""
        
        if not self._instance:
            raise RuntimeError("DatabaseFactory not initialized")
        return self._instance.get_session()
    
    @classmethod
    def get_pool_manager(self):
        """Get pool manager instance"""
        
        if not self._instance:
            raise RuntimeError("DatabaseFactory not initialized")
        return self._instance


# ========================
# EXAMPLE CONFIGURATIONS
# ========================

POOL_CONFIGS = {
    "development": {
        "pool_size": 5,
        "max_overflow": 10,
        "pool_recycle": 3600,
        "echo": True
    },
    "staging": {
        "pool_size": 20,
        "max_overflow": 30,
        "pool_recycle": 3600,
        "echo": False
    },
    "production": {
        "pool_size": 50,
        "max_overflow": 100,
        "pool_recycle": 1800,  # Recycle more frequently
        "echo": False
    }
}


if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Example: Production setup
    print("=" * 60)
    print("DATABASE POOL CONFIGURATION EXAMPLES")
    print("=" * 60)
    
    # For PostgreSQL
    database_url = "postgresql+psycopg2://user:password@localhost/seo_platform"
    
    # For development
    print("\n1. DEVELOPMENT SETUP")
    print("-" * 60)
    db_dev = DatabasePoolManager(
        database_url=database_url,
        pool_size=5,
        max_overflow=10,
        environment="development"
    )
    print("Pool configuration: 5 base + 10 overflow (15 total)")
    print("Best for: 1-2 workers")
    
    # For staging
    print("\n2. STAGING SETUP")
    print("-" * 60)
    db_staging = DatabasePoolManager(
        database_url=database_url,
        pool_size=20,
        max_overflow=30,
        environment="staging"
    )
    print("Pool configuration: 20 base + 30 overflow (50 total)")
    print("Best for: 3-5 workers")
    
    # For production
    print("\n3. PRODUCTION SETUP")
    print("-" * 60)
    db_prod = DatabasePoolManager(
        database_url=database_url,
        pool_size=50,
        max_overflow=100,
        environment="production"
    )
    print("Pool configuration: 50 base + 100 overflow (150 total)")
    print("Best for: 8-15+ workers")
    
    # Example: Monitor pool
    print("\n4. POOL MONITORING")
    print("-" * 60)
    status = db_prod.get_pool_status()
    print(f"Active connections: {status['active_connections']}")
    print(f"Idle connections: {status['idle_connections']}")
    print(f"Utilization: {status['utilization_percent']}")
    
    # Example: Scaling recommendations
    print("\n5. SCALING RECOMMENDATIONS")
    print("-" * 60)
    recommendations = db_prod.get_scaling_recommendations()
    print(f"Current peak: {recommendations['current_peak']} connections")
    if recommendations['recommendations']:
        for rec in recommendations['recommendations']:
            print(f"  → {rec}")
    else:
        print("  ✅ No scaling recommendations at this time")
    
    # Cleanup
    db_prod.dispose_pool()
