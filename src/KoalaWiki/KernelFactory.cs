using System.ClientModel;
using System.Collections.Concurrent;
using System.Diagnostics;
using KoalaWiki.Functions;
using KoalaWiki.Options;
using KoalaWiki.plugins;
using Microsoft.SemanticKernel;
using OpenAI;
using Serilog;

#pragma warning disable SKEXP0070

#pragma warning disable SKEXP0010

namespace KoalaWiki;

/// <summary>
/// 提供一个静态方法来创建和配置一个内核实例，用于各种基于ai的操作。
/// KernelFactory类负责设置必要的服务、插件和配置
/// 内核需要的，包括聊天完成服务，日志记录和文件处理功能。
/// 它支持多个AI模型提供者，并允许可选的代码分析功能。
/// </summary>
public static class KernelFactory
{
    /// <summary>
    /// 创建和配置AI内核实例
    /// 该方法负责构建一个完整的AI内核，包括配置AI模型、添加插件、设置服务等
    /// 内核是AI操作的核心组件，提供了与AI模型交互、调用插件函数的能力
    /// </summary>
    /// <param name="chatEndpoint">AI服务的端点URL，用于连接AI模型服务</param>
    /// <param name="apiKey">API密钥，用于认证AI服务访问</param>
    /// <param name="gitPath">Git仓库的本地路径，用于文件操作插件</param>
    /// <param name="model">AI模型名称，默认为"gpt-4.1"</param>
    /// <param name="isCodeAnalysis">是否启用代码分析功能，默认为true</param>
    /// <returns>配置完成的AI内核实例</returns>
    public static Kernel GetKernel(string chatEndpoint,
        string apiKey,
        string gitPath,
        string model = "gpt-4.1", bool isCodeAnalysis = true)
    {
        // ===== 分布式追踪初始化 =====
        // 创建分布式追踪活动，用于监控内核创建过程的性能和行为
        using var activity = Activity.Current?.Source.StartActivity();
        activity?.SetTag("model", model);  // 设置AI模型名称追踪标签
        activity?.SetTag("provider", OpenAIOptions.ModelProvider);  // 设置模型提供者追踪标签
        activity?.SetTag("code_analysis_enabled", isCodeAnalysis);  // 设置代码分析启用状态追踪标签
        activity?.SetTag("git_path", gitPath);  // 设置Git路径追踪标签

        // ===== 步骤1：创建内核构建器 =====
        // 创建内核构建器，用于配置和构建AI内核实例
        var kernelBuilder = Kernel.CreateBuilder();

        // ===== 步骤2：配置日志服务 =====
        // 添加Serilog日志服务，用于内核内部的日志记录
        kernelBuilder.Services.AddSerilog(Log.Logger);

        // ===== 步骤3：配置提示词渲染过滤器 =====
        // 添加语言提示词过滤器，用于处理多语言提示词的渲染
        kernelBuilder.Services.AddSingleton<IPromptRenderFilter, LanguagePromptFilter>();

        // ===== 步骤4：配置AI模型服务 =====
        // 根据配置的模型提供者，添加相应的AI聊天完成服务
        if (OpenAIOptions.ModelProvider.Equals("OpenAI", StringComparison.OrdinalIgnoreCase))
        {
            // 配置OpenAI服务
            // 创建自定义HTTP客户端，包含重试机制和连接池配置
            kernelBuilder.AddOpenAIChatCompletion(model, new Uri(chatEndpoint), apiKey,
                httpClient: new HttpClient(new KoalaHttpClientHandler()
                {
                    // 配置HTTP客户端重试机制
                    AllowAutoRedirect = true,  // 允许自动重定向
                    MaxAutomaticRedirections = 5,  // 最大自动重定向次数
                    MaxConnectionsPerServer = 200,  // 每个服务器的最大连接数
                })
                {
                    // 设置HTTP客户端超时时间（16秒）
                    Timeout = TimeSpan.FromSeconds(16000),
                });
        }
        else if (OpenAIOptions.ModelProvider.Equals("AzureOpenAI", StringComparison.OrdinalIgnoreCase))
        {
            // 配置Azure OpenAI服务
            // 使用与OpenAI相同的HTTP客户端配置，确保一致的网络行为
            kernelBuilder.AddAzureOpenAIChatCompletion(model, chatEndpoint, apiKey, httpClient: new HttpClient(
                new KoalaHttpClientHandler()
                {
                    // 配置HTTP客户端重试机制
                    AllowAutoRedirect = true,  // 允许自动重定向
                    MaxAutomaticRedirections = 5,  // 最大自动重定向次数
                    MaxConnectionsPerServer = 200,  // 每个服务器的最大连接数
                })
            {
                // 设置HTTP客户端超时时间（16秒）
                Timeout = TimeSpan.FromSeconds(16000),
            });
        }
        else if (OpenAIOptions.ModelProvider.Equals("Anthropic", StringComparison.OrdinalIgnoreCase))
        {
            // 配置Anthropic服务
            // 使用与OpenAI相同的HTTP客户端配置，确保一致的网络行为
            kernelBuilder.AddAnthropicChatCompletion(model, apiKey, httpClient: new HttpClient(
                new KoalaHttpClientHandler()
                {
                    // 配置HTTP客户端重试机制
                    AllowAutoRedirect = true,  // 允许自动重定向
                    MaxAutomaticRedirections = 5,  // 最大自动重定向次数
                    MaxConnectionsPerServer = 200,  // 每个服务器的最大连接数
                })
            {
                // 设置HTTP客户端超时时间（16秒）
                Timeout = TimeSpan.FromSeconds(16000),
            });
        }
        else
        {
            // ===== 错误处理：不支持的模型提供者 =====
            // 如果配置了不支持的模型提供者，记录错误并抛出异常
            activity?.SetStatus(ActivityStatusCode.Error, "不支持的模型提供者");
            throw new Exception("暂不支持：" + OpenAIOptions.ModelProvider + "，请使用OpenAI、AzureOpenAI或Anthropic");
        }

        // ===== 步骤5：配置代码分析插件 =====
        // 如果启用了代码分析功能，添加代码分析插件
        if (isCodeAnalysis)
        {
            // 从plugins/CodeAnalysis目录加载代码分析插件
            // 这些插件包含AI代码分析、README生成、目录结构分析等功能
            kernelBuilder.Plugins.AddFromPromptDirectory(Path.Combine(AppContext.BaseDirectory, "plugins",
                "CodeAnalysis"));
            activity?.SetTag("plugins.code_analysis", "loaded");  // 记录代码分析插件加载状态
        }

        // ===== 步骤6：配置文件操作插件 =====
        // 添加文件操作函数插件，提供文件读取、文件信息获取等功能
        // FileFunction是AI内核与文件系统交互的核心组件
        var fileFunction = new FileFunction(gitPath);
        kernelBuilder.Plugins.AddFromObject(fileFunction);
        activity?.SetTag("plugins.file_function", "loaded");  // 记录文件函数插件加载状态

        // ===== 步骤7：配置代码依赖分析插件 =====
        // 如果启用了代码依赖分析功能，添加代码依赖分析插件
        if (DocumentOptions.EnableCodeDependencyAnalysis)
        {
            // 添加代码依赖分析函数，提供函数依赖树、文件依赖树分析功能
            var codeAnalyzeFunction = new CodeAnalyzeFunction(gitPath);
            kernelBuilder.Plugins.AddFromObject(codeAnalyzeFunction);
            activity?.SetTag("plugins.code_analyze_function", "loaded");  // 记录代码分析函数加载状态
        }

        // ===== 步骤8：构建内核实例 =====
        // 使用配置好的构建器创建内核实例
        var kernel = kernelBuilder.Build();
        
        // ===== 步骤9：添加函数调用拦截器 =====
        // 添加函数结果拦截器，用于监控和记录函数调用的结果
        kernel.FunctionInvocationFilters.Add(new FunctionResultInterceptor());

        // ===== 步骤10：完成追踪并返回 =====
        // 标记分布式追踪活动为成功状态
        activity?.SetStatus(ActivityStatusCode.Ok);
        activity?.SetTag("kernel.created", true);  // 记录内核创建成功

        // 返回配置完成的AI内核实例
        return kernel;
    }
}