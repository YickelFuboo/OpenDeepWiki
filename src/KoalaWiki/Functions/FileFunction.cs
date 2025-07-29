using System.ComponentModel;
using System.Text;
using System.Text.Encodings.Web;
using System.Text.Json;
using Microsoft.SemanticKernel;
using OpenDeepWiki.CodeFoundation;
using OpenDeepWiki.CodeFoundation.Utils;

namespace KoalaWiki.Functions;

/// <summary>
/// 文件操作函数类
/// 该类提供AI内核与本地文件系统交互的功能，包括文件读取、文件信息获取、目录结构扫描等
/// 主要用于AI模型访问和分析代码仓库中的文件内容
/// </summary>
/// <param name="gitPath">Git仓库的本地路径，用于定位和访问仓库中的文件</param>
public class FileFunction(string gitPath)
{
    /// <summary>
    /// 代码压缩服务实例
    /// 用于对代码文件进行压缩处理，减少文件大小并保留关键信息
    /// </summary>
    private readonly CodeCompressionService _codeCompressionService = new();

    /// <summary>
    /// 获取当前仓库的压缩目录结构
    /// 该方法扫描整个仓库目录，构建文件树结构，并返回压缩后的字符串表示
    /// 主要用于AI模型了解项目的整体文件结构
    /// </summary>
    /// <returns>压缩后的目录结构字符串，包含所有文件和目录的层级关系</returns>
    public string GetTree()
    {
        // ===== 步骤1：获取忽略文件列表 =====
        // 获取.gitignore等文件中定义的忽略规则，避免扫描不必要的文件
        var ignoreFiles = DocumentsHelper.GetIgnoreFiles(gitPath);
        var pathInfos = new List<PathInfo>();

        // ===== 步骤2：递归扫描目录 =====
        // 递归扫描仓库根目录下的所有文件和目录，构建路径信息列表
        DocumentsHelper.ScanDirectory(gitPath, pathInfos, ignoreFiles);

        // ===== 步骤3：构建文件树 =====
        // 将路径信息列表转换为树形结构
        var fileTree = FileTreeBuilder.BuildTree(pathInfos, gitPath);
        
        // ===== 步骤4：转换为压缩字符串 =====
        // 将文件树转换为紧凑的字符串格式，便于AI模型处理
        return FileTreeBuilder.ToCompactString(fileTree);
    }

    /// <summary>
    /// 获取文件基本信息
    /// 该方法用于批量获取多个文件的基本信息，包括文件名、大小、扩展名、行数等
    /// 建议在读取文件内容之前先调用此方法获取文件信息，以提高效率
    /// </summary>
    /// <param name="filePath">要获取信息的文件路径数组，支持批量处理以提高效率</param>
    /// <returns>JSON格式的文件信息，键为文件路径，值为包含文件详细信息的JSON对象</returns>
    [KernelFunction(name: "FileInfo"), Description(
         "Before accessing or reading any file content, always use this method to retrieve the basic information for all specified files. Batch as many file paths as possible into a single call to maximize efficiency. Provide file paths as an array. The function returns a JSON object where each key is the file path and each value contains the file's name, size, extension, creation time, last write time, and last access time. Ensure this information is obtained and reviewed before proceeding to any file content operations."
     )]
    [return:
        Description(
            "Return a JSON object with file paths as keys and file information as values. The information includes file name, size, extension, creation time, last write time, and last access time."
        )]
    public string GetFileInfoAsync(
        [Description("File Path")] string[] filePath)
    {
        try
        {
            // ===== 步骤1：初始化结果字典 =====
            // 创建用于存储文件信息的字典，键为文件路径，值为文件信息JSON字符串
            var dic = new Dictionary<string, string>();

            // ===== 步骤2：去重处理 =====
            // 移除重复的文件路径，避免重复处理同一文件
            filePath = filePath.Distinct().ToArray();

            // ===== 步骤3：记录文件访问 =====
            // 如果启用了文档上下文存储，将访问的文件路径添加到文档存储中
            if (DocumentContext.DocumentStore?.Files != null)
            {
                DocumentContext.DocumentStore.Files.AddRange(filePath);
            }

            // ===== 步骤4：批量处理文件信息 =====
            // 遍历所有文件路径，获取每个文件的基本信息
            foreach (var item in filePath)
            {
                // 构建完整的文件路径
                var fullPath = Path.Combine(gitPath, item.TrimStart('/'));
                
                // ===== 步骤4.1：检查文件是否存在 =====
                if (!File.Exists(fullPath))
                {
                    dic[item] = "File not found";
                    continue;
                }

                // ===== 步骤4.2：获取文件信息 =====
                Console.WriteLine($"Getting file info: {fullPath}");
                var info = new FileInfo(fullPath);

                // 获取文件信息并序列化为JSON格式
                dic[item] = JsonSerializer.Serialize(new
                {
                    info.Name,           // 文件名
                    info.Length,         // 文件大小（字节）
                    info.Extension,      // 文件扩展名
                    TotalLine = File.ReadAllLines(fullPath).Length,  // 文件总行数
                }, JsonSerializerOptions.Web);
            }

            // ===== 步骤5：返回结果 =====
            // 将所有文件信息序列化为JSON格式返回
            return JsonSerializer.Serialize(dic, JsonSerializerOptions.Web);
        }
        catch (Exception ex)
        {
            // ===== 异常处理 =====
            // 记录错误信息到控制台，便于调试和问题排查
            Console.WriteLine($"Error getting file info: {ex.Message}");
            return $"Error getting file info: {ex.Message}";
        }
    }

