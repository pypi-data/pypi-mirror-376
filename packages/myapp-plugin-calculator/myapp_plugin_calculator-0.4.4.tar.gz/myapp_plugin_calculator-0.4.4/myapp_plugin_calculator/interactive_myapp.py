#!/usr/bin/env python3
"""
MyApp 交互模式
"""
import sys
import re
from myapp.core import MyApp

def main():
    print("=== MyApp 交互模式 ===")
    print("直接输入算式即可计算！")
    print("示例: 5 + 3 =  或  10 减 4 =  或  8 除 2 加 3 =")
    print("输入 'quit' 退出")
    print("输入 '/help' 查看帮助")
    print()
    
    app = MyApp()
    
    while True:
        try:
            user_input = input("myapp> ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("再见！")
                break
            
            if not user_input:
                continue
            
            # 检查是否为特殊命令
            if user_input.startswith('/'):
                plugin = app.plugin_manager.get_plugin('calculator')
                if plugin:
                    result = plugin.execute(user_input)
                    print(f"结果: {result}")
                else:
                    print("❌ 计算器插件未找到")
                continue
            
            # 检查是否为算式（包含数字和运算符，以等于号结尾）
            if re.search(r'[\d+\-*/.]', user_input) and ('=' in user_input or '等于' in user_input):
                # 使用计算器插件
                plugin = app.plugin_manager.get_plugin('calculator')
                if plugin:
                    result = plugin.execute(user_input)
                    print(f"结果: {result}")
                else:
                    print("❌ 计算器插件未找到")
                continue
            
            # 检查是否为科学计算
            if any(func in user_input.lower() for func in ['sin', 'cos', 'tan', 'log', 'sqrt', 'ln']):
                plugin = app.plugin_manager.get_plugin('calculator')
                if plugin:
                    # 移除等号和"等于"后再处理
                    cleaned_input = user_input.replace('=', '').replace('等于', '').strip()
                    result = plugin.execute(cleaned_input)
                    print(f"结果: {result}")
                else:
                    print("❌ 计算器插件未找到")
                continue
            
            # 默认使用hello插件
            plugin = app.plugin_manager.get_plugin('hello')
            if plugin:
                result = plugin.execute(user_input)
                print(f"结果: {result}")
            else:
                print("❌ hello插件未找到")
                
        except KeyboardInterrupt:
            print("\n再见！")
            break
        except Exception as e:
            print(f"错误: {e}")

if __name__ == "__main__":
    main()