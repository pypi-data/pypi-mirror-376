# MCP MySQL Server (理财-CZG版)

一个支持跨数据库查询和中文字段映射的MySQL MCP服务器。

## 🚀 特性

- ✅ **跨数据库查询支持** - 支持多个MySQL数据库的联合查询
- ✅ **中文字段映射** - 返回数据包含中文字段说明，前端更易理解
- ✅ **真实业务SQL** - 基于实际业务需求设计的查询接口
- ✅ **安全连接** - 支持SSL和安全的数据库连接
- ✅ **灵活配置** - 通过环境变量轻松配置多个数据库

## 📦 安装

```bash
pip install mcp-mysql-server-licai-czg
```

## 🛠️ 配置

### 1. MCP客户端配置

在你的MCP客户端配置文件中添加：

```json
{
  "mcpServers": {
    "mysql-server": {
      "command": "mcp-mysql-server-licai-czg",
      "env": {
        "MYSQL_HOST": "your-mysql-host",
        "MYSQL_PORT": "3306",
        "MYSQL_USER": "your-username",
        "MYSQL_PASSWORD": "your-password",
        "MYSQL_DATABASES": "database1,database2"
      }
    }
  }
}
```

### 2. 环境变量

| 变量名 | 描述 | 默认值 |
|--------|------|--------|
| `MYSQL_HOST` | MySQL服务器地址 | `localhost` |
| `MYSQL_PORT` | MySQL端口 | `3306` |
| `MYSQL_USER` | 数据库用户名 | `root` |
| `MYSQL_PASSWORD` | 数据库密码 | `` |
| `MYSQL_DATABASES` | 数据库列表(逗号分隔) | `` |

## 🔧 可用工具

### 1. 用户查询工具

- **get_user_info_by_mobile** - 根据手机号查询用户信息
- **get_user_info_by_nickname** - 根据用户名查询用户信息

### 2. 业务数据工具

- **get_user_courses** - 查询用户课程信息
- **get_user_cases** - 查询用户案例信息
- **get_user_orders** - 查询用户订单信息
- **get_user_invoices** - 查询用户发票信息

### 3. 统计分析工具

- **get_user_study_plan_stats** - 查询用户学习计划统计数据

## 📊 返回数据格式

所有工具返回的数据都包含中文字段说明：

```json
{
  "用户ID": 123456,
  "用户昵称": "张三",
  "注册日期": "2024-01-01",
  "手机状态": 1,
  "手机区号": "+86"
}
```

## 🗄️ 数据库支持

### 跨数据库查询

支持在单个查询中访问多个数据库：

```sql
SELECT 
    u.userId as 用户ID,
    u.nickname as 用户昵称
FROM sso.sso_user_new u
LEFT JOIN dpt_e-commerce.orders o ON o.userid = u.userId
WHERE u.mobile = %s
```

### 支持的数据库类型

- MySQL 5.7+
- MySQL 8.0+
- MariaDB 10.3+

## 🔒 安全性

- 支持SSL连接
- 参数化查询防止SQL注入
- 敏感信息通过环境变量配置
- 连接池管理

## 📝 开发

### 本地开发

```bash
# 克隆项目
git clone https://github.com/yourusername/mcp-mysql-business-server.git
cd mcp-mysql-business-server

# 安装依赖
pip install -r requirements.txt

# 运行测试
python -m pytest tests/

# 本地安装
pip install -e .
```

### 构建发布

```bash
# 构建包
python setup.py sdist bdist_wheel

# 上传到PyPI
twine upload dist/*
```

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

## 🤝 贡献

欢迎提交Issue和Pull Request！

## 📞 支持

如有问题，请提交Issue或联系：
- Email: your.email@example.com
- GitHub: https://github.com/yourusername/mcp-mysql-business-server

## 🔄 更新日志

### v1.0.0 (2024-09-11)
- 初始版本发布
- 支持跨数据库查询
- 中文字段映射
- 7个业务查询工具
- 完整的MCP协议支持