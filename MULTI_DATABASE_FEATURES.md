# 多数据库备份功能详解

本文档详细介绍MySQL备份系统的多数据库支持功能。

## 🎯 功能概述

系统现在支持备份多个不同地方的数据库，包括：
- 不同服务器上的数据库
- 不同云服务商的数据库
- 微服务架构中的多个数据库
- 多环境部署（开发、测试、生产）
- 多租户SaaS应用的独立数据库

## 🔧 支持的配置格式

### 1. 简单格式（向后兼容）

```bash
# 单个数据库
MYSQL_CONNECTIONS="mysql://user:pass@host:3306/database"

# 同服务器多个数据库
MYSQL_CONNECTIONS="mysql://user:pass@host:3306/db1,db2,db3"
```

### 2. 多服务器格式（新增）

```bash
# 多个不同服务器（分号分隔）
MYSQL_CONNECTIONS="mysql://user1:pass1@host1:3306/db1;mysql://user2:pass2@host2:3306/db2"
```

### 3. JSON配置格式（推荐）

```json
[
  {
    "name": "Production",
    "connection": "mysql://prod_user:prod_pass@prod.db.com:3306/proddb",
    "schedule": "0 2 * * *",
    "retention_days": 30,
    "enabled": true
  },
  {
    "name": "Staging",
    "connection": "mysql://staging_user:staging_pass@staging.db.com:3306/stagingdb",
    "schedule": "0 4 * * *",
    "retention_days": 14,
    "enabled": true
  }
]
```

## 🏗️ 核心功能

### 连接分组管理

- 自动按连接组织数据库
- 支持自定义组名
- 按组显示备份状态和统计

### 独立配置支持

每个连接组可以有独立的：
- 备份调度时间
- 数据保留策略
- 启用/禁用状态
- 自定义标签和元数据

### 智能文件命名

备份文件自动包含组名：
```
backup_[组名]_[数据库名]_[时间戳].sql.gz
```

示例：
- `backup_Production_maindb_20231203_140000.sql.gz`
- `backup_Staging_testdb_20231203_140000.sql.gz`

## 📊 监控和状态

### 分组状态显示

```json
{
  "connection_groups": {
    "Production": {
      "connection_count": 2,
      "databases": ["maindb", "userdb"],
      "hosts": ["prod-db1.com:3306", "prod-db2.com:3306"]
    },
    "Staging": {
      "connection_count": 1,
      "databases": ["stagingdb"],
      "hosts": ["staging-db.com:3306"]
    }
  }
}
```

### 备份结果分组

```json
{
  "groups": {
    "Production": {
      "success_count": 2,
      "error_count": 0,
      "total_size": 2097152,
      "databases": [...]
    },
    "Staging": {
      "success_count": 1,
      "error_count": 0,
      "total_size": 1048576,
      "databases": [...]
    }
  }
}
```

## 🔄 备份流程

### 1. 连接解析
- 解析配置字符串
- 验证连接格式
- 分组和过滤连接

### 2. 按组执行备份
- 按连接组顺序执行
- 记录每组的执行状态
- 生成带组名的备份文件

### 3. 上传和清理
- 上传到B2云存储
- 清理本地临时文件
- 记录详细的执行日志

## 🛠️ 实际使用示例

### 微服务架构

```json
[
  {
    "name": "UserService",
    "connection": "mysql://user_svc:pass@user-db:3306/users",
    "schedule": "0 1 * * *"
  },
  {
    "name": "OrderService",
    "connection": "mysql://order_svc:pass@order-db:3306/orders",
    "schedule": "0 2 * * *"
  },
  {
    "name": "PaymentService",
    "connection": "mysql://payment_svc:pass@payment-db:3306/payments",
    "schedule": "0 3 * * *"
  }
]
```

### 多环境部署

```bash
# 使用分号分隔的简单格式
MYSQL_CONNECTIONS="mysql://prod:pass@prod.db.com:3306/app;mysql://staging:pass@staging.db.com:3306/app;mysql://dev:pass@dev.db.com:3306/app"
```

### 混合云部署

```json
[
  {
    "name": "AWS-Primary",
    "connection": "mysql://aws_user:pass@aws-rds.amazonaws.com:3306/maindb",
    "retention_days": 30
  },
  {
    "name": "GCP-Analytics",
    "connection": "mysql://gcp_user:pass@gcp-sql.googleapis.com:3306/analytics?ssl-mode=REQUIRED",
    "retention_days": 90
  }
]
```

## 🔍 API端点增强

### 状态查询

```bash
# 查看所有连接组状态
curl http://localhost:8080/status

# 响应包含分组信息
{
  "total_database_count": 5,
  "connection_groups": {
    "Production": {...},
    "Staging": {...}
  }
}
```

### 备份结果

```bash
# 手动触发备份
curl -X POST http://localhost:8080/backup/run

# 响应包含分组结果
{
  "groups": {
    "Production": {...},
    "Staging": {...}
  },
  "databases": [...],
  "success_count": 4,
  "error_count": 1
}
```

## 🚀 性能优化

### 并发控制
- 按组顺序执行，避免资源冲突
- 支持大型数据库的错峰备份
- 智能调度避免网络拥塞

### 资源管理
- 临时文件及时清理
- 内存使用优化
- 网络连接复用

## 🔒 安全增强

### 连接信息保护
- 日志中隐藏敏感信息
- 安全的连接信息显示
- 分组标识便于审计

### 权限隔离
- 每个数据库使用独立用户
- 最小权限原则
- 连接失败不影响其他组

## 📈 扩展性

### 水平扩展
- 支持任意数量的数据库
- 支持任意数量的连接组
- 配置文件大小无限制

### 功能扩展
- 自定义字段支持
- 插件化架构预留
- API扩展友好

## 🧪 测试验证

系统包含完整的测试套件：

```bash
# 测试解析器功能
python scripts/test_parser_only.py

# 测试结果
总测试数: 13
通过: 13
失败: 0
成功率: 100.0%
```

测试覆盖：
- 所有连接格式解析
- 分组功能
- 过滤功能
- 错误处理
- 边界条件

## 📚 文档和示例

- `examples/multi-database-config.md` - 详细配置示例
- `.env.example` - 环境变量示例
- `README.md` - 完整使用说明
- `DEPLOYMENT.md` - 部署指南

## 🔄 向后兼容性

- 完全兼容现有的单数据库配置
- 现有的环境变量格式继续有效
- 无需修改现有部署即可升级

## 🎉 总结

多数据库备份功能为MySQL备份系统带来了：

1. **灵活性**: 支持各种复杂的数据库架构
2. **可扩展性**: 轻松添加新的数据库和服务器
3. **可管理性**: 分组管理和独立配置
4. **可观测性**: 详细的状态和日志信息
5. **安全性**: 增强的权限控制和信息保护

这使得系统能够满足从简单的单数据库备份到复杂的企业级多环境、多服务商的备份需求。
