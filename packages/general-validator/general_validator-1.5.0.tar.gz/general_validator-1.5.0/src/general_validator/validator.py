# -*- coding:utf-8 -*-
"""
General-Validator 增强版 API - 返回详细校验信息

新增的 validate 系列函数支持：
1. 校验成功时返回详细的 ValidationResult 对象
2. 校验失败时抛出包含完整信息的 ValidationError 异常
3. 与现有 check 系列 API 完全兼容，共享核心校验逻辑
"""
from typing import List, Optional
from .logger import log_debug, log_info, log_warning, log_error
from .base import BaseValidator
from .checker import ValidationEngine, perform_item_wise_conditional_check, get_nested_value, _parse_and_validate


class FieldResult:
    """单个字段的校验结果"""
    
    def __init__(self, field_path, validator, expect_value, actual_value, success, message):
        self.field_path = field_path          # 字段路径，如 "users[1].name"
        self.validator = validator            # 校验器名称，如 "not_empty", "gt"
        self.expect_value = expect_value      # 期望值，如 "> 0", "not empty"
        self.actual_value = actual_value      # 实际值
        self.success = success                # 是否校验成功
        self.message = message                # 详细描述信息

    def to_dict(self):
        """返回字段结果的字典格式"""
        return {
            "field_path": self.field_path,
            "validator": self.validator,
            "expect_value": self.expect_value,
            "actual_value": self.actual_value,
            "success": self.success,
            "message": self.message
        }


class RuleResult:
    """单个规则的校验结果"""
    
    def __init__(self, rule, total_fields, passed_fields, failed_fields, field_results=None, 
                 success=True, failure_rate=0.0, threshold_info=""):
        self.rule = rule                      # 原始规则表达式，如 "users.*.age > 18"
        self.total_fields = total_fields      # 该规则匹配到的字段总数
        self.passed_fields = passed_fields    # 通过校验的字段数
        self.failed_fields = failed_fields    # 失败的字段数  
        self.field_results = field_results or []  # 所有字段的详细结果
        self.success = success                # 规则是否整体成功（考虑阈值）
        self.failure_rate = failure_rate      # 失败率
        self.threshold_info = threshold_info  # 阈值信息描述

    def to_dict(self):
        """返回规则结果的字典格式"""
        return {
            "rule": self.rule,
            "total_fields": self.total_fields,
            "passed_fields": self.passed_fields,
            "failed_fields": self.failed_fields,
            "success": self.success,
            "failure_rate": self.failure_rate,
            "threshold_info": self.threshold_info,
            "field_results": [field_result.to_dict() for field_result in self.field_results]
        }


