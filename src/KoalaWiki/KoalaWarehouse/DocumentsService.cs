using System.Diagnostics;
using System.Runtime.CompilerServices;
using System.Text;
using System.Text.Json;
using System.Text.RegularExpressions;
using KoalaWiki.Domains;
using KoalaWiki.Domains.Warehouse;
using KoalaWiki.Entities;
using KoalaWiki.Functions;
using KoalaWiki.KoalaWarehouse.DocumentPending;
using KoalaWiki.KoalaWarehouse.GenerateThinkCatalogue;
using KoalaWiki.KoalaWarehouse.Overview;
using KoalaWiki.Options;
using Microsoft.EntityFrameworkCore;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.OpenAI;

namespace KoalaWiki.KoalaWarehouse;

public partial class DocumentsService
{
    private static readonly ActivitySource s_activitySource = new("KoalaWiki.Warehouse");

    /// <summary>
    /// Handles the asynchronous processing of a document within a specified warehouse, including parsing directory structures, generating update logs, and saving results to the database.
    /// </summary>
    /// <param name="document">The document to be processed.</param>
    /// <param name="warehouse">The warehouse associated with the document.</param>
    /// <param name="dbContext">The database context used for data operations.</param>
    /// <param name="gitRepository">The Git repository address related to the document.</param>
    /// <returns>A task representing the asynchronous operation.</returns>
    public async Task HandleAsync(Document document, Warehouse warehouse, IKoalaWikiContext dbContext,
        string gitRepository)
    {
        // 在WarehouseTask的Activity上下文中创建子Activity，形成完整的调用链
        // 用于分布式追踪，监控整个文档处理流程
        using var activity = s_activitySource.StartActivity(ActivityKind.Server);
        activity?.SetTag("warehouse.id", warehouse.Id);  // 设置仓库ID追踪标签
        activity?.SetTag("warehouse.name", warehouse.Name);  // 设置仓库名称追踪标签
        activity?.SetTag("document.id", document.Id);  // 设置文档ID追踪标签
        activity?.SetTag("git.repository", gitRepository);  // 设置Git仓库地址追踪标签

        // 创建内部活动，用于追踪文档处理的完整流程
        using var handle = Activity.Current?.Source.StartActivity("处理文档完整流程",
            ActivityKind.Internal);

        // 获取仓库的本地路径，用于文件系统操作
        var path = document.GitPath;

        // 创建AI内核实例，用于调用AI模型进行文档生成
        var kernel = KernelFactory.GetKernel(OpenAIOptions.Endpoint,
            OpenAIOptions.ChatApiKey,
            path, OpenAIOptions.ChatModel);

        // 创建文件操作专用的AI内核实例，禁用某些功能以提高性能
        var fileKernel = KernelFactory.GetKernel(OpenAIOptions.Endpoint,
            OpenAIOptions.ChatApiKey, path, OpenAIOptions.ChatModel, false);

        // 步骤1: 读取生成README
        string readme;
        using (var readmeActivity = s_activitySource.StartActivity("读取生成README"))
        {
            readmeActivity?.SetTag("warehouse.id", warehouse.Id);  // 设置仓库ID追踪标签
            readmeActivity?.SetTag("path", path);  // 设置路径追踪标签
            
            // 调用AI生成README文档
            readme = await GenerateReadMe(warehouse, path, dbContext);
            
            readmeActivity?.SetTag("readme.length", readme?.Length ?? 0);  // 记录README长度
        }

        // 步骤2: 读取并且生成目录结构
        string catalogue;
        using (var catalogueActivity = s_activitySource.StartActivity("读取并生成目录结构"))
        {
            catalogueActivity?.SetTag("warehouse.id", warehouse.Id);  // 设置仓库ID追踪标签
            
            // 尝试从数据库获取已优化的目录结构
            catalogue = warehouse.OptimizedDirectoryStructure;

            // 如果目录结构为空，则生成新的目录结构
            if (string.IsNullOrWhiteSpace(catalogue))
            {
                catalogueActivity?.SetTag("action", "generate_new_catalogue");  // 标记为生成新目录
                
                // 使用AI智能过滤生成优化的目录结构
                catalogue = await GetCatalogueSmartFilterOptimizedAsync(path, readme);
                
                // 如果成功生成目录结构，保存到数据库
                if (!string.IsNullOrWhiteSpace(catalogue))
                {
                    await dbContext.Warehouses.Where(x => x.Id == warehouse.Id)
                        .ExecuteUpdateAsync(x => x.SetProperty(y => y.OptimizedDirectoryStructure, catalogue));
                }
            }
            else
            {
                catalogueActivity?.SetTag("action", "use_existing_catalogue");  // 标记为使用现有目录
            }

            catalogueActivity?.SetTag("catalogue.length", catalogue?.Length ?? 0);  // 记录目录结构长度
        }

        // 步骤3: 读取或生成项目类别
        ClassifyType? classify;
        using (var classifyActivity = s_activitySource.StartActivity("读取或生成项目类别"))
        {
            classifyActivity?.SetTag("warehouse.id", warehouse.Id);  // 设置仓库ID追踪标签
            
            // 如果数据库中没有项目分类，则使用AI进行分类分析
            classify = warehouse.Classify ?? await WarehouseClassify.ClassifyAsync(fileKernel, catalogue, readme);
            
            classifyActivity?.SetTag("classify", classify?.ToString());  // 记录分类结果
        }

        // 将项目分类结果保存到数据库
        await dbContext.Warehouses.Where(x => x.Id == warehouse.Id)
            .ExecuteUpdateAsync(x => x.SetProperty(y => y.Classify, classify));

        // 步骤4: 生成知识图谱
        using (var miniMapActivity = s_activitySource.StartActivity("生成知识图谱"))
        {
            miniMapActivity?.SetTag("warehouse.id", warehouse.Id);  // 设置仓库ID追踪标签
            miniMapActivity?.SetTag("path", path);  // 设置路径追踪标签
            
            // 调用AI生成知识图谱
            var miniMap = await MiniMapService.GenerateMiniMap(catalogue, warehouse, path);
            
            // 删除旧的知识图谱数据
            await dbContext.MiniMaps.Where(x => x.WarehouseId == warehouse.Id)
                .ExecuteDeleteAsync();
            
            // 保存新的知识图谱到数据库
            await dbContext.MiniMaps.AddAsync(new MiniMap()
            {
                Id = Guid.NewGuid().ToString("N"),  // 生成唯一ID
                WarehouseId = warehouse.Id,  // 关联仓库ID
                Value = JsonSerializer.Serialize(miniMap, JsonSerializerOptions.Web)  // 序列化知识图谱内容
            });
            
            miniMapActivity?.SetTag("minimap.generated", true);  // 标记知识图谱已生成
        }

        // 步骤5: 生成项目概述
        string overview;
        using (var overviewActivity = s_activitySource.StartActivity("生成项目概述"))
        {
            overviewActivity?.SetTag("warehouse.id", warehouse.Id);  // 设置仓库ID追踪标签
            overviewActivity?.SetTag("git.repository", gitRepository);  // 设置Git仓库地址追踪标签
            overviewActivity?.SetTag("branch", warehouse.Branch);  // 设置分支追踪标签
            
            // 调用AI生成项目概述
            overview = await OverviewService.GenerateProjectOverview(fileKernel, catalogue, gitRepository,
                warehouse.Branch, readme, classify);

            // 清理项目分析标签内容（某些模型会生成不需要的标签）
            var project_analysis = new Regex(@"<project_analysis>(.*?)</project_analysis>",
                RegexOptions.Singleline);
            var project_analysis_match = project_analysis.Match(overview);
            if (project_analysis_match.Success)
            {
                // 删除项目分析标签及其内容
                overview = overview.Replace(project_analysis_match.Value, "");
            }

            // 提取blog标签中的内容（某些模型会包装在blog标签中）
            var overviewmatch = new Regex(@"<blog>(.*?)</blog>",
                RegexOptions.Singleline).Match(overview);

            if (overviewmatch.Success)
            {
                // 提取blog标签内的内容
                overview = overviewmatch.Groups[1].Value;
            }

            // 删除旧的概述数据
            await dbContext.DocumentOverviews.Where(x => x.DocumentId == document.Id)
                .ExecuteDeleteAsync();

            // 保存新的项目概述到数据库
            await dbContext.DocumentOverviews.AddAsync(new DocumentOverview()
            {
                Content = overview,  // 概述内容
                Title = "",  // 标题（暂时为空）
                DocumentId = document.Id,  // 关联文档ID
                Id = Guid.NewGuid().ToString("N")  // 生成唯一ID
            });

            overviewActivity?.SetTag("overview.length", overview?.Length ?? 0);  // 记录概述长度
        }

        // 步骤6: 生成目录结构
        List<DocumentCatalog> documentCatalogs = [];
        using (var catalogueStructureActivity = s_activitySource.StartActivity("生成目录结构"))
        {
            catalogueStructureActivity?.SetTag("warehouse.id", warehouse.Id);  // 设置仓库ID追踪标签
            
            // 调用AI生成文档目录结构
            var result = await GenerateThinkCatalogueService.GenerateCatalogue(path, gitRepository, catalogue,
                warehouse,
                classify);

            // 递归处理目录层次结构，将AI生成的目录转换为数据库实体
            DocumentsHelper.ProcessCatalogueItems(result.items, null, warehouse, document, documentCatalogs);

            // 设置每个目录项的初始状态
            documentCatalogs.ForEach(x =>
            {
                x.IsCompleted = false;  // 标记为未完成
                if (string.IsNullOrWhiteSpace(x.Prompt))
                {
                    x.Prompt = " ";  // 确保提示不为空
                }
            });

            // 删除遗留的目录数据
            await dbContext.DocumentCatalogs.Where(x => x.WarehouseId == warehouse.Id)
                .ExecuteDeleteAsync();

            // 将解析的目录结构保存到数据库
            await dbContext.DocumentCatalogs.AddRangeAsync(documentCatalogs);

            // 保存数据库更改
            await dbContext.SaveChangesAsync();
            
            catalogueStructureActivity?.SetTag("documents.count", documentCatalogs.Count);  // 记录文档数量
        }

        // 步骤7: 生成目录结构中的文档内容
        using (var documentsGenerationActivity = s_activitySource.StartActivity("生成目录结构中的文档"))
        {
            documentsGenerationActivity?.SetTag("warehouse.id", warehouse.Id);  // 设置仓库ID追踪标签
            documentsGenerationActivity?.SetTag("documents.count", documentCatalogs.Count);  // 设置文档数量追踪标签
            
            // 调用文档待处理服务，为每个目录项生成具体的文档内容
            await DocumentPendingService.HandlePendingDocumentsAsync(documentCatalogs, fileKernel, catalogue,
                gitRepository,
                warehouse, path, dbContext, warehouse.Classify);
        }

        // 步骤8: 生成更新日志 (仅Git仓库)
        if (warehouse.Type.Equals("git", StringComparison.CurrentCultureIgnoreCase))
        {
            using var updateLogActivity = s_activitySource.StartActivity("生成更新日志");
            updateLogActivity?.SetTag("warehouse.id", warehouse.Id);  // 设置仓库ID追踪标签
            updateLogActivity?.SetTag("warehouse.type", "git");  // 设置仓库类型追踪标签
            updateLogActivity?.SetTag("git.address", warehouse.Address);  // 设置Git地址追踪标签
            updateLogActivity?.SetTag("git.branch", warehouse.Branch);  // 设置分支追踪标签

            // 删除旧的提交记录
            await dbContext.DocumentCommitRecords.Where(x => x.WarehouseId == warehouse.Id)
                .ExecuteDeleteAsync();

            // 开始生成更新日志
            var committer = await GenerateUpdateLogAsync(document.GitPath, readme,
                warehouse.Address,
                warehouse.Branch,
                kernel);

            // 将提交记录转换为数据库实体
            var record = committer.Select(x => new DocumentCommitRecord()
            {
                WarehouseId = warehouse.Id,  // 关联仓库ID
                CreatedAt = DateTime.Now,  // 创建时间
                Author = string.Empty,  // 作者（暂时为空）
                Id = Guid.NewGuid().ToString("N"),  // 生成唯一ID
                CommitMessage = x.description,  // 提交消息
                Title = x.title,  // 标题
                LastUpdate = x.date,  // 最后更新时间
            });

            // 如果重新生成则需要清空之前记录
            await dbContext.DocumentCommitRecords.Where(x => x.WarehouseId == warehouse.Id)
                .ExecuteDeleteAsync();

            // 保存新的提交记录到数据库
            await dbContext.DocumentCommitRecords.AddRangeAsync(record);
            
            updateLogActivity?.SetTag("commit_records.count", record.Count());  // 记录提交记录数量
        }

        // 标记整个处理流程已完成
        activity?.SetTag("processing.completed", true);
    }

