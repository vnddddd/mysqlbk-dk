# 多数据库配置示例

本文档提供了各种多数据库备份配置的详细示例。

## 🔧 配置格式

### 1. 简单多服务器配置（分号分隔）

适用于简单的多服务器备份需求：

```bash
# 生产环境和测试环境
MYSQL_CONNECTIONS="mysql://prod_user:prod_pass@prod.db.com:3306/proddb;mysql://test_user:test_pass@test.db.com:3306/testdb"

# 不同云服务商的数据库
MYSQL_CONNECTIONS="mysql://aws_user:aws_pass@aws-rds.amazonaws.com:3306/awsdb;mysql://gcp_user:gcp_pass@gcp-sql.googleapis.com:3306/gcpdb"
```

### 2. JSON格式配置（推荐）

适用于复杂的多环境备份需求：

```json
[
  {
    "name": "Production-Main",
    "connection": "mysql://prod_user:prod_pass@prod-main.db.com:3306/maindb",
    "schedule": "0 2 * * *",
    "retention_days": 30,
    "enabled": true
  },
  {
    "name": "Production-Analytics", 
    "connection": "mysql://analytics_user:analytics_pass@analytics.db.com:3306/analytics",
    "schedule": "0 3 * * *",
    "retention_days": 90,
    "enabled": true
  },
  {
    "name": "Staging",
    "connection": "mysql://staging_user:staging_pass@staging.db.com:3306/stagingdb",
    "schedule": "0 6 * * *",
    "retention_days": 7,
    "enabled": true
  },
  {
    "name": "Development",
    "connection": "mysql://dev_user:dev_pass@dev.db.com:3306/devdb",
    "schedule": "0 12 * * *",
    "retention_days": 3,
    "enabled": false
  }
]
```

## 🏢 实际使用场景

### 场景1: 微服务架构

每个微服务有独立的数据库：

```json
[
  {
    "name": "UserService",
    "connection": "mysql://user_svc:password@user-db.internal:3306/users",
    "schedule": "0 1 * * *",
    "retention_days": 30
  },
  {
    "name": "OrderService", 
    "connection": "mysql://order_svc:password@order-db.internal:3306/orders",
    "schedule": "0 2 * * *",
    "retention_days": 90
  },
  {
    "name": "PaymentService",
    "connection": "mysql://payment_svc:password@payment-db.internal:3306/payments",
    "schedule": "0 3 * * *",
    "retention_days": 365
  }
]
```

### 场景2: 多环境部署

开发、测试、生产环境：

```json
[
  {
    "name": "Production",
    "connection": "mysql://prod_admin:secure_pass@prod-cluster.db.com:3306/app_prod",
    "schedule": "0 2 * * *",
    "retention_days": 30,
    "enabled": true
  },
  {
    "name": "Staging",
    "connection": "mysql://staging_admin:staging_pass@staging.db.com:3306/app_staging", 
    "schedule": "0 4 * * *",
    "retention_days": 14,
    "enabled": true
  },
  {
    "name": "Development",
    "connection": "mysql://dev_admin:dev_pass@dev.db.com:3306/app_dev",
    "schedule": "0 6 * * 1-5",
    "retention_days": 7,
    "enabled": false
  }
]
```

### 场景3: 多租户SaaS应用

每个租户有独立的数据库：

```json
[
  {
    "name": "Tenant-CompanyA",
    "connection": "mysql://tenant_user:tenant_pass@tenant-db.com:3306/company_a_db",
    "schedule": "0 1 * * *",
    "retention_days": 60
  },
  {
    "name": "Tenant-CompanyB",
    "connection": "mysql://tenant_user:tenant_pass@tenant-db.com:3306/company_b_db", 
    "schedule": "0 2 * * *",
    "retention_days": 60
  },
  {
    "name": "Tenant-CompanyC",
    "connection": "mysql://tenant_user:tenant_pass@tenant-db.com:3306/company_c_db",
    "schedule": "0 3 * * *", 
    "retention_days": 60
  }
]
```

