using System.Text;
using System.Text.RegularExpressions;

namespace KoalaWiki.CodeMap
{
    public class DependencyAnalyzer
    {
        private readonly Dictionary<string, HashSet<string>> _fileDependencies = new();
        private readonly Dictionary<string, HashSet<string>> _functionDependencies = new();
        private readonly Dictionary<string, List<CodeMapFunctionInfo>> _fileToFunctions = new();
        private readonly Dictionary<string, string> _functionToFile = new();
        private readonly List<ILanguageParser> _parsers = new();
        private readonly Dictionary<string, ISemanticAnalyzer> _semanticAnalyzers = new();
        private readonly string _basePath;
        private bool _isInitialized = false;
        private ProjectSemanticModel? _semanticModel;
        private List<GitIgnoreRule> _gitIgnoreRules = new();

        public DependencyAnalyzer(string basePath)
        {
            _basePath = basePath;
            
            // 注册传统解析器（作为回退）
            // _parsers.Add(new CSharpParser());
            _parsers.Add(new JavaScriptParser());
            _parsers.Add(new PythonParser());
            _parsers.Add(new JavaParser());
            _parsers.Add(new CppParser());
            _parsers.Add(new GoParser());
            
            // 注册语义分析器
            RegisterSemanticAnalyzer(new GoSemanticAnalyzer());
            // TODO: 添加其他语言的语义分析器
        }
        
        private void RegisterSemanticAnalyzer(ISemanticAnalyzer analyzer)
        {
            foreach (var extension in analyzer.SupportedExtensions)
            {
                _semanticAnalyzers[extension] = analyzer;
            }
        }

        public async Task Initialize()
        {
            if (_isInitialized)
                return;
                
            // 初始化.gitignore规则
            await InitializeGitIgnore();
            
            var files = GetAllSourceFiles(_basePath);
            
            // 优先使用语义分析器
            await InitializeSemanticAnalysis(files);
            
            // 对不支持语义分析的文件使用传统解析器
            var traditionalFiles = files.Where(f => !HasSemanticAnalyzer(f)).ToList();
            var traditionalTasks = traditionalFiles.Select(async file => 
            {
                var parser = GetParserForFile(file);
                if (parser != null)
                {
                    var fileContent = await File.ReadAllTextAsync(file);
                    await ProcessFile(file, fileContent, parser);
                }
            });
            
            await Task.WhenAll(traditionalTasks);
            _isInitialized = true;
        }
        
        private async Task InitializeSemanticAnalysis(List<string> files)
        {
            var groupedFiles = files.GroupBy(f => Path.GetExtension(f).ToLowerInvariant())
                                   .Where(g => _semanticAnalyzers.ContainsKey(g.Key))
                                   .ToDictionary(g => g.Key, g => g.ToArray());
            
            var tasks = groupedFiles.Select(async kvp =>
            {
                var analyzer = _semanticAnalyzers[kvp.Key];
                var projectModel = await analyzer.AnalyzeProjectAsync(kvp.Value);
                return projectModel;
            });
            
            var models = await Task.WhenAll(tasks);
            
            // 合并语义模型
            _semanticModel = MergeSemanticModels(models);
            
            // 将语义模型转换为传统格式以保持兼容性
            ConvertSemanticToTraditional();
        }
        
        private bool HasSemanticAnalyzer(string filePath)
        {
            var extension = Path.GetExtension(filePath).ToLowerInvariant();
            return _semanticAnalyzers.ContainsKey(extension);
        }
        
        private ProjectSemanticModel MergeSemanticModels(ProjectSemanticModel[] models)
        {
            var merged = new ProjectSemanticModel();
            
            foreach (var model in models)
            {
                foreach (var kvp in model.Files)
                {
                    merged.Files[kvp.Key] = kvp.Value;
                }
                
                foreach (var kvp in model.Dependencies)
                {
                    merged.Dependencies[kvp.Key] = kvp.Value;
                }
                
                foreach (var kvp in model.AllTypes)
                {
                    merged.AllTypes[kvp.Key] = kvp.Value;
                }
                
                foreach (var kvp in model.AllFunctions)
                {
                    merged.AllFunctions[kvp.Key] = kvp.Value;
                }
            }
            
            return merged;
        }
        