class ValidationResult:
    """整体校验结果"""
    
    def __init__(self, success, total_rules, passed_rules, failed_rules, rule_results=None,
                 summary="", max_fail_info="", execution_mode="strict", fast_fail=True, output_format="summary"):
        self.success = success                # 整体是否成功
        self.total_rules = total_rules        # 总规则数
        self.passed_rules = passed_rules      # 通过的规则数
        self.failed_rules = failed_rules      # 失败的规则数
        self.rule_results = rule_results or []  # 所有规则的详细结果
        self.summary = summary                # 结果摘要
        self.max_fail_info = max_fail_info    # 失败阈值信息
        self.execution_mode = execution_mode  # 执行模式：strict/threshold
        self.fast_fail = fast_fail            # 快速失败
        self.output_format = output_format    # 输出格式：summary/detail/dict

    def __str__(self):
        """返回校验结果信息"""
        if self.output_format == "summary":
            return self.summary
        elif self.output_format == "detail":
            return self.get_detail_message()
        elif self.output_format == "dict":
            return self.to_dict()
        else:
            return self.summary

    def get_detail_message(self):
        """返回校验结果详情信息"""
        # 构建详细信息
        detail_message = self.summary

        # 添加所有规则概览
        if self.rule_results:
            detail_message += f"\n\n规则执行概览 ({len(self.rule_results)} 个规则):"
            for rule_result in self.rule_results:
                status_icon = "✓" if rule_result.success else "✗"
                detail_message += f"\n  {status_icon} {rule_result.rule}: {rule_result.passed_fields}/{rule_result.total_fields} 个字段通过"
                if rule_result.failure_rate > 0:
                    detail_message += f" (失败率: {rule_result.failure_rate:.1%})"
                if rule_result.threshold_info and not rule_result.success:
                    detail_message += f" - {rule_result.threshold_info}"
        
        # 添加具体字段详情
        all_field_results = []
        for rule_result in self.rule_results:
            all_field_results.extend(rule_result.field_results)
            
        if all_field_results:
            # 分别显示失败和成功的字段
            failed_fields = [f for f in all_field_results if not f.success]
            success_fields = [f for f in all_field_results if f.success]
            
            # 失败字段详情（最多显示10个）
            if failed_fields:
                detail_message += f"\n\n失败字段详情:"
                display_count = min(len(failed_fields), 10)
                for field_result in failed_fields[:display_count]:
                    detail_message += f"\n  ✗ {field_result.field_path}: {field_result.message}"
                
                if len(failed_fields) > display_count:
                    detail_message += f"\n  ... 还有 {len(failed_fields) - display_count} 个字段失败"
            
            # 成功字段概要（如果有失败字段则只显示统计，否则显示前几个成功字段）
            if success_fields:
                if failed_fields:
                    detail_message += f"\n\n成功字段统计: {len(success_fields)} 个字段校验通过"
                else:
                    # 没有失败字段时，显示前几个成功字段作为示例
                    detail_message += f"\n\n成功字段详情:"
                    display_count = min(len(success_fields), 5)
                    for field_result in success_fields[:display_count]:
                        detail_message += f"\n  ✓ {field_result.field_path}: {field_result.message}"
                    
                    if len(success_fields) > display_count:
                        detail_message += f"\n  ... 还有 {len(success_fields) - display_count} 个字段通过"
        
        # 添加阈值信息
        if self.max_fail_info:
            detail_message += f"\n\n阈值设置: {self.max_fail_info}"
        
        return detail_message

    def get_error_message(self):
        """返回校验异常消息"""
        # 构建异常消息
        error_message = self.summary
        
        # 添加失败规则概览
        failed_rules = self.get_failed_rules()
        if failed_rules:
            error_message += f"\n\n失败规则概览 ({len(failed_rules)}/{self.total_rules}):"
            for rule_result in failed_rules:
                error_message += f"\n  ✗ {rule_result.rule}: {rule_result.failed_fields}/{rule_result.total_fields} 个字段失败"
                if rule_result.threshold_info:
                    error_message += f" ({rule_result.threshold_info})"
        
        # 添加具体失败字段（最多显示10个，避免信息过多）
        failed_fields = self.get_failed_fields()
        if failed_fields:
            error_message += f"\n\n具体失败字段:"
            display_count = min(len(failed_fields), 10)
            for field_result in failed_fields[:display_count]:
                error_message += f"\n  - {field_result.field_path}: {field_result.message}"
            
            if len(failed_fields) > display_count:
                error_message += f"\n  ... 还有 {len(failed_fields) - display_count} 个字段失败"
        
        return error_message

    def to_dict(self):
        """
        返回校验结果结构化信息
        
        包含以下信息：
        - 顶层校验统计信息
        - 详细的规则执行结果  
        - 具体的字段校验详情
        - 阈值和执行模式信息
        
        :return: dict - 完整的校验结果字典
        """
        return {
            # 整体校验结果
            "success": self.success,
            "summary": self.summary,
            
            # 统计信息
            "statistics": {
                "total_rules": self.total_rules,
                "passed_rules": self.passed_rules,
                "failed_rules": self.failed_rules,
                "success_rate": self.get_success_rate()
            },
            
            # 执行配置
            "execution_config": {
                "execution_mode": self.execution_mode,
                "fast_fail": self.fast_fail,
                "max_fail_info": self.max_fail_info
            },
            
            # 详细规则结果
            "rule_results": [rule_result.to_dict() for rule_result in self.rule_results],
            
            # 聚合字段信息
            "field_summary": {
                "total_fields": sum(rule.total_fields for rule in self.rule_results),
                "passed_fields": sum(rule.passed_fields for rule in self.rule_results),
                "failed_fields": sum(rule.failed_fields for rule in self.rule_results)
            },
            
            # 失败详情统计
            "failure_analysis": {
                "failed_rule_count": len(self.get_failed_rules()),
                "failed_field_count": len(self.get_failed_fields()),
                "failed_rules": [rule.rule for rule in self.get_failed_rules()],
                "failed_fields": [field.field_path for field in self.get_failed_fields()]
            }
        }

    def get_failed_rules(self) -> List[RuleResult]:
        """获取所有失败的规则"""
        return [rule for rule in self.rule_results if not rule.success]
    
    def get_failed_fields(self) -> List[FieldResult]:
        """获取所有失败的字段"""
        failed_fields = []
        for rule_result in self.rule_results:
            failed_fields.extend([field for field in rule_result.field_results if not field.success])
        return failed_fields
    
    def get_success_rate(self) -> float:
        """获取成功率"""
        return (self.passed_rules / self.total_rules) if self.total_rules > 0 else 1.0


