"""
异步任务管理基础框架
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from celery import Celery, current_task
from celery.result import AsyncResult
import time

logger = logging.getLogger(__name__)


class BaseTask(ABC):
    """任务基类"""
    
    def __init__(self, celery_app: Celery):
        self.celery_app = celery_app
    
    @abstractmethod
    def execute(self, *args, **kwargs) -> Dict[str, Any]:
        """执行任务的具体逻辑"""
        pass
    
    def update_progress(self, progress: int, message: str = ""):
        """更新任务进度"""
        if current_task:
            current_task.update_state(
                state="PROGRESS",
                meta={
                    "progress": progress,
                    "message": message,
                    "timestamp": time.time()
                }
            )
    
    def log_task_info(self, message: str, level: str = "info"):
        """记录任务日志"""
        log_func = getattr(logger, level.lower(), logger.info)
        task_id = current_task.request.id if current_task else "unknown"
        log_func(f"[Task {task_id}] {message}")


class TaskManager:
    """任务管理器"""
    
    def __init__(self, celery_app: Celery):
        self.celery_app = celery_app
        self._tasks: Dict[str, BaseTask] = {}
    
    def register_task(self, name: str, task: BaseTask):
        """注册任务"""
        self._tasks[name] = task
        logger.info(f"注册任务: {name}")
    
    def get_task(self, name: str) -> Optional[BaseTask]:
        """获取任务"""
        return self._tasks.get(name)
    
    def submit_task(self, task_name: str, *args, **kwargs) -> AsyncResult:
        """提交任务"""
        if task_name not in self._tasks:
            raise ValueError(f"任务不存在: {task_name}")
        
        task = self._tasks[task_name]
        return self.celery_app.send_task(task_name, args=args, kwargs=kwargs)
    
    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """获取任务状态"""
        result = AsyncResult(task_id, app=self.celery_app)
        return {
            "task_id": task_id,
            "status": result.status,
            "result": result.result if result.ready() else None,
            "info": result.info if hasattr(result, 'info') else None
        }
    
    def cancel_task(self, task_id: str) -> bool:
        """取消任务"""
        result = AsyncResult(task_id, app=self.celery_app)
        if result.state in ['PENDING', 'STARTED']:
            result.revoke(terminate=True)
            logger.info(f"取消任务: {task_id}")
            return True
        return False
    
    def get_running_tasks(self) -> Dict[str, Any]:
        """获取正在运行的任务"""
        active_tasks = self.celery_app.control.inspect().active()
        return active_tasks or {}
    
    def get_pending_tasks(self) -> Dict[str, Any]:
        """获取待处理的任务"""
        pending_tasks = self.celery_app.control.inspect().reserved()
        return pending_tasks or {}


class TaskRetryMixin:
    """任务重试混入类"""
    
    def __init__(self, max_retries: int = 3, retry_delay: int = 60):
        self.max_retries = max_retries
        self.retry_delay = retry_delay
    
    def should_retry(self, exception: Exception, retry_count: int) -> bool:
        """判断是否应该重试"""
        # 可以根据异常类型决定是否重试
        retryable_exceptions = (
            ConnectionError,
            TimeoutError,
            OSError
        )
        
        if isinstance(exception, retryable_exceptions):
            return retry_count < self.max_retries
        
        return False
    
    def get_retry_delay(self, retry_count: int) -> int:
        """获取重试延迟时间（指数退避）"""
        return self.retry_delay * (2 ** retry_count)


class TaskMonitor:
    """任务监控器"""
    
    def __init__(self, celery_app: Celery):
        self.celery_app = celery_app
    
    def get_task_metrics(self) -> Dict[str, Any]:
        """获取任务指标"""
        inspector = self.celery_app.control.inspect()
        
        return {
            "active": len(inspector.active() or {}),
            "reserved": len(inspector.reserved() or {}),
            "registered": len(inspector.registered() or {}),
            "stats": inspector.stats() or {}
        }
    
    def get_worker_status(self) -> Dict[str, Any]:
        """获取工作节点状态"""
        inspector = self.celery_app.control.inspect()
        return inspector.stats() or {}
    
    def ping_workers(self) -> Dict[str, Any]:
        """检查工作节点连接"""
        inspector = self.celery_app.control.inspect()
        return inspector.ping() or {}


# 全局任务管理器实例
_task_manager: Optional[TaskManager] = None
_task_monitor: Optional[TaskMonitor] = None


def init_task_manager(celery_app: Celery):
    """初始化任务管理器"""
    global _task_manager, _task_monitor
    _task_manager = TaskManager(celery_app)
    _task_monitor = TaskMonitor(celery_app)
    logger.info("任务管理器初始化完成")


def get_task_manager() -> TaskManager:
    """获取任务管理器"""
    if _task_manager is None:
        raise RuntimeError("任务管理器未初始化")
    return _task_manager


def get_task_monitor() -> TaskMonitor:
    """获取任务监控器"""
    if _task_monitor is None:
        raise RuntimeError("任务监控器未初始化")
    return _task_monitor 