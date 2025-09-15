"""
NagaAgent_core 命令行接口
"""

import argparse
import sys
import asyncio
import logging
from typing import Optional

def main():
    """主入口函数"""
    parser = argparse.ArgumentParser(
        description="NagaAgent_core - 娜迦AI助手核心功能包",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  NagaAgent-core --version                    # 显示版本信息
  NagaAgent-core --help                       # 显示帮助信息
        """
    )
    
    parser.add_argument(
        "--version",
        action="version",
        version="NagaAgent_core 1.0.0"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="启用详细输出"
    )
    
    # 子命令
    subparsers = parser.add_subparsers(dest="command", help="可用命令")
    
    # 测试命令
    test_parser = subparsers.add_parser("test", help="测试核心功能")
    test_parser.add_argument(
        "--component",
        choices=["streaming", "mcp", "messages", "tools", "all"],
        default="all",
        help="要测试的组件"
    )
    
    # 信息命令
    info_parser = subparsers.add_parser("info", help="显示包信息")
    
    args = parser.parse_args()
    
    # 设置日志级别
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)
    
    # 执行命令
    if args.command == "test":
        asyncio.run(run_tests(args.component))
    elif args.command == "info":
        show_info()
    else:
        parser.print_help()

async def run_tests(component: str):
    """运行测试"""
    print(f"测试组件: {component}")
    
    try:
        if component in ["streaming", "all"]:
            print("测试流式工具调用...")
            from NagaAgent_core.streaming import StreamingToolCallExtractor
            extractor = StreamingToolCallExtractor()
            print("✓ 流式工具调用提取器创建成功")
        
        if component in ["mcp", "all"]:
            print("测试MCP管理器...")
            from NagaAgent_core.mcp import MCPManager
            manager = MCPManager()
            print("✓ MCP管理器创建成功")
        
        if component in ["messages", "all"]:
            print("测试消息管理器...")
            from NagaAgent_core.messages import MessageManager
            msg_manager = MessageManager()
            session_id = msg_manager.create_session()
            print(f"✓ 消息管理器创建成功，会话ID: {session_id}")
        
        if component in ["tools", "all"]:
            print("测试工具调用解析器...")
            from NagaAgent_core.tools import parse_tool_calls
            test_content = '{"tool_name": "test_tool", "args": {"param": "value"}}'
            tool_calls = parse_tool_calls(test_content)
            print(f"✓ 工具调用解析成功，解析到 {len(tool_calls)} 个工具调用")
        
        print("所有测试通过！")
        
    except Exception as e:
        print(f"测试失败: {e}")
        sys.exit(1)

def show_info():
    """显示包信息"""
    print("NagaAgent_core - 娜迦AI助手核心功能包")
    print("版本: 1.0.0")
    print("作者: NagaAgent Team")
    print()
    print("包含的核心模块:")
    print("- 流式工具调用处理")
    print("- MCP服务管理")
    print("- 消息和会话管理")
    print("- 工具调用解析和执行")
    print()
    print("更多信息请访问: https://github.com/naga-agent/NagaAgent-core")

if __name__ == "__main__":
    main()