class ValidationError(Exception):
    """校验失败异常，包含详细的失败信息"""
    
    def __init__(self, result: ValidationResult, output_format="summary"):
        self.result = result
        self.output_format = output_format

        if self.output_format == "summary":
            error_message = result.get_error_message()
        elif self.output_format == "detail":
            error_message = result.get_detail_message()
        elif self.output_format == "dict":
            error_message = result.to_dict()
        else:
            error_message = result.get_error_message()

        super().__init__(error_message)
    
    def get_failed_rule_count(self) -> int:
        """获取失败规则数量"""
        return len(self.result.get_failed_rules())
    
    def get_failed_field_count(self) -> int:
        """获取失败字段数量"""
        return len(self.result.get_failed_fields())
        
    def get_first_failed_rule(self) -> Optional[RuleResult]:
        """获取第一个失败的规则"""
        failed_rules = self.result.get_failed_rules()
        return failed_rules[0] if failed_rules else None
        
    def get_first_failed_field(self) -> Optional[FieldResult]:
        """获取第一个失败的字段"""
        failed_fields = self.result.get_failed_fields()
        return failed_fields[0] if failed_fields else None


def validate(data, *validations, max_fail=None, fast_fail=True, output_format="summary") -> ValidationResult:
    """
    极简数据校验函数
    
    :param data: 要校验的数据
    :param validations: 校验规则，支持多种简洁格式
    :param max_fail: 失败阈值
        - None: 严格模式，一个失败全部失败（默认）
        - int: 每个规则最多允许N个失败
        - float: 每个规则最多允许N%失败率
    :param fast_fail: 快速失败，默认True
    :param output_format: 校验结果输出格式：summary/detail/dict
    :return: ValidationResult 对象，包含详细校验信息
    :raises: ValidationError: 当校验失败时抛出，包含完整失败详情
    :raises: Exception: 当参数错误或数据结构异常时抛出异常
    
    示例：
    
    # 1. 成功场景 - 获取详细校验结果
    try:
        result = validate(data, "field1", "field2 > 0", "field3")
        print(f"校验成功: {result.summary}")
        print(f"共校验了 {result.total_rules} 个规则，全部通过")
        
        # 查看每个规则的执行详情
        for rule_result in result.rule_results:
            print(f"规则 '{rule_result.rule}': {rule_result.passed_fields}/{rule_result.total_fields} 字段通过")
    
    # 2. 失败场景 - 快速定位问题根源  
    except ValidationError as e:
        print(f"校验失败: {str(e)}")
        
        # 快速定位：第一个失败的规则和字段
        first_failed_rule = e.get_first_failed_rule()
        first_failed_field = e.get_first_failed_field()
        if first_failed_field:
            print(f"首个失败: {first_failed_field.field_path} -> {first_failed_field.message}")
        
        # 详细分析：遍历所有失败项
        for rule_result in e.result.get_failed_rules():
            print(f"失败规则: {rule_result.rule}")
            for field_result in [f for f in rule_result.field_results if not f.success]:
                print(f"  - {field_result.field_path}: 期望{field_result.expect_value}, 实际{field_result.actual_value}")
    
    # 3. 阈值模式 - 灵活的质量控制
    try:
        result = validate(data, "users.*.id > 0", "users.*.name", max_fail=0.1)  # 允许10%失败
        print(f"校验通过: {result.summary}")
        if result.execution_mode == "threshold":
            print("在可接受的质量范围内")
    except ValidationError as e:
        print(f"质量不达标: {str(e)}")
        print(f"失败率超过了设定的阈值 ({e.result.max_fail_info})")
    """
    # 使用核心引擎执行校验
    engine = ValidationEngine()
    context = engine.execute(data, validations, max_fail, fast_fail, output_format=output_format)
    
    # 构建详细结果
    result = context.build_detailed_result()
    
    # 根据结果决定返回成功对象还是抛出异常
    if result.success:
        return result
    else:
        raise ValidationError(result, output_format=output_format)


