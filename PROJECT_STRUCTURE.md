# 项目结构说明

本文档详细说明了MySQL备份系统的项目结构和各个文件的作用。

## 📁 项目结构

```
mysql-backup-system/
├── src/                          # 主要Python源代码
│   ├── main.py                   # 应用程序入口点
│   ├── database_parser.py        # 数据库连接字符串解析器
│   ├── backup_manager.py         # MySQL备份管理器
│   ├── b2_uploader.py           # Backblaze B2云存储管理器
│   ├── scheduler.py             # 任务调度器
│   └── health_check.py          # 健康检查HTTP服务
│
├── scripts/                      # 工具脚本
│   └── test_system.py           # 系统测试脚本
│
├── test-data/                    # 测试数据
│   └── 01-init.sql              # 测试数据库初始化脚本
│
├── .github/                      # GitHub Actions工作流
│   └── workflows/
│       └── docker-build.yml     # Docker镜像构建和发布
│
├── logs/                         # 日志目录（运行时创建）
│
├── Dockerfile                    # Docker镜像构建文件
├── docker-compose.yml           # 生产环境Docker编排
├── docker-compose.dev.yml       # 开发环境Docker编排
├── requirements.txt             # Python依赖包
├── Makefile                     # 便捷操作命令
│
├── .env.example                 # 环境变量配置模板
├── .env.dev                     # 开发环境配置
├── .gitignore                   # Git忽略文件
├── .dockerignore               # Docker忽略文件
│
├── README.md                    # 项目主文档
├── QUICKSTART.md               # 快速开始指南
├── DEPLOYMENT.md               # 部署指南
├── PROJECT_STRUCTURE.md        # 项目结构说明（本文件）
└── LICENSE                     # 开源许可证
```

## 📄 核心文件说明

### 源代码文件 (`src/`)

#### `main.py`
- **作用**: 应用程序的主入口点
- **功能**: 
  - 整合所有组件
  - 处理服务启动和停止
  - 配置日志系统
  - 信号处理
- **关键类**: `MySQLBackupService`

#### `database_parser.py`
- **作用**: 解析各种格式的MySQL连接字符串，支持多个不同地方的数据库
- **支持格式**:
  - TCP格式: `user:pass@tcp(host:port)/db`
  - MySQL URL: `mysql://user:pass@host:port/db`
  - 同服务器多数据库: `mysql://user:pass@host:port/db1,db2,db3`
  - 多个不同服务器: `mysql://user1:pass1@host1:port1/db1;mysql://user2:pass2@host2:port2/db2`
  - SSL连接: `mysql://user:pass@host:port/db?ssl-mode=REQUIRED`
  - JSON配置: 支持复杂的多连接配置，包括分组、调度、保留策略等
- **新功能**:
  - 连接分组管理
  - 启用/禁用控制
  - 自定义调度和保留策略
  - 连接信息安全显示
- **关键类**: `DatabaseConnectionParser`

#### `backup_manager.py`
- **作用**: 管理MySQL数据库备份操作
- **功能**:
  - 测试数据库连接
  - 执行mysqldump备份
  - 压缩备份文件
  - 清理本地文件
- **关键类**: `BackupManager`

#### `b2_uploader.py`
- **作用**: 管理Backblaze B2云存储操作
- **功能**:
  - 上传备份文件到B2
  - 列出存储桶中的文件
  - 删除过期备份
  - 测试B2连接
- **关键类**: `B2Uploader`

#### `scheduler.py`
- **作用**: 管理定时任务调度
- **功能**:
  - 解析Cron表达式
  - 调度备份和清理任务
  - 支持手动触发
- **关键类**: `BackupScheduler`

#### `health_check.py`
- **作用**: 提供HTTP健康检查服务
- **端点**:
  - `GET /health` - 基本健康检查
  - `GET /status` - 详细状态信息
  - `GET /metrics` - 系统指标
  - `POST /backup/run` - 手动备份
  - `POST /cleanup/run` - 手动清理
- **关键类**: `HealthChecker`, `HealthCheckServer`

### 配置文件

