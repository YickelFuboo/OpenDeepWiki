using System.Diagnostics;
using KoalaWiki.Domains;
using KoalaWiki.Domains.Warehouse;
using Microsoft.EntityFrameworkCore;

namespace KoalaWiki.BackendService;

public class WarehouseTask(
    ILogger<WarehouseTask> logger,
    DocumentsService documentsService,
    IServiceProvider service)
    : BackgroundService
{
    private static readonly ActivitySource s_activitySource = new("KoalaWiki.Warehouse");

    protected override async Task ExecuteAsync(CancellationToken stoppingToken)
    {
        // 初始化延迟，避免服务启动时立即执行
        await Task.Delay(1000, stoppingToken);

        // 创建服务作用域，用于获取数据库上下文
        await using var scope = service.CreateAsyncScope();
        var dbContext = scope.ServiceProvider.GetService<IKoalaWikiContext>();
        
        // 主循环：持续监控待处理的仓库
        while (!stoppingToken.IsCancellationRequested)
        {
            // 查询待处理或处理中的仓库，优先处理正在处理中的仓库
            var value = await dbContext!.Warehouses
                .Where(x => x.Status == WarehouseStatus.Pending || x.Status == WarehouseStatus.Processing)
                // 处理中优先：确保正在处理的仓库优先完成
                .OrderByDescending(x => x.Status == WarehouseStatus.Processing)
                .FirstOrDefaultAsync(stoppingToken);

            // 如果没有找到待处理的仓库，等待5秒后继续
            if (value == null)
            {
                // 如果没有仓库，等待一段时间
                await Task.Delay(1000 * 5, stoppingToken);
                continue;
            }

            // 创建分布式追踪活动，用于监控仓库处理过程
            using var activity = s_activitySource.CreateActivity("仓库处理任务", ActivityKind.Server);
            activity?.SetTag("warehouse.id", value.Id);  // 仓库ID
            activity?.SetTag("warehouse.name", value.Name);  // 仓库名称
            activity?.SetTag("warehouse.type", value.Type);  // 仓库类型
            activity?.SetTag("warehouse.address", value.Address);  // 仓库地址
            activity?.SetTag("warehouse.status", value.Status.ToString());  // 仓库状态

            try
            {
                Document document;

                // 处理Git类型的仓库
                if (value?.Type?.Equals("git", StringComparison.OrdinalIgnoreCase) == true)
                {
                    // 设置Git相关的追踪标签
                    activity?.SetTag("git.address", value.Address);  // Git仓库地址
                    activity?.SetTag("git.branch", value?.Branch);  // Git分支
                    activity?.SetTag("git.has_username", !string.IsNullOrEmpty(value?.GitUserName));  // 是否有用户名
                    activity?.SetTag("git.has_password", !string.IsNullOrEmpty(value?.GitPassword));  // 是否有密码

                    // 开始克隆Git仓库
                    logger.LogInformation("开始拉取仓库：{Address}", value.Address);
                    var info = GitService.CloneRepository(value.Address, value?.GitUserName ?? string.Empty,
                        value?.GitPassword ?? string.Empty, value?.Branch);

                    logger.LogInformation("仓库拉取完成：{RepositoryName}, 分支：{BranchName}", info.RepositoryName,
                        info.BranchName);

                    // 设置Git克隆结果的追踪标签
                    activity?.SetTag("git.repository_name", info.RepositoryName);  // 仓库名称
                    activity?.SetTag("git.branch_name", info.BranchName);  // 分支名称
                    activity?.SetTag("git.organization", info.Organization);  // 组织名称
                    activity?.SetTag("git.version", info.Version);  // 版本信息
                    activity?.SetTag("git.local_path", info.LocalPath);  // 本地路径

                    // 更新仓库信息到数据库：设置仓库名称、分支、版本、状态和组织名称
                    await dbContext!.Warehouses.Where(x => x.Id == value.Id)
                        .ExecuteUpdateAsync(x => x.SetProperty(a => a.Name, info.RepositoryName)  // 更新仓库名称
                            .SetProperty(x => x.Branch, info.BranchName)  // 更新分支名称
                            .SetProperty(x => x.Version, info.Version)  // 更新版本信息
                            .SetProperty(x => x.Status, WarehouseStatus.Processing)  // 设置状态为处理中
                            .SetProperty(x => x.OrganizationName, info.Organization), stoppingToken);  // 更新组织名称

                    logger.LogInformation("更新仓库信息到数据库完成，仓库ID：{Id}", value.Id);

                    // 检查是否已存在文档记录
                    if (await dbContext.Documents.AnyAsync(x => x.WarehouseId == value.Id, stoppingToken))
                    {
                        // 获取现有的文档记录
                        document = await dbContext.Documents.FirstAsync(x => x.WarehouseId == value.Id,
                            stoppingToken);
                        logger.LogInformation("获取现有文档记录，文档ID：{Id}", document.Id);
                    }
                    else
                    {
                        // 创建新的文档记录
                        document = new Document
                        {
                            Id = Guid.NewGuid().ToString(),  // 生成唯一ID
                            WarehouseId = value.Id,  // 关联仓库ID
                            CreatedAt = DateTime.UtcNow,  // 创建时间
                            LastUpdate = DateTime.UtcNow,  // 最后更新时间
                            GitPath = info.LocalPath,  // Git本地路径
                            Status = WarehouseStatus.Pending  // 初始状态为待处理
                        };
                        logger.LogInformation("创建文档记录，文档ID：{Id}", document.Id);
                        await dbContext.Documents.AddAsync(document, stoppingToken);
                        logger.LogInformation("添加新文档记录完成，文档ID：{Id}", document.Id);

                        // 保存数据库更改
                        await dbContext.SaveChangesAsync(stoppingToken);
                    }

                    logger.LogInformation("数据库更改保存完成，开始处理文档。");

                    // 调用文档处理服务，进行AI分析、文档生成等处理
                    // 其Activity将作为当前Activity的子Activity
                    await documentsService.HandleAsync(document, value, dbContext,
                        value.Address.Replace(".git", string.Empty));
                }
                // 处理文件类型的仓库
                else if (value?.Type?.Equals("file", StringComparison.OrdinalIgnoreCase) == true)
                {
                    // 设置文件相关的追踪标签
                    activity?.SetTag("file.address", value.Address);

                    // 更新仓库状态为处理中
                    await dbContext!.Warehouses.Where(x => x.Id == value.Id)
                        .ExecuteUpdateAsync(x => x.SetProperty(x => x.Status, WarehouseStatus.Processing),
                            stoppingToken);

                    logger.LogInformation("更新仓库信息到数据库完成，仓库ID：{Id}", value.Id);

                    // 检查是否已存在文档记录
                    if (await dbContext.Documents.AnyAsync(x => x.WarehouseId == value.Id, stoppingToken))
                    {
                        // 获取现有的文档记录
                        document = await dbContext.Documents.FirstAsync(x => x.WarehouseId == value.Id,
                            stoppingToken);
                        logger.LogInformation("获取现有文档记录，文档ID：{Id}", document.Id);
                    }
                    else
                    {
                        // 创建新的文档记录
                        document = new Document
                        {
                            Id = Guid.NewGuid().ToString(),  // 生成唯一ID
                            WarehouseId = value.Id,  // 关联仓库ID
                            CreatedAt = DateTime.UtcNow,  // 创建时间
                            LastUpdate = DateTime.UtcNow,  // 最后更新时间
                            GitPath = value.Address,  // 文件路径
                            Status = WarehouseStatus.Pending  // 初始状态为待处理
                        };
                        logger.LogInformation("创建文档记录，文档ID：{Id}", document.Id);
                        await dbContext.Documents.AddAsync(document, stoppingToken);
                        logger.LogInformation("添加新文档记录完成，文档ID：{Id}", document.Id);

                        // 保存数据库更改
                        await dbContext.SaveChangesAsync(stoppingToken);
                    }

                    logger.LogInformation("数据库更改保存完成，开始处理文档。");

                    // 调用文档处理服务，进行AI分析、文档生成等处理
                    // 其Activity将作为当前Activity的子Activity
                    await documentsService.HandleAsync(document, value, dbContext,
                        value.Address.Replace(".git", string.Empty));
                }
                // 处理不支持的仓库类型
                else
                {
                    // 设置错误相关的追踪标签
                    activity?.SetTag("error", "不支持的仓库类型");
                    logger.LogError("不支持的仓库类型：{Type}", value.Type);
                    
                    // 更新仓库状态为失败，并记录错误信息
                    await dbContext.Warehouses.Where(x => x.Id == value.Id)
                        .ExecuteUpdateAsync(x => x.SetProperty(a => a.Status, WarehouseStatus.Failed)  // 设置状态为失败
                            .SetProperty(x => x.Error, "不支持的仓库类型"), stoppingToken);  // 记录错误信息

                    logger.LogInformation("更新仓库状态为失败，仓库地址：{address}", value.Address);
                    activity?.SetTag("warehouse.final_status", "failed");
                    return;  // 结束当前处理
                }

                logger.LogInformation("文档处理完成，仓库地址：{address}", value.Address);

                // 更新仓库状态为完成
                activity?.SetTag("document.id", document.Id);

                // 更新仓库状态为已完成，并清空错误信息
                await dbContext.Warehouses.Where(x => x.Id == value.Id)
                    .ExecuteUpdateAsync(x => x.SetProperty(a => a.Status, WarehouseStatus.Completed)  // 设置状态为已完成
                        .SetProperty(x => x.Error, string.Empty), stoppingToken);  // 清空错误信息

                logger.LogInformation("更新仓库状态为完成，仓库地址：{address}", value.Address);

                // 更新文档的最后更新时间和状态
                await dbContext.Documents.Where(x => x.Id == document.Id)
                    .ExecuteUpdateAsync(x => x.SetProperty(a => a.LastUpdate, DateTime.UtcNow)  // 更新最后更新时间
                        .SetProperty(a => a.Status, WarehouseStatus.Completed), stoppingToken);  // 设置状态为已完成

                logger.LogInformation("文档状态更新为完成，仓库地址：{address}", value.Address);

                // 设置成功相关的追踪标签
                activity?.SetTag("processing.success", true);
                activity?.SetTag("warehouse.final_status", "completed");
            }
            catch (Exception e)
            {
                // 设置异常相关的追踪标签
                activity?.SetTag("error.message", e.Message);  // 错误消息
                activity?.SetTag("error.type", e.GetType().Name);  // 错误类型
                activity?.SetTag("error.occurred", true);  // 标记发生错误
                activity?.SetTag("warehouse.final_status", "failed");  // 最终状态为失败

                // 记录错误日志
                logger.LogError("发生错误：{e}", e);
                
                // 等待5秒后继续，避免频繁重试
                await Task.Delay(1000 * 5, stoppingToken);

                // 更新仓库状态为失败，并记录详细的错误信息
                await dbContext.Warehouses.Where(x => x.Id == value.Id)
                    .ExecuteUpdateAsync(x => x.SetProperty(a => a.Status, WarehouseStatus.Failed)  // 设置状态为失败
                        .SetProperty(x => x.Error, e.ToString()), stoppingToken);  // 记录完整错误信息
            }
        }
    }
}