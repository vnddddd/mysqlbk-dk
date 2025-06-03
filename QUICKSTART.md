# 快速开始指南

本指南将帮助你在5分钟内启动MySQL备份系统。

## 📋 准备工作

在开始之前，请确保你有：

1. **Docker和Docker Compose** 已安装
2. **MySQL数据库** 连接信息
3. **Backblaze B2账户** 和存储桶

## 🚀 5分钟快速部署

### 步骤1: 获取代码

```bash
git clone https://github.com/yourusername/mysql-backup-system.git
cd mysql-backup-system
```

### 步骤2: 配置环境变量

```bash
# 复制配置模板
cp .env.example .env

# 编辑配置文件
nano .env
```

**最小配置示例：**
```bash
# 必需配置
MYSQL_CONNECTIONS=mysql://username:password@host:3306/database
B2_APPLICATION_KEY_ID=your_b2_key_id
B2_APPLICATION_KEY=your_b2_application_key
B2_BUCKET_NAME=your_backup_bucket

# 可选配置（使用默认值）
BACKUP_SCHEDULE=0 4 * * *
RETENTION_DAYS=7
```

### 步骤3: 启动服务

```bash
# 启动服务
docker-compose up -d

# 查看启动日志
docker-compose logs -f
```

### 步骤4: 验证部署

```bash
# 检查服务状态
curl http://localhost:8080/health

# 查看详细状态
curl http://localhost:8080/status

# 手动触发备份测试
curl -X POST http://localhost:8080/backup/run
```

## ✅ 验证清单

确保以下项目都正常工作：

- [ ] 服务启动成功（`docker-compose ps` 显示运行中）
- [ ] 健康检查通过（`/health` 返回 `"status": "healthy"`）
- [ ] 数据库连接正常（日志中无连接错误）
- [ ] B2存储连接正常（日志中无上传错误）
- [ ] 初始备份成功（如果启用了 `RUN_INITIAL_BACKUP`）

## 🔧 常用命令

```bash
# 查看服务状态
docker-compose ps

# 查看实时日志
docker-compose logs -f

# 重启服务
docker-compose restart

# 停止服务
docker-compose down

# 手动备份
curl -X POST http://localhost:8080/backup/run

# 手动清理
curl -X POST http://localhost:8080/cleanup/run
```

## 🎯 下一步

部署成功后，你可以：

1. **设置监控**: 配置外部监控检查 `/health` 端点
2. **调整调度**: 修改 `BACKUP_SCHEDULE` 适应你的需求
3. **配置告警**: 设置备份失败时的通知
4. **查看文档**: 阅读完整的 [README.md](README.md) 和 [DEPLOYMENT.md](DEPLOYMENT.md)

## 🚨 故障排除

### 服务无法启动

```bash
# 检查配置文件
cat .env

# 查看详细错误
docker-compose logs mysql-backup
```

### 数据库连接失败

```bash
# 测试数据库连接
docker run --rm mysql:8.0 mysql -h your_host -P 3306 -u your_user -p

# 检查连接字符串格式
echo $MYSQL_CONNECTIONS
```

### B2上传失败

```bash
# 验证B2凭据
curl -u "$B2_APPLICATION_KEY_ID:$B2_APPLICATION_KEY" \
  https://api.backblazeb2.com/b2api/v2/b2_authorize_account
```

## 📞 获取帮助

如果遇到问题：

1. 查看 [故障排除文档](DEPLOYMENT.md#故障排除)
2. 搜索 [GitHub Issues](https://github.com/yourusername/mysql-backup-system/issues)
3. 创建新的 Issue 并提供详细信息

## 🎉 成功！

恭喜！你的MySQL备份系统现在已经运行并将自动备份你的数据库到Backblaze B2云存储。

系统将：
- ⏰ 每天按计划自动备份
- ☁️ 上传备份到B2云存储
- 🧹 自动清理过期备份
- 📊 提供健康检查和监控端点
- 📝 记录详细的操作日志