    /// <summary>
    /// 获取智能过滤的优化树形目录结构
    /// </summary>
    /// <param name="path">扫描路径</param>
    /// <param name="readme">README内容</param>
    /// <param name="format">输出格式</param>
    /// <returns>优化后的目录结构</returns>
    public static async Task<string> GetCatalogueSmartFilterOptimizedAsync(string path, string readme,
        string format = "compact")
    {
        using var activity = s_activitySource.StartActivity("智能过滤优化目录结构", ActivityKind.Server);
        activity?.SetTag("path", path);
        activity?.SetTag("format", format);

        var ignoreFiles = DocumentsHelper.GetIgnoreFiles(path);
        var pathInfos = new List<PathInfo>();

        // 递归扫描目录所有文件和目录
        DocumentsHelper.ScanDirectory(path, pathInfos, ignoreFiles);
        activity?.SetTag("total_files", pathInfos.Count);

        // 如果文件数量较少，直接返回优化结构
        if (pathInfos.Count < 800)
        {
            activity?.SetTag("processing_type", "direct_build");
            var fileTree = FileTreeBuilder.BuildTree(pathInfos, path);
            return format.ToLower() switch
            {
                "json" => FileTreeBuilder.ToCompactJson(fileTree),
                "pathlist" => string.Join("\n", FileTreeBuilder.ToPathList(fileTree)),
                "compact" or _ => FileTreeBuilder.ToCompactString(fileTree)
            };
        }

        // 如果不启用智能过滤，返回优化结构
        if (DocumentOptions.EnableSmartFilter == false)
        {
            activity?.SetTag("processing_type", "smart_filter_disabled");
            var fileTree = FileTreeBuilder.BuildTree(pathInfos, path);
            return format.ToLower() switch
            {
                "json" => FileTreeBuilder.ToCompactJson(fileTree),
                "pathlist" => string.Join("\n", FileTreeBuilder.ToPathList(fileTree)),
                "compact" or _ => FileTreeBuilder.ToCompactString(fileTree)
            };
        }

        activity?.SetTag("processing_type", "ai_smart_filter");
        Log.Logger.Information($"开始优化目录结构（使用{DocumentOptions.CatalogueFormat}格式）");

        var analysisModel = KernelFactory.GetKernel(OpenAIOptions.Endpoint,
            OpenAIOptions.ChatApiKey, path, OpenAIOptions.AnalysisModel);

        var codeDirSimplifier = analysisModel.Plugins["CodeAnalysis"]["CodeDirSimplifier"];

        // 使用优化的目录结构作为输入
        var optimizedInput = DocumentsHelper.GetCatalogueOptimized(path, DocumentOptions.CatalogueFormat);
        activity?.SetTag("optimized_input.length", optimizedInput?.Length ?? 0);

        var sb = new StringBuilder();
        int retryCount = 0;
        const int maxRetries = 5;
        Exception? lastException = null;

        while (retryCount < maxRetries)
        {
            try
            {
                await foreach (var item in analysisModel.InvokeStreamingAsync(codeDirSimplifier, new KernelArguments(
                                   new OpenAIPromptExecutionSettings()
                                   {
                                       MaxTokens = DocumentsHelper.GetMaxTokens(OpenAIOptions.AnalysisModel)
                                   })
                               {
                                   ["code_files"] = optimizedInput,
                                   ["readme"] = readme
                               }))
                {
                    sb.Append(item);
                }

                // 成功则跳出循环
                lastException = null;
                break;
            }
            catch (Exception ex)
            {
                retryCount++;
                lastException = ex;
                Log.Logger.Error(ex, $"优化目录结构失败，重试第{retryCount}次");
                activity?.SetTag($"retry.{retryCount}.error", ex.Message);
                if (retryCount >= maxRetries)
                {
                    activity?.SetTag("failed_after_retries", true);
                    throw new Exception($"优化目录结构失败，已重试{maxRetries}次", ex);
                }

                await Task.Delay(5000 * retryCount);
                sb.Clear();
            }
        }

        activity?.SetTag("retry_count", retryCount);
        activity?.SetTag("raw_result.length", sb.Length);

        // 正则表达式提取response_file
        var regex = new Regex("<response_file>(.*?)</response_file>", RegexOptions.Singleline);
        var match = regex.Match(sb.ToString());
        if (match.Success)
        {
            activity?.SetTag("extraction_method", "response_file_tag");
            return match.Groups[1].Value;
        }

        // 可能是```json
        var jsonRegex = new Regex("```json(.*?)```", RegexOptions.Singleline);
        var jsonMatch = jsonRegex.Match(sb.ToString());
        if (jsonMatch.Success)
        {
            activity?.SetTag("extraction_method", "json_code_block");
            return jsonMatch.Groups[1].Value;
        }

        activity?.SetTag("extraction_method", "raw_content");
        return sb.ToString();
    }