def validate_not_empty(data, *validations, max_fail=None, fast_fail=True, output_format="summary") -> ValidationResult:
    """
    专门的非空校验
    
    :param data: 要校验的数据
    :param validations: 校验规则，支持多种简洁格式
    :param max_fail: 失败阈值
        - None: 严格模式，一个失败全部失败（默认）
        - int: 每个规则最多允许N个失败
        - float: 每个规则最多允许N%失败率
    :param fast_fail: 快速失败，默认True
    :param output_format: 校验结果输出格式：summary/detail/dict
    :return: ValidationResult: 当校验成功时返回校验结果对象
    :raises: ValidationError: 当校验失败时抛出异常
    :raises: Exception: 当参数错误或数据结构异常时抛出异常
    
    示例：
    try:
        result = validate_not_empty(data, "field1", "field2")
        print(f"非空校验成功: {result}")
    except ValidationError as e:
        print(f"非空校验失败: {e}")
    """
    return validate(data, *validations, max_fail=max_fail, fast_fail=fast_fail, output_format=output_format)


def validate_when(data, condition, *then, max_fail=None, fast_fail=True, output_format="summary") -> ValidationResult:
    """
    严格条件校验 -  - 所有匹配项都满足条件时才执行then校验（第一种语义）
    
    语义说明：
    1. 对所有数据项进行条件校验
    2. 如果所有数据项都满足条件，就执行then规则校验
    3. 如果任一数据项不满足条件，就跳过整个then校验（返回成功）
    4. 每个then规则有独立的统计维度
    
    :param data: 要校验的数据
    :param condition: 条件表达式，支持所有校验器语法
    :param then: then表达式，支持所有校验器语法，可传入多个校验规则
    :param max_fail: 失败阈值
        - None: 严格模式，一个失败全部失败（默认）
        - int: 每个规则最多允许N个失败
        - float: 每个规则最多允许N%失败率
    :param fast_fail: 快速失败，默认True
    :param output_format: 校验结果输出格式：summary/detail/dict
    :return: ValidationResult: 当校验成功时返回校验结果对象
    :raises: ValidationError: 当校验失败时抛出异常
    :raises: Exception: 当参数错误或数据结构异常时抛出异常
    
    示例：
    try:
        result = validate_when(data, "products.*.status == 'active'", "products.*.price > 0")
        print(f"条件校验成功: {result}")
    except ValidationError as e:
        print(f"条件校验失败: {e}")
    """
    # 参数验证
    if not then:
        raise ValueError("至少需要提供一个then校验规则")
    
    log_info(f"开始严格条件校验 - 数据长度: {len(data)}, then规则数: {len(then)}")
    log_debug(f"校验规则: validate_when({condition}) then({', '.join(str(rule) for rule in then)})")
    log_debug(f"失败阈值: {'默认严格模式' if max_fail is None else max_fail}")
    
    try:
        # 检查条件是否满足（条件检查不计入统计）
        condition_result = _parse_and_validate(data, condition, context=None)
        
        # 条件不成立，跳过then校验
        if not condition_result:
            result = f"条件不成立: validate_when({condition}), 跳过then校验"
            log_warning(result)
            return ValidationResult(success=True, total_rules=0, passed_rules=0, failed_rules=0, summary=result, fast_fail=fast_fail, output_format=output_format)

        # 条件成立，直接调用validate()函数校验then规则。这样每个then规则自然成为独立的统计维度
        log_debug(f"条件成立: validate_when({condition}), 执行then校验")
        return validate(data, *then, max_fail=max_fail, fast_fail=fast_fail, output_format=output_format)
    except ValidationError as e:
        log_error(f"❌ 严格条件校验失败: validate_when({condition}) - '{str(e)}'")
        raise
    except Exception as e:
        log_error(f"❌ 严格条件校验出现异常: validate_when({condition}) - '{str(e)}'")
        raise


