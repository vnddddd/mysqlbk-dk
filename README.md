# MySQL Database Backup System

一个功能完整的MySQL数据库自动备份系统，支持定时备份到Backblaze B2云存储，具有完善的错误处理、日志记录和健康检查功能。

## 🚀 主要特性

- **自动化备份**: 支持Cron表达式的灵活调度，默认每天凌晨4点执行备份
- **云存储**: 自动上传备份到Backblaze B2云存储，无本地文件保留
- **智能清理**: 自动删除超过保留期的备份文件（默认7天）
- **多数据库支持**: 支持同时备份多个数据库
- **多种连接格式**: 支持多种MySQL连接字符串格式
- **健康检查**: 提供HTTP端点进行系统监控
- **Docker部署**: 完整的Docker支持，易于部署和管理
- **错误处理**: 完善的错误处理和日志记录
- **初始验证**: 部署时自动执行初始备份验证系统功能

## 📋 支持的连接格式

系统支持以下MySQL连接字符串格式，可以备份多个不同地方的数据库：

### 1. TCP格式（单个连接）
```
username:password@tcp(host:port)/database
```
示例：
```
myuser:mypass@tcp(mysql.example.com:3306)/mydb
```

### 2. MySQL URL格式（单个连接）
```
mysql://username:password@host:port/database
```
示例：
```
mysql://admin:password@db.example.com:3306/mydb
```

### 3. 同服务器多数据库（逗号分隔）
```
mysql://username:password@host:port/db1,db2,db3
```
示例：
```
mysql://admin:password@db.example.com:3306/db1,db2,db3
```

### 4. 带SSL的MySQL URL
```
mysql://username:password@host:port/database?ssl-mode=REQUIRED
```
示例：
```
mysql://admin:password@secure-db.example.com:3306/mydb?ssl-mode=REQUIRED
```

### 5. 多个不同服务器（分号分隔）
```
mysql://user1:pass1@host1:port1/db1;mysql://user2:pass2@host2:port2/db2
```
示例：
```
mysql://prod_user:prod_pass@prod.db.com:3306/proddb;mysql://staging_user:staging_pass@staging.db.com:3306/stagingdb
```

### 6. JSON格式配置（推荐用于复杂配置）
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
    "name": "Development",
    "connection": "mysql://dev_user:dev_pass@dev.db.com:3306/devdb",
    "schedule": "0 6 * * *",
    "retention_days": 7,
    "enabled": true
  }
]
```

JSON格式支持的字段：
- `name`: 连接组名称
- `connection`: 数据库连接字符串
- `schedule`: 自定义备份调度（可选）
- `retention_days`: 自定义保留天数（可选）
- `enabled`: 是否启用此连接（可选，默认true）

## 🛠️ 快速开始

### 使用Docker Compose（推荐）

1. **克隆仓库**
```bash
git clone https://github.com/yourusername/mysql-backup-system.git
cd mysql-backup-system
```

2. **配置环境变量**
```bash
cp .env.example .env
# 编辑.env文件，填入你的配置信息
```

3. **启动服务**
```bash
docker-compose up -d
```

4. **检查状态**
```bash
# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f

# 健康检查
curl http://localhost:8080/health
```

### 使用Docker

```bash
docker run -d \
  --name mysql-backup \
  -p 8080:8080 \
  -e MYSQL_CONNECTIONS="mysql://user:pass@host:3306/db" \
  -e B2_APPLICATION_KEY_ID="your_key_id" \
  -e B2_APPLICATION_KEY="your_key" \
  -e B2_BUCKET_NAME="your_bucket" \
  yourusername/mysql-backup-system:latest
```

## ⚙️ 环境变量配置

### 必需变量

| 变量名 | 描述 | 示例 |
|--------|------|------|
| `MYSQL_CONNECTIONS` | MySQL连接字符串 | `mysql://user:pass@host:3306/db` |
| `B2_APPLICATION_KEY_ID` | Backblaze B2应用密钥ID | `your_key_id` |
| `B2_APPLICATION_KEY` | Backblaze B2应用密钥 | `your_application_key` |
| `B2_BUCKET_NAME` | B2存储桶名称 | `my-backup-bucket` |

### 可选变量

| 变量名 | 默认值 | 描述 |
|--------|--------|------|
| `BACKUP_SCHEDULE` | `0 4 * * *` | 备份调度时间（Cron表达式） |
| `RETENTION_DAYS` | `7` | 备份保留天数 |
| `HEALTH_CHECK_PORT` | `8080` | 健康检查端口 |
| `RUN_INITIAL_BACKUP` | `true` | 启动时是否执行初始备份 |
| `LOG_LEVEL` | `INFO` | 日志级别 |