#### `Dockerfile`
- **作用**: 定义Docker镜像构建过程
- **特点**:
  - 基于Python 3.11-slim
  - 安装mysql-client
  - 配置健康检查
  - 优化镜像大小

#### `docker-compose.yml`
- **作用**: 生产环境的Docker编排配置
- **特点**:
  - 环境变量配置
  - 端口映射
  - 健康检查
  - 资源限制
  - 重启策略

#### `docker-compose.dev.yml`
- **作用**: 开发环境的Docker编排配置
- **特点**:
  - 包含测试MySQL数据库
  - 调试配置
  - 源代码挂载（可选）
  - 快速测试调度

#### `requirements.txt`
- **作用**: Python依赖包列表
- **主要依赖**:
  - `mysql-connector-python` - MySQL连接器
  - `b2sdk` - Backblaze B2 SDK
  - `schedule` - 任务调度
  - `croniter` - Cron表达式解析

### 工具和脚本

#### `Makefile`
- **作用**: 提供便捷的操作命令
- **主要命令**:
  - `make build` - 构建镜像
  - `make run` - 启动生产环境
  - `make dev-up` - 启动开发环境
  - `make health` - 健康检查
  - `make backup` - 手动备份

#### `scripts/test_system.py`
- **作用**: 系统功能测试脚本
- **测试内容**:
  - 数据库连接解析
  - 健康检查端点
  - 手动操作功能
  - 服务可用性

### 文档文件

#### `README.md`
- **作用**: 项目主文档
- **内容**: 功能介绍、快速开始、API文档、配置说明

#### `QUICKSTART.md`
- **作用**: 5分钟快速部署指南
- **内容**: 最简配置、验证步骤、常用命令

#### `DEPLOYMENT.md`
- **作用**: 详细部署指南
- **内容**: 生产部署、云平台部署、监控配置、故障排除

#### `PROJECT_STRUCTURE.md`
- **作用**: 项目结构说明（本文件）
- **内容**: 文件结构、组件说明、开发指南

### GitHub Actions

#### `.github/workflows/docker-build.yml`
- **作用**: 自动构建和发布Docker镜像
- **触发条件**:
  - 推送到main分支
  - 创建版本标签
  - Pull Request
- **功能**:
  - 多架构构建（amd64, arm64）
  - 自动标签管理
  - Docker Hub发布

## 🔧 开发指南

### 添加新功能

1. **创建新模块**: 在`src/`目录下创建新的Python文件
2. **更新main.py**: 在主服务类中集成新功能
3. **添加测试**: 在`scripts/test_system.py`中添加测试
4. **更新文档**: 更新相关文档文件

### 修改配置

1. **环境变量**: 在`.env.example`中添加新的配置项
2. **Docker配置**: 更新`docker-compose.yml`
3. **文档更新**: 在README.md中说明新配置

### 测试流程

1. **本地测试**: 使用`make dev-up`启动开发环境
2. **功能测试**: 运行`python scripts/test_system.py`
3. **集成测试**: 使用`make test`运行完整测试

### 发布流程

1. **更新版本**: 创建版本标签（如`v1.0.0`）
2. **自动构建**: GitHub Actions自动构建和发布
3. **更新文档**: 更新CHANGELOG和文档

## 📊 依赖关系

```
main.py
├── database_parser.py
├── backup_manager.py
├── b2_uploader.py
├── scheduler.py
└── health_check.py

health_check.py
└── main.py (循环依赖，通过参数传递解决)

scheduler.py
├── backup_manager.py (通过回调函数)
└── b2_uploader.py (通过回调函数)
```

## 🔒 安全考虑

### 敏感信息处理
- 所有敏感信息通过环境变量传递
- 日志中隐藏密码信息
- 使用`.gitignore`防止敏感文件提交

### 权限控制
- 容器以非root用户运行（可选）
- 最小权限原则
- 网络访问限制

### 数据安全
- 备份文件加密传输
- 本地文件及时清理
- B2存储桶访问控制

这个项目结构设计遵循了模块化、可维护性和安全性的原则，便于开发、部署和维护。