    /// <summary>
    /// 批量读取文件内容
    /// 该方法用于批量读取多个文件的内容，支持大文件处理（超过100KB的文件会提示使用行读取）
    /// 建议批量处理多个文件以提高效率，减少函数调用次数
    /// </summary>
    /// <param name="filePaths">要读取的文件路径数组，支持批量处理以提高效率</param>
    /// <returns>JSON格式的文件内容，键为文件路径，值为文件内容或提示信息</returns>
    /// <summary>
    /// 批量读取文件内容
    /// 该方法用于批量读取多个文件的内容，支持大文件处理（超过100KB的文件会提示使用行读取）
    /// 建议批量处理多个文件以提高效率，减少函数调用次数
    /// </summary>
    /// <param name="filePaths">要读取的文件路径数组，支持批量处理以提高效率</param>
    /// <returns>JSON格式的文件内容，键为文件路径，值为文件内容或提示信息</returns>
    public async Task<string> ReadFilesAsync(
        [Description("File Path array. Always batch multiple file paths to reduce the number of function calls.")]
        string[] filePaths)
    {
        try
        {
            // ===== 步骤1：去重处理 =====
            // 移除重复的文件路径，避免重复读取同一文件
            filePaths = filePaths.Distinct().ToArray();

            // ===== 步骤2：记录文件访问 =====
            // 如果启用了文档上下文存储，将访问的文件路径添加到文档存储中
            if (DocumentContext.DocumentStore?.Files != null)
            {
                DocumentContext.DocumentStore.Files.AddRange(filePaths);
            }

            // ===== 步骤3：批量读取文件内容 =====
            var dic = new Dictionary<string, string>();
            foreach (var filePath in filePaths)
            {
                // 构建完整的文件路径
                var item = Path.Combine(gitPath, filePath.TrimStart('/'));
                
                // ===== 步骤3.1：检查文件是否存在 =====
                if (!File.Exists(item))
                {
                    continue;
                }

                Console.WriteLine($"Reading file: {item}");

                var info = new FileInfo(item);

                // ===== 步骤3.2：大文件处理 =====
                // 如果文件大小超过100KB，提示使用行读取方法
                if (info.Length > 1024 * 100)
                {
                    dic[filePath] =
                        "If the file exceeds 100KB, you should use ReadFileFromLineAsync to read the file content line by line";
                }
                else
                {
                    // ===== 步骤3.3：读取文件内容 =====
                    // 读取整个文件内容
                    string content = await File.ReadAllTextAsync(item);

                    // ===== 步骤3.4：代码压缩处理 =====
                    // 如果启用代码压缩且是代码文件，则应用压缩算法
                    if (DocumentOptions.EnableCodeCompression && CodeFileDetector.IsCodeFile(filePath))
                    {
                        content = _codeCompressionService.CompressCode(content, filePath);
                    }

                    dic[filePath] = content;
                }
            }

            // ===== 步骤4：返回结果 =====
            // 将所有文件内容序列化为JSON格式返回，使用宽松的JSON转义
            return JsonSerializer.Serialize(dic, new JsonSerializerOptions()
            {
                Encoder = JavaScriptEncoder.UnsafeRelaxedJsonEscaping,
                WriteIndented = true,
            });
        }
        catch (Exception ex)
        {
            // ===== 异常处理 =====
            // 记录错误信息并抛出异常
            Console.WriteLine($"Error reading file: {ex.Message}");
            throw new Exception($"Error reading file: {ex.Message}");
        }
    }

