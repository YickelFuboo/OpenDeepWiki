"""
User-Service 数据库工厂模式
支持MySQL和PostgreSQL数据库
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
import logging

logger = logging.getLogger(__name__)


class DatabaseConnection(ABC):
    """数据库连接抽象基类"""
    
    @abstractmethod
    def create_engine(self, config: Dict[str, Any]) -> Engine:
        """创建数据库引擎"""
        pass
    
    @abstractmethod
    def get_session(self) -> Session:
        """获取数据库会话"""
        pass
    
    @abstractmethod
    def close(self):
        """关闭数据库连接"""
        pass


class PostgreSQLConnection(DatabaseConnection):
    """PostgreSQL数据库连接"""
    
    def __init__(self):
        self.engine: Optional[Engine] = None
        self.session_factory = None
    
    def create_engine(self, config: Dict[str, Any]) -> Engine:
        """创建PostgreSQL引擎"""
        try:
            # 构建PostgreSQL连接URL
            user = config.get('user', 'postgres')
            password = config.get('password', '')
            host = config.get('host', 'localhost')
            port = config.get('port', 5432)
            database = config.get('database', 'user_service')
            
            connection_url = f"postgresql://{user}:{password}@{host}:{port}/{database}"
            
            # 创建引擎
            self.engine = create_engine(
                connection_url,
                poolclass=QueuePool,
                pool_size=config.get('pool_size', 10),
                max_overflow=config.get('max_overflow', 20),
                pool_pre_ping=True,
                echo=config.get('echo', False)
            )
            
            # 创建会话工厂
            self.session_factory = sessionmaker(
                bind=self.engine,
                autocommit=False,
                autoflush=False
            )
            
            logger.info(f"PostgreSQL连接创建成功: {host}:{port}/{database}")
            return self.engine
            
        except Exception as e:
            logger.error(f"PostgreSQL连接创建失败: {e}")
            raise
    
    def get_session(self) -> Session:
        """获取PostgreSQL会话"""
        if not self.session_factory:
            raise RuntimeError("数据库引擎未初始化")
        return self.session_factory()
    
    def close(self):
        """关闭PostgreSQL连接"""
        if self.engine:
            self.engine.dispose()
            logger.info("PostgreSQL连接已关闭")


class MySQLConnection(DatabaseConnection):
    """MySQL数据库连接"""
    
    def __init__(self):
        self.engine: Optional[Engine] = None
        self.session_factory = None
    
    def create_engine(self, config: Dict[str, Any]) -> Engine:
        """创建MySQL引擎"""
        try:
            # 构建MySQL连接URL
            user = config.get('user', 'root')
            password = config.get('password', '')
            host = config.get('host', 'localhost')
            port = config.get('port', 3306)
            database = config.get('database', 'user_service')
            
            connection_url = f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}"
            
            # 创建引擎
            self.engine = create_engine(
                connection_url,
                poolclass=QueuePool,
                pool_size=config.get('pool_size', 10),
                max_overflow=config.get('max_overflow', 20),
                pool_pre_ping=True,
                echo=config.get('echo', False)
            )
            
            # 创建会话工厂
            self.session_factory = sessionmaker(
                bind=self.engine,
                autocommit=False,
                autoflush=False
            )
            
            logger.info(f"MySQL连接创建成功: {host}:{port}/{database}")
            return self.engine
            
        except Exception as e:
            logger.error(f"MySQL连接创建失败: {e}")
            raise
    
    def get_session(self) -> Session:
        """获取MySQL会话"""
        if not self.session_factory:
            raise RuntimeError("数据库引擎未初始化")
        return self.session_factory()
    
    def close(self):
        """关闭MySQL连接"""
        if self.engine:
            self.engine.dispose()
            logger.info("MySQL连接已关闭")


class DatabaseFactory:
    """数据库工厂类"""
    
    _connections: Dict[str, DatabaseConnection] = {}
    
    @classmethod
    def create_connection(cls, db_type: str, config: Dict[str, Any]) -> DatabaseConnection:
        """创建数据库连接
        
        Args:
            db_type: 数据库类型 ('postgresql' 或 'mysql')
            config: 数据库配置
            
        Returns:
            DatabaseConnection: 数据库连接实例
        """
        db_type = db_type.lower()
        
        if db_type not in cls._connections:
            if db_type == 'postgresql':
                connection = PostgreSQLConnection()
            elif db_type == 'mysql':
                connection = MySQLConnection()
            else:
                raise ValueError(f"不支持的数据库类型: {db_type}")
            
            # 创建引擎
            connection.create_engine(config)
            cls._connections[db_type] = connection
            
            logger.info(f"创建数据库连接: {db_type}")
        
        return cls._connections[db_type]
    
    @classmethod
    def get_connection(cls, db_type: str) -> Optional[DatabaseConnection]:
        """获取已存在的数据库连接"""
        return cls._connections.get(db_type.lower())
    
    @classmethod
    def close_all(cls):
        """关闭所有数据库连接"""
        for connection in cls._connections.values():
            connection.close()
        cls._connections.clear()
        logger.info("所有数据库连接已关闭")


# 全局数据库连接实例
_db_connection: Optional[DatabaseConnection] = None


def init_database():
    """初始化数据库连接"""
    global _db_connection
    
    from config.settings import get_settings
    settings = get_settings()
    
    try:
        db_type = settings.database.db_type.lower()
        
        if db_type == "postgresql":
            config = {
                'host': settings.database.postgresql_host,
                'port': settings.database.postgresql_port,
                'user': settings.database.postgresql_user,
                'password': settings.database.postgresql_password,
                'database': settings.database.postgresql_database,
                'pool_size': settings.database.pool_size,
                'max_overflow': settings.database.max_overflow
            }
        elif db_type == "mysql":
            config = {
                'host': settings.database.mysql_host,
                'port': settings.database.mysql_port,
                'user': settings.database.mysql_user,
                'password': settings.database.mysql_password,
                'database': settings.database.mysql_database,
                'pool_size': settings.database.pool_size,
                'max_overflow': settings.database.max_overflow
            }
        else:
            raise ValueError(f"不支持的数据库类型: {db_type}")
        
        _db_connection = DatabaseFactory.create_connection(db_type, config)
        logger.info(f"数据库连接初始化成功: {db_type}")
        
    except Exception as e:
        logger.error(f"初始化数据库连接失败: {e}")
        raise


def get_db() -> Session:
    """获取数据库会话 - FastAPI依赖注入使用"""
    global _db_connection
    
    if _db_connection is None:
        try:
            init_database()
        except Exception as e:
            logger.error(f"数据库初始化失败: {e}")
            raise RuntimeError("数据库服务不可用")
    
    if not _db_connection:
        raise RuntimeError("数据库未初始化")
    return _db_connection.get_session()


def close_db():
    """关闭数据库连接"""
    global _db_connection
    if _db_connection:
        _db_connection.close()
        _db_connection = None 