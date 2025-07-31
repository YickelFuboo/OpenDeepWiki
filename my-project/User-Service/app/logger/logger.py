import logging
import sys
import os
from datetime import datetime
from typing import Optional
from enum import Enum
import inspect
import colorama

# 初始化colorama以支持Windows下的彩色输出
colorama.init()

class LogLevel(str, Enum):
    """日志级别"""
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    FATAL = "FATAL"

class ColorCode:
    """日志颜色代码"""
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    RED = "\033[31m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    RESET = "\033[0m"

class Logger:
    """统一日志工具类"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Logger, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """初始化日志配置"""
        self.logger = logging.getLogger("user-service")
        self.logger.setLevel(logging.INFO)
        
        # 如果已经有处理器，不重复添加
        if not self.logger.handlers:
            # 控制台处理器
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(logging.INFO)
            self.logger.addHandler(console_handler)
            
            # 文件处理器
            log_dir = "logs"
            if not os.path.exists(log_dir):
                os.makedirs(log_dir)
            file_handler = logging.FileHandler(
                os.path.join(log_dir, f"pando_{datetime.now().strftime('%Y%m%d')}.log"),
                encoding='utf-8'
            )
            file_handler.setLevel(logging.INFO)
            self.logger.addHandler(file_handler)

    def _get_caller_info(self) -> tuple:
        """获取调用者信息"""
        frame = inspect.currentframe()
        # 向上查找3层调用栈以跳过日志模块内部调用
        for _ in range(3):
            if frame.f_back is not None:
                frame = frame.f_back
        
        filename = frame.f_code.co_filename
        lineno = frame.f_lineno
        func_name = frame.f_code.co_name
        
        # 获取相对路径
        try:
            filename = os.path.relpath(filename)
        except ValueError:
            # 如果无法获取相对路径，使用绝对路径
            pass
            
        # 移除.py后缀
        if filename.endswith('.py'):
            filename = filename[:-3]
            
        # 将路径分隔符替换为点
        module_path = filename.replace(os.sep, '.')
        
        return module_path, func_name, lineno

    def _format_message(self, level: LogLevel, message: str, module_path: str, func_name: str, lineno: int) -> str:
        """格式化日志消息"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        
        # 根据日志级别选择颜色
        color_code = {
            LogLevel.INFO: ColorCode.GREEN,
            LogLevel.WARNING: ColorCode.YELLOW,
            LogLevel.ERROR: ColorCode.RED,
            LogLevel.FATAL: ColorCode.MAGENTA
        }.get(level, ColorCode.RESET)
        
        # 格式化日志
        log_format = (
            f"{ColorCode.GREEN}{timestamp}{ColorCode.RESET} | "
            f"{color_code}{level:8}{ColorCode.RESET} | "
            f"{ColorCode.CYAN}{module_path}:{func_name}:{lineno}{ColorCode.RESET} - "
            f"{message}"
        )
        
        return log_format

    def log(self, level: LogLevel, message: str):
        """记录日志"""
        module_path, func_name, lineno = self._get_caller_info()
        formatted_message = self._format_message(level, message, module_path, func_name, lineno)
        
        # 根据级别调用相应的日志方法
        log_method = {
            LogLevel.INFO: self.logger.info,
            LogLevel.WARNING: self.logger.warning,
            LogLevel.ERROR: self.logger.error,
            LogLevel.FATAL: self.logger.critical
        }.get(level, self.logger.info)
        
        log_method(formatted_message)

    def info(self, message: str):
        """信息日志"""
        self.log(LogLevel.INFO, message)
        
    def warning(self, message: str):
        """警告日志"""
        self.log(LogLevel.WARNING, message)
        
    def error(self, message: str):
        """错误日志"""
        self.log(LogLevel.ERROR, message)
        
    def fatal(self, message: str):
        """致命错误日志"""
        self.log(LogLevel.FATAL, message)

# 创建全局日志实例
logger = Logger() 