## 🔍 监控和管理

### 健康检查端点

- **基本健康检查**: `GET /health`
- **详细状态**: `GET /status`
- **系统指标**: `GET /metrics`
- **手动备份**: `POST /backup/run`
- **手动清理**: `POST /cleanup/run`

### 示例API调用

```bash
# 检查系统健康状态
curl http://localhost:8080/health

# 获取详细状态信息
curl http://localhost:8080/status

# 手动触发备份
curl -X POST http://localhost:8080/backup/run

# 手动触发清理
curl -X POST http://localhost:8080/cleanup/run
```

## 📊 日志和监控

系统提供详细的日志记录，包括：

- 备份任务执行状态
- 文件上传进度
- 错误信息和异常处理
- 系统性能指标

日志输出到标准输出和文件（如果挂载了日志目录）。

## 🔧 高级配置

### 自定义调度时间

使用Cron表达式自定义备份时间：

```bash
# 每天凌晨2点
BACKUP_SCHEDULE="0 2 * * *"

# 每12小时
BACKUP_SCHEDULE="0 */12 * * *"

# 每周日凌晨3点
BACKUP_SCHEDULE="0 3 * * 0"
```

### 多数据库配置

```bash
# 同服务器多个数据库
MYSQL_CONNECTIONS="mysql://user:pass@host:3306/db1,db2,db3"

# 多个不同服务器
MYSQL_CONNECTIONS="mysql://user1:pass1@host1:3306/db1;mysql://user2:pass2@host2:3306/db2"

# JSON格式（推荐用于复杂配置）
MYSQL_CONNECTIONS='[
  {"name":"Production","connection":"mysql://prod:pass@prod.db.com:3306/proddb"},
  {"name":"Staging","connection":"mysql://staging:pass@staging.db.com:3306/stagingdb"}
]'
```

## 🚀 GitHub Actions自动构建

项目包含GitHub Actions工作流，可自动构建和推送Docker镜像到Docker Hub。

### 设置步骤

1. **Fork此仓库到你的GitHub账户**

2. **设置Docker Hub凭据**（可选，但推荐）：
   - 在Docker Hub创建访问令牌
   - 在GitHub仓库设置中添加Secrets：
     - `DOCKERHUB_USERNAME`: 你的Docker Hub用户名
     - `DOCKERHUB_TOKEN`: 你的Docker Hub访问令牌
   - 详细步骤请参考 [GitHub Actions设置指南](GITHUB_ACTIONS_SETUP.md)

3. **推送代码或创建标签**：
   - 推送到`main`分支会自动构建和推送`latest`标签（如果有凭据）
   - 创建版本标签（如`v1.0.0`）会构建对应版本标签
   - Pull Request只会构建测试，不会推送

**注意**: 即使没有Docker Hub凭据，GitHub Actions也会成功构建镜像进行测试，只是不会推送到Docker Hub。

### 使用预构建镜像

```bash
# 从Docker Hub拉取最新镜像
docker pull yourusername/mysql-backup-system:latest

# 或使用特定版本
docker pull yourusername/mysql-backup-system:v1.0.0
```

## 🛡️ 安全注意事项

1. **敏感信息保护**：
   - 使用环境变量存储敏感信息
   - 不要在代码中硬编码密码
   - 使用`.env`文件并将其添加到`.gitignore`

2. **网络安全**：
   - 确保MySQL连接使用SSL（如果需要）
   - 限制健康检查端口的访问

3. **权限管理**：
   - 使用最小权限原则配置数据库用户
   - 定期轮换B2访问密钥

## 🔧 故障排除

### 常见问题

1. **连接失败**：
   - 检查数据库连接字符串格式
   - 验证网络连接和防火墙设置
   - 确认数据库用户权限

2. **B2上传失败**：
   - 验证B2密钥和存储桶名称
   - 检查网络连接
   - 确认存储桶权限

3. **备份文件为空**：
   - 检查mysqldump是否正确安装
   - 验证数据库用户是否有足够权限
   - 查看详细错误日志

### 调试模式

启用调试日志：

```bash
LOG_LEVEL=DEBUG
```

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

## 🤝 贡献

欢迎提交Issue和Pull Request！

## 📞 支持

如有问题，请：
1. 查看文档和FAQ
2. 搜索现有Issues
3. 创建新的Issue并提供详细信息
