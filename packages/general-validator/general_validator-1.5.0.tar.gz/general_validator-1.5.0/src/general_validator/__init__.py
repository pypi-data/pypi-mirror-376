__version__ = "1.5.0"
__description__ = "General-Validator is a universal batch data validator with detailed validation results."

# 导入基础类
from .base import BaseValidator

# 导入原有的校验函数（保持向后兼容）
from .checker import (
    check,
    check_not_empty,
    check_when,
    check_when_each,
    check_list_when,
    check_list,
    check_nested,
    checker
)

# 导入新的增强版校验函数和数据结构
from .validator import (
    validate,
    validate_not_empty,
    validate_when,
    validate_when_each,
    validate_list_when,
    validate_list,
    validate_nested,
    validator,
    ValidationResult,
    ValidationError,
    RuleResult,
    FieldResult
)

__all__ = [
    # 版本信息
    "__version__", 
    "__description__",
    
    # 基础类
    "BaseValidator",        # 校验器基类

    # 原有API（保持完全向后兼容）
    "check",                # 通用校验函数
    "check_not_empty",      # 非空校验函数
    "check_when",           # 严格条件校验
    "check_when_each",      # 逐项条件校验
    "check_list_when",      # check_when_each的简化版，专门用于列表数据
    "check_list",           # 列表校验函数
    "check_nested",         # 嵌套列表校验函数
    "checker",              # 链式校验函数
    
    # 新增API（返回详细校验信息）
    "validate",             # 通用校验函数 - 增强版
    "validate_not_empty",   # 非空校验函数 - 增强版
    "validate_when",        # 严格条件校验 - 增强版
    "validate_when_each",   # 逐项条件校验 - 增强版
    "validate_list_when",   # 列表条件校验 - 增强版
    "validate_list",        # 列表校验函数 - 增强版
    "validate_nested",      # 嵌套列表校验函数 - 增强版
    "validator",            # 链式校验函数 - 增强版
    
    # 数据结构和异常类
    "ValidationResult",     # 详细校验结果类
    "ValidationError",      # 校验失败异常类
    "RuleResult",           # 单个规则校验结果类
    "FieldResult",          # 单个字段校验结果类
]