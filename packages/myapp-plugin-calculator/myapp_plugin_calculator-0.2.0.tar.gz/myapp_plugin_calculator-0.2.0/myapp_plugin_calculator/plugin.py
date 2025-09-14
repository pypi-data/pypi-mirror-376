from myapp.plugin_base import PluginBase
import re
from typing import List, Tuple

class CalculatorPlugin(PluginBase):
    def get_name(self) -> str:
        return "calculator"
    
    def execute(self, data):
        """执行复杂计算器功能
        支持连续运算：数字 运算符 数字 运算符 ... 等于号 [结果]
        例如：5 + 3 * 2 =  或  10 - 4 + 1 =  或  8 除 2 加 3 =
        """
        try:
            # 解析输入
            input_str = data.strip()
            
            if not input_str:
                return "请输入计算表达式！"
            
            # 检查是否以等于号结尾
            if not (input_str.endswith('=') or input_str.endswith('等于')):
                return "格式错误！表达式需要以 '=' 或 '等于' 结尾"
            
            # 移除等于号
            expression = input_str[:-1].strip() if input_str.endswith('=') else input_str[:-2].strip()
            
            if not expression:
                return "请输入有效的计算表达式！"
            
            # 将中文运算符转换为符号
            expression = self._convert_chinese_operators(expression)
            
            # 验证表达式格式
            if not self._validate_expression(expression):
                return "格式错误！请使用：数字 运算符 数字 运算符 ... 等于号"
            
            # 解析表达式为token
            tokens = self._parse_expression(expression)
            if not tokens:
                return "无法解析表达式！"
            
            # 计算结果
            result = self._calculate(tokens)
            
            # 格式化原始表达式
            original_expr = self._format_expression(tokens)
            
            # 检查是否有预期结果
            expected_result = self._check_expected_result(input_str, result)
            
            if expected_result is not None:
                if abs(result - expected_result) < 0.0001:
                    return f"✅ 正确！{original_expr} = {result}"
                else:
                    return f"❌ 错误！{original_expr} = {result} (你输入的结果是: {expected_result})"
            else:
                return f"{original_expr} = {result}"
                
        except ZeroDivisionError:
            return "错误：除数不能为零！"
        except ValueError as e:
            return f"错误：请输入有效的数字 - {e}"
        except Exception as e:
            return f"计算错误：{e}"
    
    def _convert_chinese_operators(self, expression: str) -> str:
        """将中文运算符转换为数学符号"""
        conversions = {
            '加': '+',
            '减': '-', 
            '乘': '*',
            '除': '/',
            '等于': '='
        }
        
        result = expression
        for chinese, symbol in conversions.items():
            result = result.replace(chinese, symbol)
        return result
    
    def _validate_expression(self, expression: str) -> bool:
        """验证表达式格式"""
        # 检查是否只包含数字、运算符和空格
        pattern = r'^[0-9+\-*/\s\.]+$'
        return bool(re.match(pattern, expression))
    
    def _parse_expression(self, expression: str) -> List[Tuple[float, str]]:
        """解析表达式为数字和运算符的列表"""
        try:
            # 使用正则表达式分割数字和运算符
            pattern = r'(\d+\.?\d*)\s*([+\-*/])\s*'
            matches = re.findall(pattern, expression)
            
            if not matches:
                return []
            
            # 获取所有数字
            numbers = re.findall(r'\d+\.?\d*', expression)
            if len(numbers) != len(matches) + 1:
                return []
            
            # 构建tokens列表
            tokens = []
            for i, (op, num_str) in enumerate(matches):
                if i == 0:
                    # 第一个数字
                    tokens.append((float(numbers[i]), matches[i][1]))
                tokens.append((float(numbers[i+1]), '' if i == len(matches)-1 else matches[i+1][1]))
            
            return tokens
            
        except Exception:
            return []
    
    def _format_expression(self, tokens: List[Tuple[float, str]]) -> str:
        """格式化表达式用于显示"""
        parts = []
        for i, (num, op) in enumerate(tokens):
            if i == 0:
                parts.append(str(num))
            else:
                if op:
                    parts.extend([op, str(num)])
                else:
                    parts.append(str(num))
        return ' '.join(parts)
    
    def _calculate(self, tokens: List[Tuple[float, str]]) -> float:
        """计算表达式结果"""
        if not tokens:
            return 0
        
        # 第一轮：处理乘除法
        i = 0
        while i < len(tokens) - 1:
            num, op = tokens[i]
            next_num, next_op = tokens[i + 1]
            
            if op in ['*', '/']:
                if op == '*':
                    result = num * next_num
                else:  # op == '/'
                    if next_num == 0:
                        raise ZeroDivisionError("除数不能为零")
                    result = num / next_num
                
                # 替换当前token，移除下一个
                tokens[i] = (result, next_op)
                tokens.pop(i + 1)
                # 不增加i，继续检查当前位置
            else:
                i += 1
        
        # 第二轮：处理加减法
        result = tokens[0][0]
        for i in range(1, len(tokens)):
            num, op = tokens[i]
            prev_num, prev_op = tokens[i-1]
            
            if prev_op == '+':
                result += num
            elif prev_op == '-':
                result -= num
        
        return result
    
    def _check_expected_result(self, input_str: str, calculated_result: float) -> Optional[float]:
        """检查是否有预期结果"""
        # 查找等于号后面的内容
        if '=' in input_str:
            parts = input_str.split('=')
            if len(parts) > 1:
                expected_str = parts[-1].strip()
                if expected_str:
                    try:
                        return float(expected_str)
                    except ValueError:
                        pass
        return None
    
    def get_help(self) -> str:
        """获取使用帮助"""
        return """
高级计算器插件使用说明：
格式：<数字> <运算符> <数字> <运算符> ... <等于号> [预期结果]

支持的运算符：
- 加法：+ 或 "加"
- 减法：- 或 "减"  
- 乘法：* 或 "乘"
- 除法：/ 或 "除"

特性：
✅ 支持连续运算（遵循数学优先级）
✅ 支持中英文运算符混用
✅ 支持结果验证
✅ 自动处理运算优先级（先乘除后加减）

示例：
5 + 3 * 2 =                    → 11.0（先乘除后加减）
10 - 4 + 1 =                   → 7.0
8 除 2 加 3 =                  → 7.0
2.5 乘 4 减 1 =                → 9.0
6 + 4 * 2 = 14                 → ✅ 正确！6 + 4 * 2 = 14
"""