    /// <summary>
    /// 读取单个文件内容
    /// 该方法用于读取单个文件的内容，支持大文件检测和代码压缩
    /// 适用于需要读取特定文件内容的场景
    /// </summary>
    /// <param name="filePath">要读取的文件路径（相对于仓库根目录）</param>
    /// <returns>文件内容字符串，如果文件过大或不存在则返回相应的提示信息</returns>
    public async Task<string> ReadFileAsync(
        [Description("File Path")] string filePath)
    {
        try
        {
            // ===== 步骤1：记录文件访问 =====
            // 如果启用了文档上下文存储，将访问的文件路径添加到文档存储中
            if (DocumentContext.DocumentStore?.Files != null)
            {
                DocumentContext.DocumentStore.Files.Add(filePath);
            }

            // ===== 步骤2：构建完整文件路径 =====
            // 将相对路径转换为绝对路径
            filePath = Path.Combine(gitPath, filePath.TrimStart('/'));
            Console.WriteLine($"Reading file: {filePath}");

            var info = new FileInfo(filePath);
            
            // ===== 步骤3：检查文件是否存在 =====
            if (!info.Exists)
            {
                return $"File not found: {filePath}";
            }

            // ===== 步骤4：大文件检测 =====
            // 如果文件大小超过100KB，返回提示信息
            if (info.Length > 1024 * 100)
            {
                return $"File too large: {filePath} ({info.Length / 1024 / 100}KB)";
            }

            // ===== 步骤5：读取文件内容 =====
            // 读取整个文件内容
            string content = await File.ReadAllTextAsync(filePath);

            // ===== 步骤6：代码压缩处理 =====
            // 如果启用代码压缩且是代码文件，则应用压缩算法
            if (DocumentOptions.EnableCodeCompression && CodeFileDetector.IsCodeFile(filePath))
            {
                content = _codeCompressionService.CompressCode(content, filePath);
            }

            return content;
        }
        catch (Exception ex)
        {
            // ===== 异常处理 =====
            // 记录错误信息到控制台，便于调试和问题排查
            Console.WriteLine($"Error reading file: {ex.Message}");
            return $"Error reading file: {ex.Message}";
        }
    }

    /// <summary>
    /// 文件读取输入类
    /// 用于批量读取文件时指定每个文件的读取参数
    /// </summary>
    public class ReadFileInput
    {
        /// <summary>
        /// 要读取的文件项数组
        /// 每个文件项包含文件路径和读取的起始、结束行号
        /// 文件必须存在且可读，如果路径无效或文件不存在会抛出异常
        /// </summary>
        [Description(
            "An array of file items to read. Each item contains the file path and the start and end line numbers for reading. The file must exist and be readable. If the path is invalid or the file does not exist, an exception will be thrown.")]
        public ReadFileItemInput[] Items { get; set; } = [];
    }

