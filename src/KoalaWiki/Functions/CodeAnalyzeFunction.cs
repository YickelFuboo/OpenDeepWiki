using System.ComponentModel;
using System.Text.Json;
using Microsoft.SemanticKernel;

namespace KoalaWiki.Functions;

/// <summary>
/// 代码依赖分析函数类
/// 该类提供代码依赖关系分析功能，集成到AI内核中供AI模型调用
/// 支持分析函数级和文件级的依赖关系，帮助理解代码结构和调用关系
/// </summary>
/// <param name="gitPath">Git仓库的本地路径，用于定位和分析代码文件</param>
public class CodeAnalyzeFunction(string gitPath)
{
    /// <summary>
    /// 分析指定文件中特定函数的依赖关系树
    /// 该方法会分析指定函数的所有调用关系，构建完整的依赖树结构
    /// 包括该函数调用的其他函数、被其他函数调用的情况等
    /// </summary>
    /// <param name="filePath">包含要分析函数的文件路径（相对于仓库根目录）</param>
    /// <param name="functionName">要分析依赖关系的函数名称</param>
    /// <returns>表示指定函数依赖树的JSON字符串，包含完整的调用关系结构</returns>
    [KernelFunction, Description("Analyze the dependency relationship of the specified method")]
    [return: Description("Return the dependency tree of the specified function")]
    public async Task<string> AnalyzeFunctionDependencyTree(
        [Description("File Path")] string filePath,
        [Description("Analyze the dependency relationship of the specified method")]
        string functionName)
    {
        try
        {
            // ===== 步骤1：记录分析请求 =====
            // 记录开始分析函数依赖关系的日志信息，包含文件路径和函数名
            Log.Logger.Information($"ReadCodeFileAsync: {filePath} {functionName}");

            // ===== 步骤2：构建完整文件路径 =====
            // 将相对路径转换为绝对路径，确保能正确访问文件
            // TrimStart('/') 移除路径开头的斜杠，避免路径拼接问题
            var newPath = Path.Combine(gitPath, filePath.TrimStart('/'));

            // ===== 步骤3：创建依赖分析器实例 =====
            // 创建DependencyAnalyzer实例，该分析器负责实际的代码依赖分析工作
            // 传入gitPath参数，让分析器知道代码仓库的根目录位置
            var code = new DependencyAnalyzer(gitPath);

            // ===== 步骤4：执行函数依赖分析 =====
            // 调用依赖分析器的AnalyzeFunctionDependencyTree方法
            // 传入完整文件路径和函数名，获取函数的依赖关系树
            var result = await code.AnalyzeFunctionDependencyTree(newPath, functionName);

            // ===== 步骤5：序列化并返回结果 =====
            // 将分析结果序列化为JSON格式，使用Web兼容的序列化选项
            // JsonSerializerOptions.Web 确保输出的JSON格式适合Web传输
            return JsonSerializer.Serialize(result, JsonSerializerOptions.Web);
        }
        catch (Exception ex)
        {
            // ===== 异常处理 =====
            // 捕获并处理分析过程中可能出现的异常
            // 记录错误信息到控制台，便于调试和问题排查
            Console.WriteLine($"Error reading file: {ex.Message}");
            
            // 返回错误信息字符串，让调用方知道分析失败的原因
            return $"Error reading file: {ex.Message}";
        }
    }

    /// <summary>
    /// 分析指定文件的整体依赖关系
    /// 该方法会分析整个文件的依赖结构，包括文件中的所有函数、导入关系等
    /// 提供文件级别的依赖关系视图，帮助理解文件的整体结构
    /// </summary>
    /// <param name="filePath">要分析依赖关系的文件路径（相对于仓库根目录）</param>
    /// <returns>表示指定文件依赖树的JSON字符串，包含文件的完整依赖结构</returns>
    [KernelFunction, Description("Analyze the dependency relationship of the specified file")]
    [return: Description("Return the dependency tree of the specified file")]
    public async Task<string> AnalyzeFileDependencyTree(
        [Description("File Path")] string filePath)
    {
        try
        {
            // ===== 步骤1：记录分析请求 =====
            // 记录开始分析文件依赖关系的日志信息，包含文件路径
            Log.Logger.Information($"ReadCodeFileAsync: {filePath}");

            // ===== 步骤2：构建完整文件路径 =====
            // 将相对路径转换为绝对路径，确保能正确访问文件
            // TrimStart('/') 移除路径开头的斜杠，避免路径拼接问题
            var newPath = Path.Combine(gitPath, filePath.TrimStart('/'));

            // ===== 步骤3：创建依赖分析器实例 =====
            // 创建DependencyAnalyzer实例，该分析器负责实际的代码依赖分析工作
            // 传入gitPath参数，让分析器知道代码仓库的根目录位置
            var code = new DependencyAnalyzer(gitPath);

            // ===== 步骤4：执行文件依赖分析 =====
            // 调用依赖分析器的AnalyzeFileDependencyTree方法
            // 传入完整文件路径，获取文件的整体依赖关系树
            var result = await code.AnalyzeFileDependencyTree(newPath);

            // ===== 步骤5：序列化并返回结果 =====
            // 将分析结果序列化为JSON格式，使用Web兼容的序列化选项
            // JsonSerializerOptions.Web 确保输出的JSON格式适合Web传输
            return JsonSerializer.Serialize(result, JsonSerializerOptions.Web);
        }
        catch (Exception ex)
        {
            // ===== 异常处理 =====
            // 捕获并处理分析过程中可能出现的异常
            // 记录错误信息到控制台，便于调试和问题排查
            Console.WriteLine($"Error reading file: {ex.Message}");
            
            // 返回错误信息字符串，让调用方知道分析失败的原因
            return $"Error reading file: {ex.Message}";
        }
    }
}