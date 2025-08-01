import os
from typing import Optional
from fastapi import FastAPI
from loguru import logger

from src.core.config import settings


class DbContextExtensions:
    """数据库上下文扩展"""
    
    @staticmethod
    def add_db_context(app: FastAPI, configuration: Optional[dict] = None):
        """添加数据库上下文"""
        try:
            # 从环境变量获取数据库配置
            db_type = os.getenv("DB_TYPE", "").strip()
            db_connection_string = os.getenv("DB_CONNECTION_STRING", "").strip()
            
            if not db_type or not db_connection_string:
                # 从配置文件获取
                if configuration:
                    db_type_from_config = configuration.get("database", {}).get("type", "").lower()
                    if db_type_from_config == "postgres":
                        DbContextExtensions._setup_postgresql(app, configuration)
                    elif db_type_from_config == "sqlserver":
                        DbContextExtensions._setup_sqlserver(app, configuration)
                    else:
                        DbContextExtensions._setup_sqlite(app, configuration)
                else:
                    # 使用默认配置
                    DbContextExtensions._setup_sqlite(app, configuration)
            else:
                # 使用环境变量配置
                if db_type.lower() == "postgres":
                    DbContextExtensions._setup_postgresql_with_connection_string(app, db_connection_string)
                elif db_type.lower() == "sqlserver":
                    DbContextExtensions._setup_sqlserver_with_connection_string(app, db_connection_string)
                else:
                    DbContextExtensions._setup_sqlite_with_connection_string(app, db_connection_string)
            
            logger.info(f"数据库上下文配置完成: {db_type or 'sqlite'}")
            
        except Exception as e:
            logger.error(f"配置数据库上下文失败: {e}")
            raise
    
    @staticmethod
    def _setup_postgresql(app: FastAPI, configuration: Optional[dict]):
        """设置PostgreSQL"""
        # 这里可以添加PostgreSQL特定的配置
        logger.info("配置PostgreSQL数据库")
    
    @staticmethod
    def _setup_sqlserver(app: FastAPI, configuration: Optional[dict]):
        """设置SQL Server"""
        # 这里可以添加SQL Server特定的配置
        logger.info("配置SQL Server数据库")
    
    @staticmethod
    def _setup_sqlite(app: FastAPI, configuration: Optional[dict]):
        """设置SQLite"""
        # 这里可以添加SQLite特定的配置
        logger.info("配置SQLite数据库")
    
    @staticmethod
    def _setup_postgresql_with_connection_string(app: FastAPI, connection_string: str):
        """使用连接字符串设置PostgreSQL"""
        logger.info(f"使用连接字符串配置PostgreSQL: {connection_string[:20]}...")
    
    @staticmethod
    def _setup_sqlserver_with_connection_string(app: FastAPI, connection_string: str):
        """使用连接字符串设置SQL Server"""
        logger.info(f"使用连接字符串配置SQL Server: {connection_string[:20]}...")
    
    @staticmethod
    def _setup_sqlite_with_connection_string(app: FastAPI, connection_string: str):
        """使用连接字符串设置SQLite"""
        logger.info(f"使用连接字符串配置SQLite: {connection_string[:20]}...") 