def validate_when_each(data, condition, *then, max_fail=None, fast_fail=True, output_format="summary") -> ValidationResult:
    """
    逐项条件校验 - 对指定路径下的每个数据项分别进行条件+then检查（第二种语义）
    
    语义说明：
    1. 通过路径表达式定位要检查的数据项列表
    2. 对每个数据项分别进行条件检查
    3. 对满足条件的数据项执行then规则校验，不满足则跳过
    4. 每个then规则按照满足条件的数据项独立统计失败率
    
    与validate_list_when的区别：
    - validate_list_when：专门用于列表数据，需要预先提取列表，如 users = data["users"]
    - validate_when_each：支持任意数据类型，直接使用路径表达式，如 "users.*.status == 'active'"
    
    :param data: 要校验的数据（任意类型）
    :param condition: 条件表达式，使用路径表达式，如 "users.*.status == 'active'"
    :param then: then规则，使用路径表达式，如 "users.*.score > 70"，可传入多个校验规则
    :param max_fail: 失败阈值
        - None: 严格模式，一个失败全部失败（默认）
        - int: 每个规则最多允许N个失败
        - float: 每个规则最多允许N%失败率
    :param fast_fail: 快速失败，默认True
    :param output_format: 校验结果输出格式：summary/detail/dict
    :return: ValidationResult: 当校验成功时返回校验结果对象
    :raises: ValidationError: 当校验失败时抛出异常
    :raises: Exception: 当参数错误或数据结构异常时抛出异常
    
    示例：
    try:
        result = validate_when_each(data, "users.*.status == 'active'", "users.*.score > 70")
        print(f"逐项校验成功: {result}")
    except ValidationError as e:
        print(f"逐项校验失败: {str(e)}")
    """
    # 参数验证
    if not then:
        raise ValueError("至少需要提供一个then校验规则")
    
    log_info(f"开始逐项条件校验 - 数据长度: {len(data)}, then规则数: {len(then)}")
    log_debug(f"校验规则: validate_when_each({condition}) then({', '.join(str(rule) for rule in then)})")
    log_debug(f"失败阈值: {'默认严格模式' if max_fail is None else max_fail}")
    
    try:
        return perform_item_wise_conditional_check(data, condition, then, max_fail, fast_fail, is_bool_mode=False, output_format=output_format)
    except ValidationError as e:
        log_error(f"❌ 逐项条件校验失败: validate_when_each({condition}) - '{str(e)}'")
        raise
    except Exception as e:
        log_error(f"❌ 逐项条件校验出现异常: validate_when_each({condition}) - '{str(e)}'")
        raise