        private void ConvertSemanticToTraditional()
        {
            if (_semanticModel == null) return;
            
            // 转换依赖关系
            foreach (var kvp in _semanticModel.Dependencies)
            {
                _fileDependencies[kvp.Key] = new HashSet<string>(kvp.Value);
            }
            
            // 转换函数信息
            foreach (var fileModel in _semanticModel.Files.Values)
            {
                var functionList = new List<CodeMapFunctionInfo>();
                
                // 添加顶级函数
                foreach (var func in fileModel.Functions)
                {
                    functionList.Add(ConvertSemanticFunction(func));
                }
                
                // 添加类型中的方法
                foreach (var type in fileModel.Types)
                {
                    foreach (var method in type.Methods)
                    {
                        functionList.Add(ConvertSemanticFunction(method));
                    }
                }
                
                _fileToFunctions[fileModel.FilePath] = functionList;
                
                // 建立函数到文件的映射
                foreach (var func in functionList)
                {
                    _functionToFile[func.FullName] = fileModel.FilePath;
                }
            }
        }
        
        private CodeMapFunctionInfo ConvertSemanticFunction(CodeMap.FunctionInfo semanticFunc)
        {
            return new CodeMapFunctionInfo
            {
                Name = semanticFunc.Name,
                FullName = semanticFunc.FullName,
                FilePath = semanticFunc.FilePath,
                LineNumber = semanticFunc.LineNumber,
                Body = "", // 语义分析不提供函数体
                Calls = semanticFunc.Calls.Select(c => c.Name).ToList()
            };
        }