### 场景4: 混合云部署

跨云服务商的数据库备份：

```json
[
  {
    "name": "AWS-Primary",
    "connection": "mysql://aws_user:aws_pass@prod.cluster-xyz.us-east-1.rds.amazonaws.com:3306/maindb",
    "schedule": "0 2 * * *",
    "retention_days": 30
  },
  {
    "name": "GCP-Analytics",
    "connection": "mysql://gcp_user:gcp_pass@analytics-db.sql.gcp.internal:3306/analytics?ssl-mode=REQUIRED",
    "schedule": "0 3 * * *", 
    "retention_days": 90
  },
  {
    "name": "Azure-Backup",
    "connection": "mysql://azure_user:azure_pass@backup-db.mysql.database.azure.com:3306/backup?ssl-mode=REQUIRED",
    "schedule": "0 4 * * *",
    "retention_days": 180
  }
]
```

## ⚙️ 配置字段说明

### 必需字段

- `name`: 连接组名称，用于标识和日志记录
- `connection`: MySQL连接字符串

### 可选字段

- `schedule`: 自定义备份调度（Cron表达式）
  - 如果不指定，使用全局的 `BACKUP_SCHEDULE`
  - 格式：`分 时 日 月 周`
  
- `retention_days`: 自定义保留天数
  - 如果不指定，使用全局的 `RETENTION_DAYS`
  - 数值类型，表示保留天数
  
- `enabled`: 是否启用此连接
  - 默认值：`true`
  - 设置为 `false` 可以临时禁用某个连接

### 自定义字段

可以添加任何自定义字段，系统会自动添加 `custom_` 前缀：

```json
{
  "name": "Production",
  "connection": "mysql://...",
  "priority": "high",
  "team": "backend",
  "environment": "production"
}
```

这些字段会被存储为：
- `custom_priority`: "high"
- `custom_team": "backend"
- `custom_environment": "production"

## 🔍 监控和管理

### 查看连接状态

```bash
# 查看所有连接组状态
curl http://localhost:8080/status

# 响应示例
{
  "connection_groups": {
    "Production": {
      "connection_count": 1,
      "databases": ["maindb"],
      "hosts": ["prod.db.com:3306"]
    },
    "Staging": {
      "connection_count": 2, 
      "databases": ["stagingdb", "testdb"],
      "hosts": ["staging.db.com:3306"]
    }
  }
}
```

### 备份结果查看

备份完成后，结果会按组分类：

```json
{
  "groups": {
    "Production": {
      "success_count": 1,
      "error_count": 0,
      "total_size": 1048576,
      "databases": [...]
    },
    "Staging": {
      "success_count": 1,
      "error_count": 1, 
      "total_size": 524288,
      "databases": [...]
    }
  }
}
```

## 🚨 注意事项

1. **JSON格式验证**：确保JSON格式正确，可以使用在线JSON验证器
2. **连接字符串安全**：避免在日志中暴露密码
3. **调度冲突**：避免多个大型数据库同时备份
4. **网络连接**：确保备份服务器能访问所有目标数据库
5. **权限管理**：为每个数据库创建专用的备份用户

## 🔧 故障排除

### 常见问题

1. **JSON解析错误**
   - 检查JSON格式是否正确
   - 确保所有字符串都用双引号包围
   - 检查是否有多余的逗号

2. **连接失败**
   - 验证数据库连接字符串
   - 检查网络连接和防火墙设置
   - 确认数据库用户权限

3. **部分备份失败**
   - 查看详细日志确定失败原因
   - 检查特定数据库的连接配置
   - 验证磁盘空间和网络状况

### 调试技巧

```bash
# 测试连接解析
python -c "
from src.database_parser import DatabaseConnectionParser
connections = DatabaseConnectionParser.parse_connections('你的配置字符串')
for conn in connections:
    print(DatabaseConnectionParser.get_connection_info(conn))
"

# 手动触发备份测试
curl -X POST http://localhost:8080/backup/run
```