    /// <summary>
    /// 获取智能过滤的目录结构（保持向后兼容的原始方法）
    /// </summary>
    /// <param name="path">扫描路径</param>
    /// <param name="readme">README内容</param>
    /// <returns>目录结构字符串</returns>
    public static async Task<string> GetCatalogueSmartFilterAsync(string path, string readme)
    {
        var ignoreFiles = DocumentsHelper.GetIgnoreFiles(path);

        var pathInfos = new List<PathInfo>();
        // 递归扫描目录所有文件和目录
        DocumentsHelper.ScanDirectory(path, pathInfos, ignoreFiles);
        var catalogue = new StringBuilder();

        foreach (var info in pathInfos)
        {
            // 删除前缀 Constant.GitPath
            var relativePath = info.Path.Replace(path, "").TrimStart('\\');

            // 过滤.开头的文件
            if (relativePath.StartsWith("."))
                continue;

            catalogue.Append($"{relativePath}\n");
        }

        // 如果文件数量小于800
        if (pathInfos.Count < 800)
        {
            // 直接返回
            return catalogue.ToString();
        }

        // 如果不启用则直接返回
        if (DocumentOptions.EnableSmartFilter == false)
        {
            return catalogue.ToString();
        }

        Log.Logger.Information("开始优化目录结构");

        var analysisModel = KernelFactory.GetKernel(OpenAIOptions.Endpoint,
            OpenAIOptions.ChatApiKey, path, OpenAIOptions.AnalysisModel);

        var codeDirSimplifier = analysisModel.Plugins["CodeAnalysis"]["CodeDirSimplifier"];

        var sb = new StringBuilder();
        int retryCount = 0;
        const int maxRetries = 5;
        Exception? lastException = null;

        while (retryCount < maxRetries)
        {
            try
            {
                await foreach (var item in analysisModel.InvokeStreamingAsync(codeDirSimplifier, new KernelArguments(
                                   new OpenAIPromptExecutionSettings()
                                   {
                                       MaxTokens = DocumentsHelper.GetMaxTokens(OpenAIOptions.AnalysisModel)
                                   })
                               {
                                   ["code_files"] = catalogue.ToString(),
                                   ["readme"] = readme
                               }))
                {
                    sb.Append(item);
                }

                // 成功则跳出循环
                lastException = null;
                break;
            }
            catch (Exception ex)
            {
                retryCount++;
                lastException = ex;
                Log.Logger.Error(ex, $"优化目录结构失败，重试第{retryCount}次");
                if (retryCount >= maxRetries)
                {
                    throw new Exception($"优化目录结构失败，已重试{maxRetries}次", ex);
                }

                await Task.Delay(5000 * retryCount);
                sb.Clear();
            }
        }

        // 正则表达式提取response_file
        var regex = new Regex("<response_file>(.*?)</response_file>", RegexOptions.Singleline);
        var match = regex.Match(sb.ToString());
        if (match.Success)
        {
            // 提取到的内容
            var extractedContent = match.Groups[1].Value;
            catalogue.Clear();
            catalogue.Append(extractedContent);
        }
        else
        {
            // 可能是```json
            var jsonRegex = new Regex("```json(.*?)```", RegexOptions.Singleline);
            var jsonMatch = jsonRegex.Match(sb.ToString());
            if (jsonMatch.Success)
            {
                // 提取到的内容
                var extractedContent = jsonMatch.Groups[1].Value;
                catalogue.Clear();
                catalogue.Append(extractedContent);
            }
            else
            {
                catalogue.Clear();
                catalogue.Append(sb);
            }
        }

        return catalogue.ToString();
    }

