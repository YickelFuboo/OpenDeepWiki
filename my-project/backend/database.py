from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base
from contextlib import contextmanager
import os
from config import DatabaseConfig

# 创建数据库引擎
database_url = DatabaseConfig.get_database_url()
engine = create_engine(
    database_url,
    echo=False,  # 设置为True可以看到SQL语句
    pool_pre_ping=True,
    pool_recycle=3600
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Session:
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_context():
    """数据库会话上下文管理器"""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def create_tables():
    """创建所有表"""
    from models import Base
    Base.metadata.create_all(bind=engine)


def drop_tables():
    """删除所有表"""
    from models import Base
    Base.metadata.drop_all(bind=engine)


def init_database():
    """初始化数据库"""
    # 确保数据目录存在
    os.makedirs("./data", exist_ok=True)
    
    # 创建表
    create_tables()
    
    # 创建初始数据
    from services.user_service import UserService
    from services.role_service import RoleService
    
    with get_db_context() as db:
        # 创建默认角色
        role_service = RoleService(db)
        admin_role = role_service.get_or_create_role("admin", "管理员")
        user_role = role_service.get_or_create_role("user", "普通用户")
        
        # 创建默认管理员用户
        user_service = UserService(db)
        admin_user = user_service.get_or_create_admin_user(
            "admin",
            "admin@example.com",
            "admin123"
        )
        
        print("数据库初始化完成")
        print(f"默认管理员账户: admin / admin123") 