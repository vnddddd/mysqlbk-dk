# MySQL备份系统 Makefile

.PHONY: help build run stop logs clean test dev-up dev-down dev-logs health status backup cleanup

# 默认目标
help:
	@echo "MySQL备份系统 - 可用命令:"
	@echo ""
	@echo "  构建和运行:"
	@echo "    build      - 构建Docker镜像"
	@echo "    run        - 运行生产环境"
	@echo "    stop       - 停止服务"
	@echo "    logs       - 查看日志"
	@echo "    clean      - 清理Docker资源"
	@echo ""
	@echo "  开发环境:"
	@echo "    dev-up     - 启动开发环境（包含测试数据库）"
	@echo "    dev-down   - 停止开发环境"
	@echo "    dev-logs   - 查看开发环境日志"
	@echo ""
	@echo "  测试和监控:"
	@echo "    test       - 运行测试"
	@echo "    health     - 检查服务健康状态"
	@echo "    status     - 获取详细状态"
	@echo "    backup     - 手动触发备份"
	@echo "    cleanup    - 手动触发清理"
	@echo "    security   - 运行安全检查"

# 构建Docker镜像
build:
	@echo "构建Docker镜像..."
	docker build -t mysql-backup-system .

# 运行生产环境
run:
	@echo "启动生产环境..."
	@if [ ! -f .env ]; then \
		echo "错误: .env文件不存在，请复制.env.example并配置"; \
		exit 1; \
	fi
	docker-compose up -d

# 停止服务
stop:
	@echo "停止服务..."
	docker-compose down

# 查看日志
logs:
	docker-compose logs -f

# 清理Docker资源
clean:
	@echo "清理Docker资源..."
	docker-compose down -v
	docker system prune -f

# 启动开发环境
dev-up:
	@echo "启动开发环境..."
	@if [ ! -f .env.dev ]; then \
		echo "警告: .env.dev文件不存在，使用默认配置"; \
	fi
	docker-compose -f docker-compose.dev.yml --env-file .env.dev up -d

# 停止开发环境
dev-down:
	@echo "停止开发环境..."
	docker-compose -f docker-compose.dev.yml down

# 查看开发环境日志
dev-logs:
	docker-compose -f docker-compose.dev.yml logs -f

# 运行测试
test:
	@echo "运行测试..."
	@python scripts/test_parser_only.py

# 运行解析器测试
test-parser:
	@echo "运行数据库连接解析器测试..."
	@python scripts/test_parser_only.py

# 健康检查
health:
	@echo "检查服务健康状态..."
	@curl -s http://localhost:8080/health | python -m json.tool || echo "服务不可用"

# 获取详细状态
status:
	@echo "获取服务状态..."
	@curl -s http://localhost:8080/status | python -m json.tool || echo "服务不可用"

# 手动触发备份
backup:
	@echo "触发手动备份..."
	@curl -s -X POST http://localhost:8080/backup/run | python -m json.tool || echo "备份触发失败"

# 手动触发清理
cleanup:
	@echo "触发手动清理..."
	@curl -s -X POST http://localhost:8080/cleanup/run | python -m json.tool || echo "清理触发失败"

# 查看容器状态
ps:
	docker-compose ps

# 进入容器
shell:
	docker-compose exec mysql-backup /bin/bash

# 重启服务
restart: stop run

# 查看实时日志（最后100行）
tail:
	docker-compose logs --tail=100 -f

# 检查配置
check-config:
	@echo "检查配置文件..."
	@if [ -f .env ]; then \
		echo "✓ .env文件存在"; \
		echo "检查必需的环境变量:"; \
		grep -E "^(MYSQL_CONNECTIONS|B2_APPLICATION_KEY_ID|B2_APPLICATION_KEY|B2_BUCKET_NAME)=" .env || echo "⚠ 缺少必需的环境变量"; \
	else \
		echo "✗ .env文件不存在"; \
	fi

# 安全检查
security:
	@echo "运行安全检查..."
	@python scripts/security_check.py