    /// <summary>
    /// 从指定行数开始读取文件内容
    /// 该方法支持按行读取文件内容，特别适用于大文件的处理
    /// 可以指定起始行号和读取行数，支持长文件的逐行读取
    /// </summary>
    /// <param name="items">要读取的文件项数组，每个项包含文件路径、起始行号和读取行数</param>
    /// <returns>JSON格式的读取结果，包含每个文件的指定行内容</returns>
    [KernelFunction(name: "File"),
     Description(
         "Reads a file from the local filesystem. You can access any file directly by using this tool.\nAssume this tool is able to read all files on the machine. If the User provides a path to a file assume that path is valid. It is okay to read a file that does not exist; an error will be returned.\n\nUsage:\n- The file_path parameter must be an absolute path, not a relative path\n- By default, it reads up to 2000 lines starting from the beginning of the file\n- You can optionally specify a line offset and limit (especially handy for long files), but it's recommended to read the whole file by not providing these parameters\n- Any lines longer than 2000 characters will be truncated\n- Results are returned using cat -n format, with line numbers starting at 1\n- This tool allows Claude Code to read images (eg PNG, JPG, etc). When reading an image file the contents are presented visually as Claude Code is a multimodal LLM.\n- For Jupyter notebooks (.ipynb files), use the NotebookRead instead\n- You have the capability to call multiple tools in a single response. It is always better to speculatively read multiple files as a batch that are potentially useful. \n- You will regularly be asked to read screenshots. If the user provides a path to a screenshot ALWAYS use this tool to view the file at the path. This tool will work with all temporary file paths like /var/folders/123/abc/T/TemporaryItems/NSIRD_screencaptureui_ZfB1tD/Screenshot.png\n- If you read a file that exists but has empty contents you will receive a system reminder warning in place of file contents.")]
    public async Task<string> ReadFileFromLineAsync(
        ReadFileItemInput[] items)
    {
        // ===== 步骤1：初始化结果字典 =====
        // 创建用于存储读取结果的字典
        var dic = new Dictionary<string, string>();
        
        // ===== 步骤2：批量处理文件读取 =====
        // 遍历所有文件项，逐个读取指定行范围的内容
        foreach (var item in items)
        {
            // 构建结果键，包含文件名和行号范围信息
            dic.Add($"fileName:{item.FilePath}\nstartLine:{item.Offset}\nendLine:{item.Limit}",
                await ReadItem(item.FilePath, item.Offset, item.Limit));
        }

        // ===== 步骤3：返回结果 =====
        // 将所有读取结果序列化为JSON格式返回
        return JsonSerializer.Serialize(dic, JsonSerializerOptions.Web);
    }

