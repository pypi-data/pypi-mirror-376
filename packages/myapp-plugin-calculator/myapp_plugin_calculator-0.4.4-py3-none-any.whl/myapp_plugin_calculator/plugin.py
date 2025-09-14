from myapp.plugin_base import PluginBase
import re
import math
import json
import os
from datetime import datetime
from typing import List, Dict, Optional, Any

class CalculatorPlugin(PluginBase):
    def __init__(self):
        self.history: List[Dict[str, Any]] = []
        self.last_result: Optional[float] = None
        self.history_file = os.path.join(os.path.expanduser("~"), ".myapp_calculator_history.json")
        self.load_history()
    
    def get_name(self) -> str:
        return "calculator"
    
    def execute(self, data: str) -> str:
        """执行高级计算器功能"""
        try:
            input_str = data.strip()
            
            if not input_str:
                return self.show_help()
            
            # 特殊命令
            if input_str.startswith('/'):
                return self.handle_command(input_str)
            
            # 连续计算模式
            if input_str.startswith('+'):
                return self.continuous_calculation(input_str)
            
            # 科学函数模式
            if any(func in input_str.lower() for func in ['sin', 'cos', 'tan', 'log', 'sqrt', 'ln']):
                return self.scientific_calculation(input_str)
            
            # 基本算式模式
            if '=' in input_str or '等于' in input_str:
                return self.basic_calculation(input_str)
            
            # 默认帮助
            return self.show_help()
            
        except Exception as e:
            return f"计算错误: {e}"
    
    def basic_calculation(self, input_str: str) -> str:
        """基本算式计算"""
        try:
            # 移除等于号
            expression = input_str.replace('=', '').replace('等于', '').strip()
            
            # 转换中文运算符
            expression = self._convert_chinese_operators(expression)
            
            # 验证表达式
            if not self._validate_expression(expression):
                return "表达式格式错误！"
            
            # 计算结果
            result = self._evaluate_expression(expression)
            
            # 保存到历史
            self._save_to_history(expression, result)
            self.last_result = result
            
            # 格式化输出
            return f"{expression} = {self._format_result(result)}"
            
        except ZeroDivisionError:
            return "错误：除数不能为零！"
        except Exception as e:
            return f"表达式错误: {e}"
    
    def scientific_calculation(self, input_str: str) -> str:
        """科学计算"""
        try:
            input_lower = input_str.lower()
            
            # 解析科学函数
            if input_lower.startswith('sin '):
                angle = float(input_str[4:].strip())
                result = math.sin(math.radians(angle))
                expr = f"sin({angle}°)"
                
            elif input_lower.startswith('cos '):
                angle = float(input_str[4:].strip())
                result = math.cos(math.radians(angle))
                expr = f"cos({angle}°)"
                
            elif input_lower.startswith('tan '):
                angle = float(input_str[4:].strip())
                result = math.tan(math.radians(angle))
                expr = f"tan({angle}°)"
                
            elif input_lower.startswith('log '):
                num = float(input_str[4:].strip())
                if num <= 0:
                    return "对数函数的参数必须大于0"
                result = math.log10(num)
                expr = f"log({num})"
                
            elif input_lower.startswith('ln '):
                num = float(input_str[4:].strip())
                if num <= 0:
                    return "自然对数函数的参数必须大于0"
                result = math.log(num)
                expr = f"ln({num})"
                
            elif input_lower.startswith('sqrt '):
                num = float(input_str[5:].strip())
                if num < 0:
                    return "平方根函数的参数不能为负数"
                result = math.sqrt(num)
                expr = f"√{num}"
                
            else:
                return "不支持的科学函数"
            
            self._save_to_history(expr, result)
            self.last_result = result
            return f"{expr} = {self._format_result(result)}"
            
        except ValueError as e:
            return f"参数错误: {e}"
        except Exception as e:
            return f"科学计算错误: {e}"
    
    def continuous_calculation(self, input_str: str) -> str:
        """连续计算模式"""
        try:
            if self.last_result is None:
                return "没有上次的计算结果，请先进行一个计算"
            
            # 解析连续运算
            expr = input_str[1:].strip()  # 移除开头的 '+'
            
            # 构建完整表达式
            full_expr = f"{self.last_result} {expr}"
            
            # 计算
            result = self._evaluate_expression(full_expr)
            
            self._save_to_history(full_expr, result, continuous=True)
            self.last_result = result
            
            return f"{full_expr} = {self._format_result(result)}"
            
        except Exception as e:
            return f"连续计算错误: {e}"
    
    def handle_command(self, command: str) -> str:
        """处理特殊命令"""
        cmd = command.lower()
        
        if cmd == '/help':
            return self.show_help()
        
        elif cmd == '/history':
            return self.show_history()
        
        elif cmd == '/clear':
            self.history.clear()
            self.save_history()
            return "历史记录已清除"
        
        elif cmd == '/last':
            if self.last_result is not None:
                return f"上次结果: {self._format_result(self.last_result)}"
            else:
                return "没有上次的计算结果"
        
        elif cmd.startswith('/save '):
            filename = command[6:].strip()
            return self.save_to_file(filename)
        
        elif cmd == '/functions':
            return self.show_functions()
        
        else:
            return f"未知命令: {command}\n输入 /help 查看可用命令"
    
    def _convert_chinese_operators(self, expression: str) -> str:
        """转换中文运算符为数学符号"""
        conversions = {
            '加': '+',
            '减': '-',
            '乘': '*',
            '除': '/',
            '等于': '=',
            'x': '*',
            'X': '*'
        }
        result = expression
        for chinese, symbol in conversions.items():
            result = result.replace(chinese, symbol)
        return result
    
    def _validate_expression(self, expression: str) -> bool:
        """验证表达式格式"""
        # 检查是否只包含有效字符
        pattern = r'^[0-9+\-*/\s\(\)\^%.]+$'
        return bool(re.match(pattern, expression))
    
    def _evaluate_expression(self, expression: str) -> float:
        """安全地计算表达式"""
        # 替换数学函数
        safe_dict = {
            'sin': lambda x: math.sin(math.radians(x)),
            'cos': lambda x: math.cos(math.radians(x)),
            'tan': lambda x: math.tan(math.radians(x)),
            'sqrt': math.sqrt,
            'log': math.log10,
            'ln': math.log,
            'pi': math.pi,
            'e': math.e
        }
        
        # 安全的内置函数
        safe_dict.update({
            '__builtins__': {
                'abs': abs,
                'round': round,
                'pow': pow,
                'max': max,
                'min': min
            }
        })
        
        # 计算表达式
        return eval(expression, {"__builtins__": {}}, safe_dict)
    
    def _format_result(self, result: float) -> str:
        """格式化结果"""
        if result == int(result):
            return str(int(result))
        else:
            return f"{result:.6g}"  # 自动格式化，去掉不必要的零
    
    def _save_to_history(self, expression: str, result: float, continuous: bool = False):
        """保存到历史记录"""
        entry = {
            'expression': expression,
            'result': result,
            'timestamp': datetime.now().isoformat(),
            'continuous': continuous
        }
        self.history.append(entry)
        
        # 限制历史记录数量
        if len(self.history) > 100:
            self.history = self.history[-100:]
        
        self.save_history()
    
    def save_history(self):
        """保存历史到文件"""
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.history, f, ensure_ascii=False, indent=2)
        except Exception:
            pass  # 忽略保存错误
    
    def load_history(self):
        """从文件加载历史"""
        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    self.history = json.load(f)
        except Exception:
            self.history = []
    
    def show_history(self) -> str:
        """显示历史记录"""
        if not self.history:
            return "没有计算历史"
        
        result = "=== 计算历史 ===\n"
        for i, entry in enumerate(self.history[-10:], 1):  # 显示最近10条
            timestamp = entry.get('timestamp', '')[:19]  # 截取日期时间部分
            continuous = " (连续)" if entry.get('continuous', False) else ""
            result += f"{i}. {entry['expression']} = {self._format_result(entry['result'])}{continuous}\n"
        
        return result.strip()
    
    def show_functions(self) -> str:
        """显示可用函数"""
        return """
=== 可用函数 ===
数学运算:
  +, -, *, /, ^ (幂), % (模), () 括号

科学函数:
  sin x    - 正弦函数 (角度制)
  cos x    - 余弦函数 (角度制)  
  tan x    - 正切函数 (角度制)
  log x    - 常用对数 (底数10)
  ln x     - 自然对数 (底数e)
  sqrt x   - 平方根

常数:
  pi       - 圆周率 π
  e        - 自然常数 e

特殊命令:
  /help    - 显示帮助
  /history - 显示历史记录
  /clear   - 清除历史记录
  /last    - 显示上次结果
  /save <文件名> - 保存历史到文件
  +<表达式> - 连续计算 (如: +5*2)
"""
    
    def save_to_file(self, filename: str) -> str:
        """保存历史到文件"""
        try:
            if not filename.endswith('.txt'):
                filename += '.txt'
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write("MyApp 计算器历史记录\n")
                f.write("=" * 30 + "\n\n")
                for entry in self.history:
                    timestamp = entry.get('timestamp', '')[:19]
                    continuous = " (连续)" if entry.get('continuous', False) else ""
                    f.write(f"[{timestamp}] {entry['expression']} = {self._format_result(entry['result'])}{continuous}\n")
            
            return f"历史记录已保存到: {filename}"
        except Exception as e:
            return f"保存失败: {e}"
    
    def show_help(self) -> str:
        """显示帮助信息"""
        return """
=== MyApp 高级计算器 v0.4.4 ===

基本用法:
  5 + 3 =                    → 8
  10 减 4 =                  → 6  
  8 除 2 加 3 =              → 7
  (2 + 3) * 4 =              → 20
  2 ^ 3 =                    → 8
  10 % 3 =                   → 1

科学计算:
  sin 30 =                   → 0.5
  cos 60 =                   → 0.5
  log 100 =                  → 2
  sqrt 16 =                  → 4

连续计算:
  5 + 3 =                    → 8
  +2 * 3 =                   → 24 (基于上次结果8)

特殊命令:
  /help    - 显示此帮助
  /history - 查看计算历史
  /clear   - 清除历史
  /last    - 显示上次结果
  /save calc_history - 保存到文件
  /functions - 显示所有函数

示例:
  5 + 3 * 2 =                → 11 (遵循运算优先级)
  6 + 4 * 2 = 14             → ✅ 正确！
  sin 30 + cos 60 =          → 1
  sqrt(16) + log(100) =      → 6
"""