def validate_list_when(data_list, condition, *then, max_fail=None, fast_fail=True, output_format="summary") -> ValidationResult:
    """
    列表逐项条件校验 - validate_when_each函数的简化版，专门用于列表数据

    语义说明：
    1. 针对数据项列表，对每个数据项分别进行条件检查
    2. 对满足条件的数据项执行then规则校验，不满足则跳过
    3. 每个then规则按照满足条件的数据项独立统计失败率
    4. 每个then规则的失败率 = (满足条件但then失败的数据项数) / (满足条件的数据项总数)

    :param data_list: 要校验的数据列表
    :param condition: 条件表达式，支持所有校验器语法
    :param then: then表达式，支持所有校验器语法，可传入多个校验规则
    :param max_fail: 失败阈值
        - None: 严格模式，一个失败全部失败（默认）
        - int: 每个规则最多允许N个失败
        - float: 每个规则最多允许N%失败率
    :param fast_fail: 快速失败，默认True
    :param output_format: 校验结果输出格式：summary/detail/dict
    :return: ValidationResult: 当校验成功时返回校验结果对象
    :raises: ValidationError: 当校验失败时抛出异常
    :raises: Exception: 当参数错误或数据结构异常时抛出异常
    
    示例：
    try:
        users = [{"name": "张三", "status": "active", "score": 85}, ...]
        result = validate_list_when(users, "status == 'active'", "score > 70")
        print(f"列表条件校验成功: {result}")
    except ValidationError as e:
        print(f"列表条件校验失败: {str(e)}")
    """
    # 参数验证
    if not isinstance(data_list, list):
        raise TypeError(f"data_list必须是列表，当前类型: {type(data_list)}")

    if not then:
        raise ValueError("至少需要提供一个then校验规则")

    log_info(f"开始列表逐项条件校验 - 列表长度: {len(data_list)}, then规则数: {len(then)}")
    log_debug(f"校验规则: validate_list_when({condition}) then({', '.join(str(rule) for rule in then)})")
    log_debug(f"失败阈值: {'默认严格模式' if max_fail is None else max_fail}")

    try:
        return perform_item_wise_conditional_check(data_list, condition, then, max_fail, fast_fail, is_bool_mode=False, output_format=output_format)
    except ValidationError as e:
        log_error(f"❌ 列表逐项条件校验失败: validate_list_when({condition}) - '{str(e)}'")
        raise
    except Exception as e:
        log_error(f"❌ 列表逐项条件校验出现异常: validate_list_when({condition}) - '{str(e)}'")
        raise


def validate_list(data_list, *validations, max_fail=None, fast_fail=True, output_format="summary", **named_validations) -> ValidationResult:
    """
    列表数据批量校验

    :param data_list: 数据列表
    :param validations: 字段校验规则（默认非空校验，同时支持符号表达式校验和字典格式参数校验）
    :param max_fail: 失败阈值
        - None: 严格模式，一个失败全部失败（默认）
        - int: 每个规则最多允许N个失败
        - float: 每个规则最多允许N%失败率
    :param fast_fail: 快速失败，默认True
    :param output_format: 校验结果输出格式：summary/detail/dict
    :param named_validations: 具名字段校验规则 field_name="validator expression"}
    :return: ValidationResult: 当校验成功时返回校验结果对象
    :raises: ValidationError: 当校验失败时抛出异常
    :raises: Exception: 当参数错误或数据结构异常时抛出异常
    
    示例：
    try:
        result = validate_list(products, "id", "name", "price > 0", max_fail=2)
        print(f"列表校验成功: {result}")
    except ValidationError as e:
        print(f"列表校验失败: {str(e)}")
        # 查看具体哪些商品的哪些字段失败了
    """
    total_fields = len(validations) + len(named_validations)
    log_info(f"列表数据批量校验 - 列表长度: {len(data_list) if isinstance(data_list, list) else '未知'}, 字段数: {total_fields}")
    log_debug(f"非空校验字段: {list(validations)}")
    log_debug(f"带校验器字段: {dict(named_validations)}")
    
    if not isinstance(data_list, list):
        raise TypeError(f"data_list必须是列表，当前类型: {type(data_list)}")
    
    # 构建校验规则
    rules = []
    # 默认非空校验的字段
    for field in validations:
        rules.append(f"*.{field}")
    # 带校验器的字段
    for field, validator_expr in named_validations.items():
        rules.append(f"*.{field} {validator_expr}")
    
    # 调用核心 validate 函数
    return validate(data_list, *rules, max_fail=max_fail, fast_fail=fast_fail, output_format=output_format)