    /// <summary>
    /// 生成或读取仓库的README文档
    /// 该函数负责处理README文档的生成逻辑，包括检查现有README、生成新README、保存到数据库等操作
    /// </summary>
    /// <param name="warehouse">仓库实体对象，包含仓库的基本信息和配置</param>
    /// <param name="path">本地仓库的完整路径，用于文件系统操作</param>
    /// <param name="koalaWikiContext">数据库上下文，用于保存生成的README到数据库</param>
    /// <returns>生成的README文档内容字符串</returns>
    public static async Task<string> GenerateReadMe(Warehouse warehouse, string path,
        IKoalaWikiContext koalaWikiContext)
    {
        // ===== 分布式追踪初始化 =====
        // 创建分布式追踪活动，用于监控README生成过程的性能和行为
        using var activity = s_activitySource.StartActivity("生成README文档", ActivityKind.Server);
        activity?.SetTag("warehouse.id", warehouse.Id);  // 设置仓库ID追踪标签
        activity?.SetTag("warehouse.name", warehouse.Name);  // 设置仓库名称追踪标签
        activity?.SetTag("path", path);  // 设置本地路径追踪标签

        // ===== 步骤1：检查现有README文件 =====
        // 尝试从本地文件系统读取现有的README文件（支持多种格式）
        var readme = await DocumentsHelper.ReadMeFile(path);
        activity?.SetTag("existing_readme_found", !string.IsNullOrEmpty(readme));  // 记录是否找到现有README
        activity?.SetTag("warehouse_readme_exists", !string.IsNullOrEmpty(warehouse.Readme));  // 记录数据库中是否已有README

        // ===== 步骤2：判断是否需要生成新README =====
        // 如果本地文件系统和数据库中都没有README，则需要生成新的README
        if (string.IsNullOrEmpty(readme) && string.IsNullOrEmpty(warehouse.Readme))
        {
            activity?.SetTag("action", "generate_new_readme");  // 标记为生成新README

            // ===== 步骤2.1：获取项目目录结构 =====
            // 获取项目的完整目录结构，用于AI分析项目结构
            var catalogue = DocumentsHelper.GetCatalogue(path);
            activity?.SetTag("catalogue.length", catalogue?.Length ?? 0);  // 记录目录结构长度

            // ===== 步骤2.2：创建AI内核实例 =====
            // 创建用于代码分析的AI内核实例（启用代码分析功能）
            var kernel = KernelFactory.GetKernel(OpenAIOptions.Endpoint,
                OpenAIOptions.ChatApiKey,
                path, OpenAIOptions.ChatModel);

            // 创建用于文件操作的AI内核实例（禁用某些功能以提高性能）
            var fileKernel = KernelFactory.GetKernel(OpenAIOptions.Endpoint,
                OpenAIOptions.ChatApiKey, path, OpenAIOptions.ChatModel, false);

            // ===== 步骤2.3：调用AI生成README =====
            // 获取README生成插件，该插件包含AI生成README的Prompt模板
            var generateReadmePlugin = kernel.Plugins["CodeAnalysis"]["GenerateReadme"];
            
            // 调用AI模型生成README，传入目录结构、Git仓库地址、分支等参数
            // ToolCallBehavior.AutoInvokeKernelFunctions 表示自动调用内核函数（如文件读取）
            var generateReadme = await fileKernel.InvokeAsync(generateReadmePlugin, new KernelArguments(
                new OpenAIPromptExecutionSettings()
                {
                    ToolCallBehavior = ToolCallBehavior.AutoInvokeKernelFunctions,  // 自动调用文件读取等函数
                })
            {
                ["catalogue"] = catalogue,  // 输入：项目目录结构
                ["git_repository"] = warehouse.Address.Replace(".git", ""),  // 输入：Git仓库地址（移除.git后缀）
                ["branch"] = warehouse.Branch  // 输入：仓库分支
            });

            // ===== 步骤2.4：提取AI生成的README内容 =====
            // 将AI返回的结果转换为字符串
            readme = generateReadme.ToString();
            activity?.SetTag("generated_readme.length", readme?.Length ?? 0);  // 记录生成的README长度

            // ===== 步骤2.5：处理AI输出格式 =====
            // 某些AI模型可能将README内容包装在<readme>标签中，需要提取实际内容
            // 正则表达式匹配<readme>标签内的内容
            var readmeRegex = new Regex(@"<readme>(.*?)</readme>", RegexOptions.Singleline);
            var readmeMatch = readmeRegex.Match(readme);

            if (readmeMatch.Success)
            {
                // 如果找到<readme>标签，提取标签内的内容
                var extractedContent = readmeMatch.Groups[1].Value;
                readme = extractedContent;
                activity?.SetTag("extraction_method", "readme_tag");  // 标记使用标签提取方法
            }
            else
            {
                // 如果没有找到<readme>标签，直接使用原始内容
                activity?.SetTag("extraction_method", "raw_content");  // 标记使用原始内容
            }

            // ===== 步骤2.6：保存生成的README到数据库 =====
            // 将生成的README内容保存到Warehouse表的Readme字段
            await koalaWikiContext.Warehouses.Where(x => x.Id == warehouse.Id)
                .ExecuteUpdateAsync(x => x.SetProperty(y => y.Readme, readme));
        }
        else
        {
            // ===== 步骤3：使用现有README =====
            // 如果本地文件系统或数据库中已有README，直接使用现有内容
            activity?.SetTag("action", "use_existing_readme");  // 标记为使用现有README
            
            // 将现有的README内容保存到数据库（确保数据一致性）
            await koalaWikiContext.Warehouses.Where(x => x.Id == warehouse.Id)
                .ExecuteUpdateAsync(x => x.SetProperty(y => y.Readme, readme));
        }

        // ===== 步骤4：兜底处理 =====
        // 如果所有方法都没有获取到README内容，使用数据库中存储的README作为兜底
        if (string.IsNullOrEmpty(readme))
        {
            activity?.SetTag("fallback_to_warehouse_readme", true);  // 标记使用兜底README
            return warehouse.Readme;  // 返回数据库中存储的README
        }

        // ===== 步骤5：返回最终结果 =====
        // 记录最终README的长度并返回
        activity?.SetTag("final_readme.length", readme?.Length ?? 0);  // 记录最终README长度
        return readme;  // 返回生成的或现有的README内容
    }
}