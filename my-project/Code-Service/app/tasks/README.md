# 后台任务模块

## 概述

后台任务模块负责处理系统中的各种异步任务，包括仓库处理、统计生成、访问日志处理、思维导图生成和数据迁移等。该模块基于Celery实现，提供了可靠的任务队列和定时任务功能。

## 功能特性

### 🎯 核心功能

- **仓库处理任务** - 异步处理仓库克隆、分析和文档生成
- **统计任务** - 生成系统统计数据和访问统计
- **访问日志处理** - 异步处理访问日志和统计
- **思维导图生成** - 自动生成知识图谱和思维导图
- **数据迁移** - 系统数据迁移和初始化
- **定时任务** - 支持各种定时任务的调度

### 🔄 任务队列

- **仓库队列** - 处理仓库相关的任务
- **统计队列** - 处理统计相关的任务
- **访问日志队列** - 处理访问日志相关的任务
- **思维导图队列** - 处理思维导图生成任务
- **迁移队列** - 处理数据迁移任务

### ⏰ 定时任务

- **仓库处理** - 每5分钟检查并处理待处理的仓库
- **仓库增量更新** - 每小时检查需要更新的仓库
- **统计生成** - 每天凌晨1点生成统计数据
- **访问日志清理** - 每天凌晨2点清理旧访问记录
- **思维导图生成** - 每10分钟检查并生成思维导图
- **访问日志处理** - 每30秒处理一次访问日志

## 目录结构

```
tasks/
├── README.md                    # 模块文档
├── __init__.py                  # 模块初始化
├── celery_app.py               # Celery应用配置
├── warehouse_tasks.py          # 仓库处理任务
├── statistics_tasks.py         # 统计任务
├── access_log_tasks.py         # 访问日志任务
├── minimap_tasks.py            # 思维导图任务
└── data_migration_tasks.py     # 数据迁移任务
```

## 配置说明

### 环境变量

```env
# Redis配置（Celery后端）
REDIS_URL=redis://localhost:6379/0

# 仓库处理配置
UPDATE_INTERVAL=7
ENABLE_WAREHOUSE_COMMIT=true

# 任务配置
TASK_MAX_SIZE_PER_USER=5
```

### Celery配置

```python
# Celery应用配置
CELERY_BROKER_URL = "redis://localhost:6379/0"
CELERY_RESULT_BACKEND = "redis://localhost:6379/0"

# 任务执行配置
TASK_SERIALIZER = "json"
ACCEPT_CONTENT = ["json"]
RESULT_SERIALIZER = "json"
TIMEZONE = "UTC"
ENABLE_UTC = True

# 任务超时配置
TASK_TIME_LIMIT = 30 * 60  # 30分钟
TASK_SOFT_TIME_LIMIT = 25 * 60  # 25分钟

# 工作进程配置
WORKER_PREFETCH_MULTIPLIER = 1
WORKER_MAX_TASKS_PER_CHILD = 1000
```

### 定时任务配置

```python
# 定时任务调度
BEAT_SCHEDULE = {
    # 仓库处理任务 - 每5分钟
    "process-pending-warehouses": {
        "task": "tasks.warehouse_tasks.schedule_warehouse_processing",
        "schedule": 300.0,
    },
    
    # 仓库增量更新任务 - 每小时
    "process-warehouse-updates": {
        "task": "tasks.warehouse_tasks.schedule_warehouse_updates",
        "schedule": 3600.0,
    },
    
    # 统计任务 - 每天凌晨1点
    "generate-daily-statistics": {
        "task": "tasks.statistics_tasks.generate_statistics_task",
        "schedule": crontab(hour=1, minute=0),
    },
    
    # 思维导图生成任务 - 每10分钟
    "generate-minimaps": {
        "task": "tasks.minimap_tasks.generate_minimap_task",
        "schedule": 600.0,
    },
}
```

## 任务类型

### 1. 仓库处理任务

#### 主要任务

- **process_warehouse_task** - 处理单个仓库
- **schedule_warehouse_processing** - 调度仓库处理任务
- **schedule_warehouse_updates** - 调度仓库增量更新
- **process_warehouse_update_task** - 处理仓库增量更新
- **cleanup_failed_warehouses_task** - 清理失败的仓库

#### 使用示例

```python
from tasks.warehouse_tasks import process_warehouse_task

# 提交仓库处理任务
result = process_warehouse_task.delay("warehouse-id")
print(f"任务ID: {result.id}")

# 获取任务结果
task_result = result.get()
print(f"任务结果: {task_result}")
```

### 2. 统计任务

#### 主要任务

- **generate_statistics_task** - 生成统计数据
- **cleanup_old_access_records_task** - 清理旧访问记录
- **generate_system_statistics_task** - 生成系统统计
- **generate_warehouse_statistics_task** - 生成仓库统计

#### 使用示例

```python
from tasks.statistics_tasks import generate_statistics_task

# 生成指定日期的统计数据
result = generate_statistics_task.delay("2023-01-01")

# 清理旧访问记录
from tasks.statistics_tasks import cleanup_old_access_records_task
result = cleanup_old_access_records_task.delay(90)  # 保留90天
```

### 3. 访问日志任务

#### 主要任务

- **process_access_log_task** - 处理访问日志
- **cleanup_old_access_logs_task** - 清理旧访问日志
- **generate_access_statistics_task** - 生成访问统计

#### 使用示例

