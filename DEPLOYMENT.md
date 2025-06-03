# 部署指南

本文档详细介绍如何在不同环境中部署MySQL备份系统。

## 📋 部署前准备

### 1. 环境要求

- Docker 20.10+
- Docker Compose 2.0+
- 至少512MB可用内存
- 网络连接（访问MySQL数据库和Backblaze B2）

### 2. 获取Backblaze B2凭据

1. 登录 [Backblaze B2控制台](https://secure.backblaze.com/b2_buckets.htm)
2. 创建一个新的存储桶或使用现有存储桶
3. 创建应用密钥：
   - 转到 "App Keys" 页面
   - 点击 "Add a New Application Key"
   - 选择存储桶和权限（需要读写权限）
   - 记录 `keyID` 和 `applicationKey`

### 3. 准备MySQL连接信息

确保你有以下MySQL连接信息：
- 主机地址和端口
- 用户名和密码
- 数据库名称
- SSL要求（如果有）

## 🚀 生产环境部署

### 方法1: 使用Docker Compose（推荐）

1. **克隆仓库**
```bash
git clone https://github.com/yourusername/mysql-backup-system.git
cd mysql-backup-system
```

2. **配置环境变量**
```bash
cp .env.example .env
nano .env  # 编辑配置文件
```

3. **启动服务**
```bash
docker-compose up -d
```

4. **验证部署**
```bash
# 检查服务状态
docker-compose ps

# 查看日志
docker-compose logs -f

# 健康检查
curl http://localhost:8080/health
```

### 方法2: 使用预构建镜像

```bash
docker run -d \
  --name mysql-backup \
  --restart unless-stopped \
  -p 8080:8080 \
  -e MYSQL_CONNECTIONS="mysql://user:pass@host:3306/db" \
  -e B2_APPLICATION_KEY_ID="your_key_id" \
  -e B2_APPLICATION_KEY="your_key" \
  -e B2_BUCKET_NAME="your_bucket" \
  -e BACKUP_SCHEDULE="0 4 * * *" \
  -e RETENTION_DAYS="7" \
  -v /var/log/mysql-backup:/var/log \
  yourusername/mysql-backup-system:latest
```

## 🔧 配置详解

### 必需配置

```bash
# MySQL连接 - 选择适合你的格式
MYSQL_CONNECTIONS=mysql://user:pass@host:3306/database

# Backblaze B2配置
B2_APPLICATION_KEY_ID=your_key_id
B2_APPLICATION_KEY=your_application_key
B2_BUCKET_NAME=your_bucket_name
```

### 高级配置

```bash
# 备份调度（Cron格式）
BACKUP_SCHEDULE=0 4 * * *  # 每天4点

# 保留策略
RETENTION_DAYS=7  # 保留7天

# 监控配置
HEALTH_CHECK_PORT=8080
LOG_LEVEL=INFO

# 启动行为
RUN_INITIAL_BACKUP=true  # 启动时执行备份
```

## 🌐 云平台部署

### AWS ECS

1. **创建任务定义**
```json
{
  "family": "mysql-backup",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "256",
  "memory": "512",
  "containerDefinitions": [
    {
      "name": "mysql-backup",
      "image": "yourusername/mysql-backup-system:latest",
      "portMappings": [
        {
          "containerPort": 8080,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {"name": "MYSQL_CONNECTIONS", "value": "mysql://..."},
        {"name": "B2_APPLICATION_KEY_ID", "value": "..."},
        {"name": "B2_APPLICATION_KEY", "value": "..."},
        {"name": "B2_BUCKET_NAME", "value": "..."}
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/mysql-backup",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

### Google Cloud Run

```bash
# 构建并推送镜像
docker build -t gcr.io/PROJECT_ID/mysql-backup .
docker push gcr.io/PROJECT_ID/mysql-backup

# 部署到Cloud Run
gcloud run deploy mysql-backup \
  --image gcr.io/PROJECT_ID/mysql-backup \
  --platform managed \
  --region us-central1 \
  --set-env-vars MYSQL_CONNECTIONS="mysql://...",B2_APPLICATION_KEY_ID="...",B2_APPLICATION_KEY="...",B2_BUCKET_NAME="..." \
  --memory 512Mi \
  --cpu 1 \
  --port 8080
```

### Azure Container Instances

```bash
az container create \
  --resource-group myResourceGroup \
  --name mysql-backup \
  --image yourusername/mysql-backup-system:latest \
  --cpu 1 \
  --memory 1 \
  --ports 8080 \
  --environment-variables \
    MYSQL_CONNECTIONS="mysql://..." \
    B2_APPLICATION_KEY_ID="..." \
    B2_APPLICATION_KEY="..." \
    B2_BUCKET_NAME="..." \
  --restart-policy Always
```

## 🔍 监控和维护

### 健康检查

设置外部监控检查以下端点：
- `GET /health` - 基本健康状态
- `GET /status` - 详细状态信息

### 日志监控

监控以下日志模式：
- `ERROR` - 错误信息
- `备份任务失败` - 备份失败
- `B2连接失败` - 存储连接问题

### 告警设置

建议设置以下告警：
1. 服务健康检查失败
2. 24小时内无成功备份
3. B2存储连接失败
4. 磁盘空间不足

## 🔒 安全最佳实践

### 1. 凭据管理

- 使用环境变量存储敏感信息
- 定期轮换B2应用密钥
- 使用最小权限原则

### 2. 网络安全

- 限制健康检查端口访问
- 使用SSL连接MySQL（如果可能）
- 配置防火墙规则

### 3. 备份安全

- 启用B2存储桶加密
- 定期验证备份完整性
- 监控异常访问

## 🚨 故障排除

### 常见问题

1. **连接超时**
```bash
# 检查网络连接
docker exec mysql-backup ping mysql-host

# 检查DNS解析
docker exec mysql-backup nslookup mysql-host
```

2. **权限错误**
```bash
# 检查MySQL用户权限
SHOW GRANTS FOR 'username'@'%';

# 检查B2权限
curl -H "Authorization: Basic $(echo -n keyId:applicationKey | base64)" \
  https://api.backblazeb2.com/b2api/v2/b2_authorize_account
```

3. **内存不足**
```bash
# 增加容器内存限制
docker run --memory=1g ...

# 或在docker-compose.yml中设置
deploy:
  resources:
    limits:
      memory: 1G
```

### 调试模式

启用详细日志：
```bash
LOG_LEVEL=DEBUG
```

### 手动测试

```bash
# 手动触发备份
curl -X POST http://localhost:8080/backup/run

# 手动触发清理
curl -X POST http://localhost:8080/cleanup/run

# 查看详细状态
curl http://localhost:8080/status | jq
```

## 📊 性能优化

### 资源配置

根据数据库大小调整资源：

| 数据库大小 | CPU | 内存 | 网络 |
|-----------|-----|------|------|
| < 1GB     | 0.25核 | 256MB | 标准 |
| 1-10GB    | 0.5核  | 512MB | 标准 |
| 10-100GB  | 1核    | 1GB   | 高速 |
| > 100GB   | 2核    | 2GB   | 高速 |

### 备份优化

- 使用`--single-transaction`确保一致性
- 启用`--quick`减少内存使用
- 考虑分表备份大型数据库

## 📈 扩展部署

### 多实例部署

为不同的数据库组部署多个实例：

```bash
# 实例1 - 生产数据库
docker run -d --name mysql-backup-prod \
  -e MYSQL_CONNECTIONS="mysql://prod-user:pass@prod-host:3306/prod-db" \
  ...

# 实例2 - 测试数据库
docker run -d --name mysql-backup-test \
  -e MYSQL_CONNECTIONS="mysql://test-user:pass@test-host:3306/test-db" \
  ...
```

### 负载均衡

使用nginx或云负载均衡器分发健康检查请求：

```nginx
upstream mysql-backup {
    server mysql-backup-1:8080;
    server mysql-backup-2:8080;
}

server {
    listen 80;
    location /health {
        proxy_pass http://mysql-backup;
    }
}
```
