"""
后台任务模块

提供各种后台任务处理功能，包括：
- 仓库处理任务
- 统计任务
- 访问日志处理任务
- 思维导图生成任务
- 数据迁移任务
"""

from .celery_app import celery_app
from .warehouse_tasks import *
from .statistics_tasks import *
from .access_log_tasks import *
from .minimap_tasks import *
from .data_migration_tasks import *

__all__ = [
    "celery_app",
    "process_warehouse_task",
    "schedule_warehouse_processing",
    "cleanup_failed_warehouses_task",
    "generate_statistics_task",
    "cleanup_old_access_records_task",
    "process_access_log_task",
    "generate_minimap_task",
    "data_migration_task"
] 