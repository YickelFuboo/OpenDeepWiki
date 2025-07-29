import os
from celery import Celery
from celery.schedules import crontab
from config import get_settings

# 获取配置
settings = get_settings()

# 创建Celery应用
celery_app = Celery(
    "opendeepwiki",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=[
        "tasks.warehouse_tasks",
        "tasks.statistics_tasks", 
        "tasks.access_log_tasks",
        "tasks.minimap_tasks",
        "tasks.data_migration_tasks"
    ]
)

# Celery配置
celery_app.conf.update(
    # 任务序列化格式
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    
    # 任务执行配置
    task_track_started=True,
    task_time_limit=30 * 60,  # 30分钟超时
    task_soft_time_limit=25 * 60,  # 25分钟软超时
    
    # 工作进程配置
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    
    # 结果配置
    result_expires=3600,  # 结果保存1小时
    
    # 定时任务配置
    beat_schedule={
        # 仓库处理任务 - 每5分钟检查待处理仓库
        "process-pending-warehouses": {
            "task": "tasks.warehouse_tasks.schedule_warehouse_processing",
            "schedule": 300.0,  # 5分钟
        },
        
        # 仓库增量更新任务 - 每小时检查需要更新的仓库
        "process-warehouse-updates": {
            "task": "tasks.warehouse_tasks.schedule_warehouse_updates",
            "schedule": 3600.0,  # 1小时
        },
        
        # 清理失败仓库任务 - 每小时清理
        "cleanup-failed-warehouses": {
            "task": "tasks.warehouse_tasks.cleanup_failed_warehouses_task",
            "schedule": 3600.0,  # 1小时
        },
        
        # 统计任务 - 每天凌晨1点执行
        "generate-daily-statistics": {
            "task": "tasks.statistics_tasks.generate_statistics_task",
            "schedule": crontab(hour=1, minute=0),  # 每天凌晨1点
        },
        
        # 清理旧访问记录 - 每天凌晨2点执行
        "cleanup-old-access-records": {
            "task": "tasks.statistics_tasks.cleanup_old_access_records_task",
            "schedule": crontab(hour=2, minute=0),  # 每天凌晨2点
        },
        
        # 思维导图生成任务 - 每10分钟检查
        "generate-minimaps": {
            "task": "tasks.minimap_tasks.generate_minimap_task",
            "schedule": 600.0,  # 10分钟
        },
        
        # 访问日志处理任务 - 每30秒处理一次
        "process-access-logs": {
            "task": "tasks.access_log_tasks.process_access_log_task",
            "schedule": 30.0,  # 30秒
        },
    },
    
    # 任务路由
    task_routes={
        "tasks.warehouse_tasks.*": {"queue": "warehouse"},
        "tasks.statistics_tasks.*": {"queue": "statistics"},
        "tasks.access_log_tasks.*": {"queue": "access_log"},
        "tasks.minimap_tasks.*": {"queue": "minimap"},
        "tasks.data_migration_tasks.*": {"queue": "migration"},
    },
    
    # 队列配置
    task_default_queue="default",
    task_queues={
        "default": {},
        "warehouse": {"exchange": "warehouse", "routing_key": "warehouse"},
        "statistics": {"exchange": "statistics", "routing_key": "statistics"},
        "access_log": {"exchange": "access_log", "routing_key": "access_log"},
        "minimap": {"exchange": "minimap", "routing_key": "minimap"},
        "migration": {"exchange": "migration", "routing_key": "migration"},
    },
)

# 自动发现任务
celery_app.autodiscover_tasks()

if __name__ == "__main__":
    celery_app.start() 