        private async Task ProcessFile(string filePath, string fileContent, ILanguageParser parser)
        {
            try
            {
                // 提取文件级依赖
                var imports = parser.ExtractImports(fileContent);
                var resolvedImports = ResolveImportPaths(imports, filePath, _basePath);
                
                lock (_fileDependencies)
                {
                    _fileDependencies[filePath] = resolvedImports;
                }
                
                // 提取函数信息
                var functions = parser.ExtractFunctions(fileContent);
                var functionInfoList = new List<CodeMapFunctionInfo>();
                
                foreach (var function in functions)
                {
                    var functionInfo = new CodeMapFunctionInfo
                    {
                        Name = function.Name,
                        FullName = $"{filePath}:{function.Name}",
                        Body = function.Body,
                        FilePath = filePath,
                        LineNumber = parser.GetFunctionLineNumber(fileContent, function.Name),
                        Calls = parser.ExtractFunctionCalls(function.Body)
                    };
                    
                    functionInfoList.Add(functionInfo);
                    
                    lock (_functionToFile)
                    {
                        _functionToFile[functionInfo.FullName] = filePath;
                    }
                }
                
                lock (_fileToFunctions)
                {
                    _fileToFunctions[filePath] = functionInfoList;
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine($"处理文件 {filePath} 时出错: {ex.Message}");
            }
        }

        public async Task<DependencyTree> AnalyzeFileDependencyTree(string filePath)
        {
            await Initialize();
            
            var normalizedPath = Path.GetFullPath(filePath);
            var visited = new HashSet<string>();
            
            return BuildFileDependencyTree(normalizedPath, visited, 0);
        }

        public async Task<DependencyTree> AnalyzeFunctionDependencyTree(string filePath, string functionName)
        {
            await Initialize();
            
            var normalizedPath = Path.GetFullPath(filePath);
            var visited = new HashSet<string>();
            
            return BuildFunctionDependencyTree(normalizedPath, functionName, visited, 0);
        }

        /// <summary>
        /// 构建文件依赖关系树
        /// 该方法递归构建指定文件的依赖关系树，包括其依赖的文件和包含的函数
        /// 使用深度优先搜索算法，支持循环依赖检测和最大深度限制
        /// 
        /// 【逻辑原理】
        /// 1. 基于图论中的深度优先搜索(DFS)算法
        /// 2. 将文件依赖关系建模为有向图，文件为节点，依赖关系为边
        /// 3. 使用访问标记集合(HashSet)检测循环依赖
        /// 4. 采用递归方式遍历依赖图，构建树形结构
        /// 
        /// 【输入参数】
        /// - filePath: 要分析依赖关系的文件路径（绝对路径）
        /// - visited: 已访问文件的集合，用于循环依赖检测
        /// - level: 当前递归深度，用于控制最大深度
        /// - maxDepth: 最大递归深度限制，防止无限递归（默认10层）
        /// 
        /// 【输出结果】
        /// - DependencyTree: 文件依赖关系树，包含：
        ///   * 文件基本信息（名称、路径、行号）
        ///   * 循环依赖标记
        ///   * 子文件依赖列表（递归结构）
        ///   * 文件中包含的函数列表
        /// 
        /// 【过程逻辑】
        /// 1. 边界检查：检查深度限制和循环依赖
        /// 2. 节点创建：初始化当前文件的依赖树节点
        /// 3. 依赖遍历：递归处理所有依赖文件
        /// 4. 函数收集：收集当前文件中的所有函数信息
        /// 5. 树形构建：组装完整的依赖关系树
        /// </summary>
        /// <param name="filePath">要分析依赖关系的文件路径</param>
        /// <param name="visited">已访问的文件集合，用于检测循环依赖</param>
        /// <param name="level">当前递归深度，用于控制最大深度</param>
        /// <param name="maxDepth">最大递归深度，默认为10层，防止无限递归</param>
        /// <returns>表示文件依赖关系的树形结构</returns>
        private DependencyTree BuildFileDependencyTree(string filePath, HashSet<string> visited, int level, int maxDepth = 10)
        {
            // ===== 步骤1：深度和循环依赖检查 =====
            // 检查是否超过最大深度或已经访问过该文件（循环依赖检测）
            if (level > maxDepth || !visited.Add(filePath))
            {
                // 创建循环依赖节点，标记为已访问
                return new DependencyTree
                {
                    NodeType = DependencyNodeType.File,  // 节点类型：文件
                    Name = Path.GetFileName(filePath),    // 文件名（不含路径）
                    FullPath = filePath,                  // 完整文件路径
                    IsCyclic = visited.Contains(filePath) // 标记是否为循环依赖
                };
            }

            // ===== 步骤2：创建文件依赖树节点 =====
            // 创建当前文件的依赖树节点，初始化基本信息
            var tree = new DependencyTree
            {
                NodeType = DependencyNodeType.File,       // 节点类型：文件
                Name = Path.GetFileName(filePath),        // 文件名（不含路径）
                FullPath = filePath,                      // 完整文件路径
                IsCyclic = false,                        // 初始化为非循环依赖
                Children = new List<DependencyTree>()     // 初始化子节点列表
            };
            
            // ===== 步骤3：添加子文件依赖 =====
            // 查找当前文件的所有依赖文件，并递归构建子依赖树
            if (_fileDependencies.TryGetValue(filePath, out var dependencies))
            {
                // 遍历当前文件的所有依赖文件
                foreach (var dependency in dependencies)
                {
                    // 为每个子节点创建独立的访问集合，避免相互影响
                    var childVisited = new HashSet<string>(visited);
                    // 递归构建子文件的依赖树
                    var child = BuildFileDependencyTree(dependency, childVisited, level + 1, maxDepth);
                    // 将子依赖树添加到当前节点的子节点列表中
                    tree.Children.Add(child);
                }
            }
            
            // ===== 步骤4：添加文件中的函数信息 =====
            // 查找当前文件中包含的所有函数，并添加到依赖树中
            if (_fileToFunctions.TryGetValue(filePath, out var functions))
            {
                // 遍历文件中的所有函数
                foreach (var function in functions)
                {
                    // 创建函数信息节点，包含函数名和行号
                    tree.Functions.Add(new DependencyTreeFunction
                    {
                        Name = function.Name,        // 函数名称
                        LineNumber = function.LineNumber  // 函数在文件中的行号
                    });
                }
            }
            
            // ===== 步骤5：返回构建完成的依赖树 =====
            // 返回包含完整依赖关系的树形结构
            return tree;
        }

        /// <summary>
        /// 构建函数依赖关系树
        /// 该方法递归构建指定函数的依赖关系树，包括其调用的其他函数
        /// 使用深度优先搜索算法，支持循环依赖检测和最大深度限制
        /// 
        /// 【逻辑原理】
        /// 1. 基于函数调用图的深度优先搜索(DFS)算法
        /// 2. 将函数调用关系建模为有向图，函数为节点，调用关系为边
        /// 3. 使用"文件路径:函数名"格式创建函数唯一标识符
        /// 4. 通过访问标记集合检测函数间的循环调用
        /// 5. 采用递归方式遍历调用图，构建函数依赖树
        /// 
        /// 【输入参数】
        /// - filePath: 包含要分析函数的文件路径（绝对路径）
        /// - functionName: 要分析依赖关系的函数名称
        /// - visited: 已访问函数的集合，用于循环依赖检测
        /// - level: 当前递归深度，用于控制最大深度
        /// - maxDepth: 最大递归深度限制，防止无限递归（默认10层）
        /// 
        /// 【输出结果】
        /// - DependencyTree: 函数依赖关系树，包含：
        ///   * 函数基本信息（名称、路径、行号）
        ///   * 循环依赖标记
        ///   * 被调用函数列表（递归结构）
        ///   * 函数调用链的完整路径
        /// 
        /// 【过程逻辑】
        /// 1. 标识符构建：创建函数的唯一标识符
        /// 2. 边界检查：检查深度限制和循环依赖
        /// 3. 节点创建：初始化当前函数的依赖树节点
        /// 4. 函数查找：在文件函数映射中查找目标函数
        /// 5. 调用解析：解析函数中的所有函数调用
        /// 6. 递归构建：为每个被调用函数递归构建依赖树
        /// 7. 树形组装：组装完整的函数调用关系树
        /// </summary>
        /// <param name="filePath">包含要分析函数的文件路径</param>
        /// <param name="functionName">要分析依赖关系的函数名称</param>
        /// <param name="visited">已访问的函数集合，用于检测循环依赖</param>
        /// <param name="level">当前递归深度，用于控制最大深度</param>
        /// <param name="maxDepth">最大递归深度，默认为10层，防止无限递归</param>
        /// <returns>表示函数依赖关系的树形结构</returns>
        private DependencyTree BuildFunctionDependencyTree(string filePath, string functionName, HashSet<string> visited, int level, int maxDepth = 10)
        {
            // ===== 步骤1：构建函数唯一标识符 =====
            // 使用"文件路径:函数名"的格式创建函数的唯一标识符
            // 这样可以区分不同文件中同名的函数
            var fullFunctionId = $"{filePath}:{functionName}";
            
            // ===== 步骤2：深度和循环依赖检查 =====
            // 检查是否超过最大深度或已经访问过该函数（循环依赖检测）
            if (level > maxDepth || !visited.Add(fullFunctionId))
            {
                // 创建循环依赖节点，标记为已访问
                return new DependencyTree
                {
                    NodeType = DependencyNodeType.Function,  // 节点类型：函数
                    Name = functionName,                     // 函数名称
                    FullPath = fullFunctionId,               // 函数唯一标识符
                    IsCyclic = visited.Contains(fullFunctionId) // 标记是否为循环依赖
                };
            }

            // ===== 步骤3：创建函数依赖树节点 =====
            // 创建当前函数的依赖树节点，初始化基本信息
            var tree = new DependencyTree
            {
                NodeType = DependencyNodeType.Function,  // 节点类型：函数
                Name = functionName,                     // 函数名称
                FullPath = fullFunctionId,               // 函数唯一标识符
                IsCyclic = false,                       // 初始化为非循环依赖
                Children = new List<DependencyTree>()    // 初始化子节点列表
            };
            
            // ===== 步骤4：查找当前函数信息并解析调用关系 =====
            // 在文件函数映射中查找当前函数的信息
            if (_fileToFunctions.TryGetValue(filePath, out var functions))
            {
                // 查找指定名称的函数
                var function = functions.FirstOrDefault(f => f.Name == functionName);
                if (function != null)
                {
                    // ===== 步骤4.1：设置函数行号 =====
                    // 记录函数在文件中的行号，便于定位和调试
                    tree.LineNumber = function.LineNumber;
                    
                    // ===== 步骤4.2：解析函数调用关系 =====
                    // 遍历当前函数调用的所有其他函数
                    foreach (var calledFunction in function.Calls)
                    {
                        // 尝试解析被调用函数的完整路径信息
                        // ResolveFunctionCall方法会查找被调用函数所在的文件和具体位置
                        var resolvedFunction = ResolveFunctionCall(calledFunction, filePath);
                        if (resolvedFunction != null)
                        {
                            // 获取被调用函数的文件路径和函数名
                            var calledFilePath = resolvedFunction.FilePath;
                            var calledFunctionName = resolvedFunction.Name;
                            
                            // 为每个子函数创建独立的访问集合，避免相互影响
                            var childVisited = new HashSet<string>(visited);
                            // 递归构建被调用函数的依赖树
                            var child = BuildFunctionDependencyTree(calledFilePath, calledFunctionName, childVisited, level + 1, maxDepth);
                            // 将被调用函数的依赖树添加到当前函数的子节点列表中
                            tree.Children.Add(child);
                        }
                    }
                }
            }
            
            // ===== 步骤5：返回构建完成的函数依赖树 =====
            // 返回包含完整函数调用关系的树形结构
            return tree;
        }

        private HashSet<string> ResolveImportPaths(List<string> imports, string currentFile, string basePath)
        {
            var result = new HashSet<string>();
            var currentDir = Path.GetDirectoryName(currentFile);
            var parser = GetParserForFile(currentFile);
            
            foreach (var import in imports)
            {
                // 根据特定语言解析导入路径
                var resolvedPath = parser.ResolveImportPath(import, currentFile, basePath);
                if (!string.IsNullOrEmpty(resolvedPath) && File.Exists(resolvedPath))
                {
                    result.Add(Path.GetFullPath(resolvedPath));
                }
            }
            
            return result;
        }

        private CodeMapFunctionInfo ResolveFunctionCall(string functionCall, string currentFile)
        {
            // 检查是否为本地函数
            if (_fileToFunctions.TryGetValue(currentFile, out var functions))
            {
                var localFunction = functions.FirstOrDefault(f => f.Name == functionCall);
                if (localFunction != null)
                {
                    return localFunction;
                }
            }
            
            // 检查导入文件中的函数
            if (_fileDependencies.TryGetValue(currentFile, out var dependencies))
            {
                foreach (var dependency in dependencies)
                {
                    if (_fileToFunctions.TryGetValue(dependency, out var dependencyFunctions))
                    {
                        var depFunction = dependencyFunctions.FirstOrDefault(f => f.Name == functionCall);
                        if (depFunction != null)
                        {
                            return depFunction;
                        }
                    }
                }
            }
            
            // 尝试在全局范围内搜索同名函数
            foreach (var entry in _fileToFunctions)
            {
                var foundFunction = entry.Value.FirstOrDefault(f => f.Name == functionCall);
                if (foundFunction != null)
                {
                    return foundFunction;
                }
            }
            
            return null;
        }

        private ILanguageParser GetParserForFile(string filePath)
        {
            var extension = Path.GetExtension(filePath).ToLowerInvariant();
            
            return extension switch
            {
                // ".cs" => _parsers.FirstOrDefault(p => p is CSharpParser),
                ".js" => _parsers.FirstOrDefault(p => p is JavaScriptParser),
                ".py" => _parsers.FirstOrDefault(p => p is PythonParser),
                ".java" => _parsers.FirstOrDefault(p => p is JavaParser),
                ".cpp" or ".h" or ".hpp" or ".cc" => _parsers.FirstOrDefault(p => p is CppParser),
                ".go" => _parsers.FirstOrDefault(p => p is GoParser),
                _ => null
            };
        }

        private List<string> GetAllSourceFiles(string path)
        {
            var extensions = new[] { ".cs", ".js", ".py", ".java", ".cpp", ".h", ".hpp", ".cc", ".go" };
            var allFiles = Directory.GetFiles(path, "*.*", SearchOption.AllDirectories)
                .Where(f => extensions.Contains(Path.GetExtension(f).ToLowerInvariant()));
            
            // 应用.gitignore规则过滤
            return allFiles.Where(f => !IsIgnoredByGitIgnore(f)).ToList();
        }

        private async Task InitializeGitIgnore()
        {
            var gitIgnorePath = Path.Combine(_basePath, ".gitignore");
            if (File.Exists(gitIgnorePath))
            {
                var lines = await File.ReadAllLinesAsync(gitIgnorePath);
                _gitIgnoreRules = ParseGitIgnoreRules(lines);
            }
        }

        private List<GitIgnoreRule> ParseGitIgnoreRules(string[] lines)
        {
            var rules = new List<GitIgnoreRule>();
            
            foreach (var line in lines)
            {
                var trimmedLine = line.Trim();
                
                // 跳过空行和注释
                if (string.IsNullOrEmpty(trimmedLine) || trimmedLine.StartsWith("#"))
                    continue;
                
                var isNegation = trimmedLine.StartsWith("!");
                var pattern = isNegation ? trimmedLine.Substring(1) : trimmedLine;
                
                // 处理目录规则（以/结尾）
                var isDirectory = pattern.EndsWith("/");
                if (isDirectory)
                    pattern = pattern.TrimEnd('/');
                
                // 转换git ignore模式为正则表达式
                var regex = ConvertGitIgnorePatternToRegex(pattern);
                
                rules.Add(new GitIgnoreRule
                {
                    OriginalPattern = trimmedLine,
                    Regex = new Regex(regex, RegexOptions.IgnoreCase | RegexOptions.Compiled),
                    IsNegation = isNegation,
                    IsDirectory = isDirectory
                });
            }
            
            return rules;
        }

        private string ConvertGitIgnorePatternToRegex(string pattern)
        {
            var sb = new StringBuilder();
            
            // 如果模式以/开头，表示从根目录开始匹配
            var isAbsolute = pattern.StartsWith("/");
            if (isAbsolute)
            {
                pattern = pattern.Substring(1);
                sb.Append("^");
            }
            else
            {
                // 非绝对路径可以匹配任何位置
                sb.Append("(^|/)");
            }
            
            // 转换通配符和特殊字符
            for (int i = 0; i < pattern.Length; i++)
            {
                char c = pattern[i];
                switch (c)
                {
                    case '*':
                        if (i + 1 < pattern.Length && pattern[i + 1] == '*')
                        {
                            // ** 匹配任意层级目录
                            if (i + 2 < pattern.Length && pattern[i + 2] == '/')
                            {
                                sb.Append("(.*/)");
                                i += 2; // 跳过 **/ 
                            }
                            else
                            {
                                sb.Append(".*");
                                i++; // 跳过第二个 *
                            }
                        }
                        else
                        {
                            // 单个 * 匹配除路径分隔符外的任意字符
                            sb.Append("[^/]*");
                        }
                        break;
                    case '?':
                        sb.Append("[^/]");
                        break;
                    case '[':
                        // 字符类，直接添加
                        var endBracket = pattern.IndexOf(']', i + 1);
                        if (endBracket > i)
                        {
                            sb.Append(pattern.Substring(i, endBracket - i + 1));
                            i = endBracket;
                        }
                        else
                        {
                            sb.Append("\\[");
                        }
                        break;
                    case '.':
                    case '^':
                    case '$':
                    case '+':
                    case '(':
                    case ')':
                    case '{':
                    case '}':
                    case '|':
                    case '\\':
                        // 转义正则表达式特殊字符
                        sb.Append('\\');
                        sb.Append(c);
                        break;
                    default:
                        sb.Append(c);
                        break;
                }
            }
            
            // 如果不是绝对路径，在末尾添加边界匹配
            if (!isAbsolute)
            {
                sb.Append("($|/)");
            }
            else
            {
                sb.Append("$");
            }
            
            return sb.ToString();
        }

        private bool IsIgnoredByGitIgnore(string filePath)
        {
            if (_gitIgnoreRules.Count == 0)
                return false;
            
            // 获取相对于_basePath的路径
            var relativePath = Path.GetRelativePath(_basePath, filePath).Replace('\\', '/');
            
            bool isIgnored = false;
            
            foreach (var rule in _gitIgnoreRules)
            {
                bool matches = false;
                
                if (rule.IsDirectory)
                {
                    // 对于目录规则，检查是否是目录或在该目录下的文件
                    var dirPath = Path.GetDirectoryName(relativePath)?.Replace('\\', '/') ?? "";
                    matches = rule.Regex.IsMatch(dirPath) || rule.Regex.IsMatch(relativePath);
                }
                else
                {
                    // 文件规则
                    matches = rule.Regex.IsMatch(relativePath);
                }
                
                if (matches)
                {
                    if (rule.IsNegation)
                    {
                        isIgnored = false; // 否定规则，取消忽略
                    }
                    else
                    {
                        isIgnored = true; // 匹配忽略规则
                    }
                }
            }
            
            return isIgnored;
        }

        public string GenerateDependencyTreeVisualization(DependencyTree tree)
        {
            var sb = new StringBuilder();
            GenerateTreeVisualization(tree, sb, "", true);
            return sb.ToString();
        }

        private void GenerateTreeVisualization(DependencyTree node, StringBuilder sb, string indent, bool isLast)
        {
            // 显示当前节点
            var nodeMarker = isLast ? "└── " : "├── ";
            var nodeType = node.NodeType == DependencyNodeType.File ? "[文件]" : "[函数]";
            var cyclicMarker = node.IsCyclic ? " (循环引用)" : "";
            var lineInfo = node.LineNumber > 0 ? $" (行: {node.LineNumber})" : "";
            
            sb.AppendLine($"{indent}{nodeMarker}{nodeType} {node.Name}{lineInfo}{cyclicMarker}");
            
            // 生成下一级缩进
            var childIndent = indent + (isLast ? "    " : "│   ");
            
            // 显示函数列表（仅适用于文件节点）
            if (node.NodeType == DependencyNodeType.File && node.Functions.Count > 0 && !node.IsCyclic)
            {
                sb.AppendLine($"{childIndent}├── [函数列表]");
                var functionsIndent = childIndent + "│   ";
                
                for (int i = 0; i < node.Functions.Count; i++)
                {
                    var function = node.Functions[i];
                    var functionMarker = i == node.Functions.Count - 1 ? "└── " : "├── ";
                    var functionLineInfo = function.LineNumber > 0 ? $" (行: {function.LineNumber})" : "";
                    sb.AppendLine($"{functionsIndent}{functionMarker}{function.Name}{functionLineInfo}");
                }
            }
            
            // 显示子节点
            if (node is { IsCyclic: false, Children: not null })
            {
                for (int i = 0; i < node.Children.Count; i++)
                {
                    GenerateTreeVisualization(node.Children[i], sb, childIndent, i == node.Children.Count - 1);
                }
            }
        }

        public string GenerateDotGraph(DependencyTree tree)
        {
            var sb = new StringBuilder();
            sb.AppendLine("digraph DependencyTree {");
            sb.AppendLine("  node [shape=box, style=filled, fontname=\"Arial\"];");
            sb.AppendLine("  edge [fontname=\"Arial\"];");
            
            // 生成节点和边
            var nodeCounter = new Dictionary<string, int>();
            GenerateDotNodes(tree, sb, nodeCounter);
            
            sb.AppendLine("}");
            return sb.ToString();
        }

        /// <summary>
        /// 检查指定文件是否被.gitignore规则忽略
        /// </summary>
        /// <param name="filePath">要检查的文件路径</param>
        /// <returns>如果文件被忽略返回true，否则返回false</returns>
        public async Task<bool> IsFileIgnored(string filePath)
        {
            await InitializeGitIgnore();
            return IsIgnoredByGitIgnore(filePath);
        }

        /// <summary>
        /// 获取当前加载的.gitignore规则信息
        /// </summary>
        /// <returns>规则信息的列表</returns>
        public async Task<List<string>> GetGitIgnoreRules()
        {
            await InitializeGitIgnore();
            return _gitIgnoreRules.Select(r => r.OriginalPattern).ToList();
        }

        private void GenerateDotNodes(DependencyTree node, StringBuilder sb, Dictionary<string, int> nodeCounter, string parentId = null)
        {
            // 生成唯一节点ID
            string nodeId;
            if (!nodeCounter.ContainsKey(node.FullPath))
            {
                nodeCounter[node.FullPath] = nodeCounter.Count;
            }
            nodeId = $"node{nodeCounter[node.FullPath]}";
            
            // 节点样式
            string nodeColor = node.NodeType == DependencyNodeType.File ? "lightblue" : "lightgreen";
            if (node.IsCyclic) nodeColor = "lightsalmon";
            
            string label = node.Name;
            if (node.LineNumber > 0) label += $"\\n(行: {node.LineNumber})";
            if (node.IsCyclic) label += "\\n(循环引用)";
            
            // 创建节点
            sb.AppendLine($"  {nodeId} [label=\"{label}\", fillcolor=\"{nodeColor}\"];");
            
            // 与父节点连接
            if (parentId != null)
            {
                sb.AppendLine($"  {parentId} -> {nodeId};");
            }
            
            // 递归处理子节点
            if (!node.IsCyclic && node.Children != null)
            {
                foreach (var child in node.Children)
                {
                    GenerateDotNodes(child, sb, nodeCounter, nodeId);
                }
            }
        }
    }

    public class CodeMapFunctionInfo
    {
        public string Name { get; set; }
        public string FullName { get; set; }
        public string Body { get; set; }
        public string FilePath { get; set; }
        public int LineNumber { get; set; }
        public List<string> Calls { get; set; } = new List<string>();
    }

    public class Function
    {
        public string Name { get; set; }
        public string Body { get; set; }
    }

    public enum DependencyNodeType
    {
        File,
        Function
    }

    public class DependencyTree
    {
        public DependencyNodeType NodeType { get; set; }
        public string Name { get; set; }
        public string FullPath { get; set; }
        public int LineNumber { get; set; }
        public bool IsCyclic { get; set; }
        public List<DependencyTree> Children { get; set; } = new List<DependencyTree>();
        public List<DependencyTreeFunction> Functions { get; set; } = new List<DependencyTreeFunction>();
    }

    public class DependencyTreeFunction
    {
        public string Name { get; set; }
        public int LineNumber { get; set; }
    }

    public class GitIgnoreRule
    {
        public string OriginalPattern { get; set; }
        public Regex Regex { get; set; }
        public bool IsNegation { get; set; }
        public bool IsDirectory { get; set; }
    }
}