    /// <summary>
    /// 读取单个文件的指定行范围内容
    /// 该方法支持从指定行号开始读取指定数量的行，适用于大文件的逐行处理
    /// 支持代码压缩和行长度限制，确保返回内容的可读性
    /// </summary>
    /// <param name="filePath">要读取的文件路径（绝对路径或相对于仓库根目录的路径）</param>
    /// <param name="offset">开始读取的行号，如果文件太大无法一次性读取时才提供</param>
    /// <param name="limit">要读取的行数，如果文件太大无法一次性读取时才提供</param>
    /// <returns>带行号的文件内容字符串，格式为"行号: 内容"</returns>
    /// <summary>
    /// 读取单个文件的指定行范围内容
    /// 该方法支持从指定行号开始读取指定数量的行，适用于大文件的逐行处理
    /// 支持代码压缩和行长度限制，确保返回内容的可读性
    /// </summary>
    /// <param name="filePath">要读取的文件路径（绝对路径或相对于仓库根目录的路径）</param>
    /// <param name="offset">开始读取的行号，如果文件太大无法一次性读取时才提供</param>
    /// <param name="limit">要读取的行数，如果文件太大无法一次性读取时才提供</param>
    /// <returns>带行号的文件内容字符串，格式为"行号: 内容"</returns>
    public async Task<string> ReadItem(
        [Description(
            "The absolute or relative path of the target file to read")]
        string filePath,
        [Description(
            "The line number to start reading from. Only provide if the file is too large to read at once")]
        int offset = 0,
        [Description(
            "The number of lines to read. Only provide if the file is too large to read at once.")]
        int limit = 200)
    {
        try
        {
            // ===== 步骤1：构建完整文件路径 =====
            // 将相对路径转换为绝对路径
            filePath = Path.Combine(gitPath, filePath.TrimStart('/'));
            Console.WriteLine(
                $"Reading file from line {offset}: {filePath} startLine={offset}, endLine={limit}");

            // ===== 步骤2：特殊参数处理 =====
            // 如果offset和limit都小于0，则读取整个文件
            if (offset < 0 && limit < 0)
            {
                return await ReadFileAsync(filePath);
            }

            // 如果limit小于0，则读取到最后一行
            if (limit < 0)
            {
                limit = int.MaxValue;
            }

            // ===== 步骤3：读取文件内容 =====
            // 先读取整个文件内容
            string fileContent = await File.ReadAllTextAsync(filePath);

            // ===== 步骤4：代码压缩处理 =====
            // 如果启用代码压缩且是代码文件，先对整个文件内容进行压缩
            if (DocumentOptions.EnableCodeCompression && CodeFileDetector.IsCodeFile(filePath))
            {
                fileContent = _codeCompressionService.CompressCode(fileContent, filePath);
            }

            // ===== 步骤5：按行分割内容 =====
            // 将文件内容按换行符分割成行数组
            var lines = fileContent.Split('\n');

            // ===== 步骤6：边界检查 =====
            // 如果offset大于文件总行数，则返回空内容提示
            if (offset >= lines.Length)
            {
                return $"No content to read from line {offset} in file: {filePath}";
            }

            // ===== 步骤7：计算实际读取范围 =====
            // 计算实际读取的行数，确保不超过文件总行数
            int actualLimit = Math.Min(limit, lines.Length - offset);
            
            // ===== 步骤8：读取指定行范围 =====
            // 读取指定行数的内容
            var resultLines = new List<string>();
            for (int i = offset; i < offset + actualLimit && i < lines.Length; i++)
            {
                // ===== 步骤8.1：行长度限制 =====
                // 如果行内容超过2000字符，则截断
                if (lines[i].Length > 2000)
                {
                    resultLines.Add(lines[i][..2000]);
                }
                else
                {
                    resultLines.Add(lines[i]);
                }
            }

            // ===== 步骤9：添加行号 =====
            // 将结果行号从1开始，格式为"行号: 内容"
            var numberedLines = resultLines.Select((line, index) => $"{index + 1}: {line}").ToList();

            // ===== 步骤10：返回结果 =====
            // 将所有行内容用换行符连接返回
            return string.Join("\n", numberedLines);
        }
        catch (Exception ex)
        {
            // ===== 异常处理 =====
            // 记录错误信息到控制台，便于调试和问题排查
            Console.WriteLine($"Error reading file: {ex.Message}");
            return $"Error reading file: {ex.Message}";
        }
    }
}

/// <summary>
/// 文件读取项输入类
/// 用于指定单个文件的读取参数，包括文件路径、起始行号和读取行数
/// </summary>
public class ReadFileItemInput
{
    /// <summary>
    /// 要读取的目标文件的绝对路径或相对路径
    /// </summary>
    [Description(
        "The absolute or relative path of the target file to read")]
    public string FilePath { get; set; }

    /// <summary>
    /// 开始读取的行号，仅在文件太大无法一次性读取时才提供
    /// </summary>
    [Description(
        "The line number to start reading from. Only provide if the file is too large to read at once")]
    public int Offset { get; set; } = 0;

    /// <summary>
    /// 要读取的行数，仅在文件太大无法一次性读取时才提供
    /// </summary>
    [Description(
        "The number of lines to read. Only provide if the file is too large to read at once.")]
    public int Limit { get; set; } = 200;
}