```python
from tasks.access_log_tasks import enqueue_access_log

# 添加访问日志到队列
log_data = {
    "resource_type": "warehouse",
    "resource_id": "warehouse-123",
    "user_id": "user-123",
    "ip_address": "192.168.1.1",
    "path": "/api/warehouses",
    "method": "GET",
    "status_code": 200,
    "response_time": 150
}

enqueue_access_log(log_data)
```

### 4. 思维导图任务

#### 主要任务

- **generate_minimap_task** - 生成思维导图
- **regenerate_minimap_task** - 重新生成思维导图
- **cleanup_old_minimaps_task** - 清理旧思维导图
- **validate_minimap_task** - 验证思维导图数据

#### 使用示例

```python
from tasks.minimap_tasks import generate_minimap_task

# 生成思维导图
result = generate_minimap_task.delay()

# 重新生成指定仓库的思维导图
from tasks.minimap_tasks import regenerate_minimap_task
result = regenerate_minimap_task.delay("warehouse-id")
```

### 5. 数据迁移任务

#### 主要任务

- **data_migration_task** - 执行数据迁移
- **initialize_users_task** - 初始化用户数据
- **migrate_warehouses_task** - 迁移仓库数据
- **migrate_documents_task** - 迁移文档数据
- **update_indexes_task** - 更新数据库索引
- **backup_data_task** - 数据备份

#### 使用示例

```python
from tasks.data_migration_tasks import data_migration_task

# 执行数据迁移
result = data_migration_task.delay()

# 数据备份
from tasks.data_migration_tasks import backup_data_task
result = backup_data_task.delay()
```

## 启动和管理

### 启动Celery Worker

```bash
# 启动默认队列的worker
celery -A tasks.celery_app worker --loglevel=info

# 启动特定队列的worker
celery -A tasks.celery_app worker --loglevel=info -Q warehouse,statistics

# 启动所有队列的worker
celery -A tasks.celery_app worker --loglevel=info -Q default,warehouse,statistics,access_log,minimap,migration
```

### 启动Celery Beat（定时任务）

```bash
# 启动定时任务调度器
celery -A tasks.celery_app beat --loglevel=info

# 使用数据库存储定时任务
celery -A tasks.celery_app beat --loglevel=info --scheduler django_celery_beat.schedulers:DatabaseScheduler
```

### 监控任务

```bash
# 查看任务状态
celery -A tasks.celery_app inspect active

# 查看队列状态
celery -A tasks.celery_app inspect stats

# 查看定时任务
celery -A tasks.celery_app inspect scheduled
```

## 监控和日志

### 任务监控

```python
from tasks.celery_app import celery_app

# 获取活跃任务
active_tasks = celery_app.control.inspect().active()

# 获取任务统计
stats = celery_app.control.inspect().stats()

# 获取定时任务
scheduled_tasks = celery_app.control.inspect().scheduled()
```

### 日志配置

```python
import logging

# 配置Celery日志
celery_logger = logging.getLogger("celery")
celery_logger.setLevel(logging.INFO)

# 配置任务日志
task_logger = logging.getLogger("tasks")
task_logger.setLevel(logging.INFO)
```

## 错误处理

### 任务重试

```python
from celery import current_task

@celery_app.task(bind=True, max_retries=3)
def process_warehouse_task(self, warehouse_id: str):
    try:
        # 任务逻辑
        pass
    except Exception as exc:
        # 重试任务
        self.retry(countdown=60, exc=exc)
```

### 错误回调

```python
@celery_app.task(bind=True)
def process_warehouse_task(self, warehouse_id: str):
    try:
        # 任务逻辑
        pass
    except Exception as exc:
        # 记录错误
        logger.error(f"任务失败: {warehouse_id}, 错误: {exc}")
        raise
```

## 性能优化

### 任务优化

1. **任务分片** - 将大任务分解为小任务
2. **并发控制** - 使用信号量控制并发数
3. **资源限制** - 设置任务超时和资源限制
4. **队列分离** - 按任务类型分离队列

### 监控优化

1. **任务监控** - 实时监控任务状态
2. **性能指标** - 收集任务执行时间
3. **错误追踪** - 记录和追踪任务错误
4. **资源监控** - 监控系统资源使用

## 故障排除

### 常见问题

1. **任务不执行**
   - 检查Celery Worker是否启动
   - 检查Redis连接是否正常
   - 检查任务队列配置

2. **任务超时**
   - 增加任务超时时间
   - 优化任务逻辑
   - 检查系统资源

3. **内存泄漏**
   - 检查任务是否正确释放资源
   - 监控内存使用情况
   - 定期重启Worker

### 调试方法

1. **启用详细日志**
   ```bash
   celery -A tasks.celery_app worker --loglevel=debug
   ```

2. **检查任务状态**
   ```python
   from tasks.celery_app import celery_app
   result = celery_app.AsyncResult(task_id)
   print(f"任务状态: {result.status}")
   ```

3. **监控队列**
   ```bash
   celery -A tasks.celery_app inspect active
   celery -A tasks.celery_app inspect stats
   ```

## 扩展

### 添加新任务

1. 在相应的任务文件中添加新任务
2. 在Celery配置中注册任务
3. 添加相应的测试用例
4. 更新文档

### 自定义队列

```python
# 创建自定义队列
@celery_app.task(queue="custom")
def custom_task():
    pass

# 启动自定义队列的worker
celery -A tasks.celery_app worker -Q custom
```

---

**注意**: 后台任务模块是系统稳定运行的重要保障，请确保正确配置和监控任务执行状态。 