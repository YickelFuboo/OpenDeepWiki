from typing import List, Dict, Optional
from enum import Enum
import re
from dataclasses import dataclass, field


class DependencyNodeType(Enum):
    """依赖节点类型"""
    FILE = "file"
    FUNCTION = "function"


class TypeKind(Enum):
    """类型种类"""
    CLASS = "class"
    INTERFACE = "interface"
    STRUCT = "struct"
    ENUM = "enum"
    DELEGATE = "delegate"
    RECORD = "record"


class AccessModifier(Enum):
    """访问修饰符"""
    PUBLIC = "public"
    PRIVATE = "private"
    PROTECTED = "protected"
    INTERNAL = "internal"
    PROTECTED_INTERNAL = "protected_internal"
    PRIVATE_PROTECTED = "private_protected"


@dataclass
class CodeMapFunctionInfo:
    """代码映射函数信息"""
    name: str = ""
    full_name: str = ""
    body: str = ""
    file_path: str = ""
    line_number: int = 0
    calls: List[str] = field(default_factory=list)


@dataclass
class Function:
    """函数信息"""
    name: str = ""
    body: str = ""


@dataclass
class DependencyTreeFunction:
    """依赖树函数信息"""
    name: str = ""
    line_number: int = 0


@dataclass
class DependencyTree:
    """依赖树"""
    node_type: DependencyNodeType = DependencyNodeType.FILE
    name: str = ""
    full_path: str = ""
    line_number: int = 0
    is_cyclic: bool = False
    children: List['DependencyTree'] = field(default_factory=list)
    functions: List[DependencyTreeFunction] = field(default_factory=list)


@dataclass
class GitIgnoreRule:
    """Git忽略规则"""
    original_pattern: str = ""
    regex: Optional[re.Pattern] = None
    is_negation: bool = False
    is_directory: bool = False


@dataclass
class ParameterInfo:
    """参数信息"""
    name: str = ""
    type: str = ""
    is_optional: bool = False
    default_value: str = ""


@dataclass
class FunctionCallInfo:
    """函数调用信息"""
    name: str = ""
    full_name: str = ""
    line_number: int = 0
    arguments: List[str] = field(default_factory=list)
    is_static: bool = False


@dataclass
class VariableInfo:
    """变量信息"""
    name: str = ""
    type: str = ""
    line_number: int = 0
    access_modifier: AccessModifier = AccessModifier.PUBLIC
    is_static: bool = False
    is_readonly: bool = False
    is_const: bool = False


@dataclass
class ImportInfo:
    """导入信息"""
    name: str = ""
    alias: str = ""
    file_path: str = ""
    is_wildcard: bool = False
    imported_members: List[str] = field(default_factory=list)


@dataclass
class FunctionInfo:
    """函数信息"""
    name: str = ""
    full_name: str = ""
    file_path: str = ""
    line_number: int = 0
    end_line_number: int = 0
    return_type: str = ""
    parameters: List[ParameterInfo] = field(default_factory=list)
    generic_parameters: List[str] = field(default_factory=list)
    calls: List[FunctionCallInfo] = field(default_factory=list)
    access_modifier: AccessModifier = AccessModifier.PUBLIC
    is_static: bool = False
    is_async: bool = False
    is_abstract: bool = False
    is_virtual: bool = False
    is_override: bool = False
    parent_type: str = ""


@dataclass
class TypeInfo:
    """类型信息"""
    name: str = ""
    full_name: str = ""
    kind: TypeKind = TypeKind.CLASS
    file_path: str = ""
    line_number: int = 0
    end_line_number: int = 0
    base_types: List[str] = field(default_factory=list)
    interfaces: List[str] = field(default_factory=list)
    methods: List[FunctionInfo] = field(default_factory=list)
    fields: List[VariableInfo] = field(default_factory=list)
    generic_parameters: List[str] = field(default_factory=list)
    access_modifier: AccessModifier = AccessModifier.PUBLIC
    is_abstract: bool = False
    is_sealed: bool = False
    is_static: bool = False


@dataclass
class SemanticModel:
    """语义模型"""
    file_path: str = ""
    namespace: str = ""
    types: List[TypeInfo] = field(default_factory=list)
    functions: List[FunctionInfo] = field(default_factory=list)
    imports: List[ImportInfo] = field(default_factory=list)
    variables: List[VariableInfo] = field(default_factory=list)


@dataclass
class ProjectSemanticModel:
    """项目语义模型"""
    files: Dict[str, SemanticModel] = field(default_factory=dict)
    dependencies: Dict[str, List[str]] = field(default_factory=dict)
    all_types: Dict[str, TypeInfo] = field(default_factory=dict)
    all_functions: Dict[str, FunctionInfo] = field(default_factory=dict) 