def validate_nested(data, list_field, nested_field, *validations, max_fail=None, fast_fail=True, output_format="summary") -> ValidationResult:
    """
    嵌套列表数据批量校验

    :param data: 要校验的数据
    :param list_field: 列表路径
    :param nested_field: 嵌套对象字段名，支持列表或字典对象
    :param validations: 字段校验规则
    :param max_fail: 失败阈值
        - None: 严格模式，一个失败全部失败（默认）
        - int: 每个规则最多允许N个失败
        - float: 每个规则最多允许N%失败率
    :param fast_fail: 快速失败，默认True
    :param output_format: 校验结果输出格式：summary/detail/dict
    :return: ValidationResult: 当校验成功时返回校验结果对象
    :raises: ValidationError: 当校验失败时抛出异常
    :raises: Exception: 当参数错误或数据结构异常时抛出异常
    
    示例：
    try:
        result = validate_nested(response, "data.productList", "purchasePlan", "id > 0", "amount >= 100")
        print(f"嵌套列表校验成功: {result}")
    except ValidationError as e:
        print(f"嵌套列表校验失败: {str(e)}")
    """
    log_info(f"嵌套列表数据批量校验 - 路径: {list_field}.*.{nested_field}, 字段数: {len(validations)}")
    log_debug(f"列表路径: {list_field}")
    log_debug(f"嵌套对象路径: {nested_field}")
    log_debug(f"字段校验规则: {list(validations)}")
    
    main_list = get_nested_value(data, list_field)
    if isinstance(main_list, list) and len(main_list) > 0:
        nested_obj = main_list[0].get(nested_field)
        if not nested_obj:
            raise ValueError(f"validate_nested校验时嵌套对象 {nested_field} 不存在或为空")
    else:
        raise ValueError(f"validate_nested校验时列表路径 {list_field} 的值不是列表或为空列表")

    # 构建校验规则
    rules = []
    for validation in validations:
        if isinstance(nested_obj, list):
            rules.append(f"{list_field}.*.{nested_field}.*.{validation}")
        elif isinstance(nested_obj, dict):
            rules.append(f"{list_field}.*.{nested_field}.{validation}")
        else:
            raise ValueError(f"validate_nested校验时嵌套对象 {nested_field} 不是列表或字典")

    return validate(data, *rules, max_fail=max_fail, fast_fail=fast_fail, output_format=output_format)


class DataValidator(BaseValidator):
    """数据校验器 - 链式调用并返回详细结果"""
    
    def validate(self, max_fail=None, fast_fail=True, output_format="summary") -> ValidationResult:
        """
        执行校验并返回详细结果
        
        :param max_fail: 失败阈值
            - None: 严格模式，一个失败全部失败（默认）
            - int: 每个规则最多允许N个失败
            - float: 每个规则最多允许N%失败率
        :param fast_fail: 快速失败，默认True
        :param output_format: 校验结果输出格式：summary/detail/dict
        :return: ValidationResult 对象，包含详细校验信息
        :raises: ValidationError: 当校验失败时抛出，包含完整失败详情
        :raises: Exception: 当参数错误或数据结构异常时抛出异常
        
        示例：
        try:
            result = validator(data)\
                .not_empty("field1", "field2")\
                .greater_than("field3", 0)\
                .validate(max_fail=0.1)
            print(f"链式校验成功: {result.summary}")
        except ValidationError as e:
            print(f"链式校验失败: {str(e)}")
        """
        return validate(self.data, *self.rules, max_fail=max_fail, fast_fail=fast_fail, output_format=output_format)


def validator(data):
    """创建数据校验器 - 增强版，支持详细结果返回"""
    return DataValidator(data)