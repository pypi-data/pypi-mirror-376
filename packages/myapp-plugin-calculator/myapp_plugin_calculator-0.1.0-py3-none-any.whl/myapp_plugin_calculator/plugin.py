from myapp.plugin_base import PluginBase

class CalculatorPlugin(PluginBase):
    def get_name(self) -> str:
        return "calculator"
    
    def execute(self, data):
        """执行计算器功能
        期望输入格式: "数字 运算符 数字 等于号 [结果]"
        例如: "5 + 3 = " 或 "10 - 4 = 6"
        """
        try:
            # 解析输入
            parts = data.strip().split()
            
            if len(parts) < 4:
                return "格式错误！请输入: <数字> <运算符> <数字> <等于号>"
            
            if parts[3] != "=" and parts[3] != "等于":
                return "格式错误！请使用 '=' 或 '等于'"
            
            num1 = float(parts[0])
            operator = parts[1]
            num2 = float(parts[2])
            
            # 执行计算
            if operator == "+" or operator == "加":
                result = num1 + num2
                operation = "加"
            elif operator == "-" or operator == "减":
                result = num1 - num2
                operation = "减"
            elif operator == "*" or operator == "乘" or operator == "x":
                result = num1 * num2
                operation = "乘"
            elif operator == "/" or operator == "除":
                if num2 == 0:
                    return "错误：除数不能为零！"
                result = num1 / num2
                operation = "除"
            else:
                return f"错误：不支持的运算符 '{operator}'。支持: +、-、*、/、加、减、乘、除"
            
            # 检查是否有预期结果
            if len(parts) > 4:
                expected = float(parts[4])
                if abs(result - expected) < 0.0001:  # 处理浮点数精度
                    return f"✅ 正确！{num1} {operation} {num2} = {result}"
                else:
                    return f"❌ 错误！{num1} {operation} {num2} = {result} (你输入的结果是: {expected})"
            else:
                return f"{num1} {operation} {num2} = {result}"
                
        except ValueError as e:
            return f"错误：请输入有效的数字 - {e}"
        except Exception as e:
            return f"计算错误：{e}"
    
    def get_help(self) -> str:
        """获取使用帮助"""
        return """
计算器插件使用说明：
格式：<数字> <运算符> <数字> <等于号> [预期结果]

支持的运算符：
- 加法：+ 或 "加"
- 减法：- 或 "减"  
- 乘法：* 或 "乘" 或 "x"
- 除法：/ 或 "除"

示例：
5 + 3 =
10 减 4 =
2.5 乘 4 =
10 除 2 =
7 + 3 = 10
"""