#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UVX入口点 - 支持命令行参数
"""

import sys
import argparse
from .server import start_server

def main():
    """主入口函数，支持uvx调用"""
    parser = argparse.ArgumentParser(description="阿里云百炼MCP服务器")
    parser.add_argument("--transport", default="http", help="传输协议")
    parser.add_argument("--host", default="0.0.0.0", help="监听地址")
    parser.add_argument("--port", type=int, default=8001, help="监听端口")
    
    args = parser.parse_args()
    
    # 启动服务器
    start_server(
        transport=args.transport,
        host=args.host,
        port=args.port
    )

if __name__ == "__main__":
    main()
