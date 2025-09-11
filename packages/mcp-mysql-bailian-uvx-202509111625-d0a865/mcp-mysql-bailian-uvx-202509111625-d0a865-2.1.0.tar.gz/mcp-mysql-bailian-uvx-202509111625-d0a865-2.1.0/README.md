# mcp-mysql-bailian-uvx-202509111625-d0a865

阿里云百炼MCP服务器 - MySQL业务查询服务 (UVX兼容版)

## 特性

- 🚀 完全兼容 uvx 调用
- 🔧 支持阿里云百炼平台
- 🗄️ MySQL跨数据库查询
- 📊 中文字段名返回

## 安装

```bash
pip install mcp-mysql-bailian-uvx-202509111625-d0a865
```

## UVX使用 (推荐)

```bash
uvx mcp-mysql-bailian-uvx-202509111625-d0a865 --transport http --host 0.0.0.0 --port 8001
```

## 直接使用

```bash
mcp-mysql-bailian-uvx-202509111625-d0a865
```

## 阿里云百炼配置

```json
{
  "mcpServers": {
    "licai_mysql_mcp": {
      "type": "http",
      "command": "uvx",
      "args": [
        "mcp-mysql-bailian-uvx-202509111625-d0a865",
        "--transport", "http",
        "--host", "0.0.0.0",
        "--port", "8001"
      ],
      "env": {
        "MYSQL_HOST": "your-host",
        "MYSQL_PORT": "3306",
        "MYSQL_USER": "your-user",
        "MYSQL_PASSWORD": "your-password",
        "MYSQL_DATABASES": "db1,db2"
      }
    }
  }
}
```

## 业务工具

- get_user_info - 用户信息
- get_user_courses - 用户课程
- get_user_cases - 案例分析
- get_user_orders - 订单信息
- get_user_invoices - 发票信息
- get_user_study_plans - 学习计划
- get_course_study_plans - 课程计划
- health_check - 健康检查

## 许可证

MIT License
