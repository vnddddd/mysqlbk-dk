# 安全指南

本文档详细说明了MySQL备份系统的安全最佳实践和注意事项。

## 🔒 敏感信息保护

### 环境变量管理

**✅ 正确做法：**
```bash
# 使用环境变量
export MYSQL_CONNECTIONS="mysql://user:password@host:3306/db"
export B2_APPLICATION_KEY_ID="your_key_id"
export B2_APPLICATION_KEY="your_application_key"
```

**❌ 错误做法：**
```python
# 不要在代码中硬编码敏感信息（这是错误示例！）
connection = "mysql://admin:NEVER_DO_THIS@prod-db.com:3306/maindb"
b2_key = "NEVER_HARDCODE_KEYS_LIKE_THIS"
```

### .env文件安全

1. **永远不要提交.env文件到版本控制**
```bash
# 确保.env在.gitignore中
echo ".env" >> .gitignore
```

2. **使用.env.example作为模板**
```bash
# 复制模板并填入实际值
cp .env.example .env
# 编辑.env文件，填入真实的敏感信息
```

3. **设置适当的文件权限**
```bash
# 限制.env文件的访问权限
chmod 600 .env
```

## 🔐 数据库安全

### 连接安全

1. **使用SSL连接（推荐）**
```bash
MYSQL_CONNECTIONS="mysql://user:pass@host:3306/db?ssl-mode=REQUIRED"
```

2. **创建专用备份用户**
```sql
-- 创建只有备份权限的用户
CREATE USER 'backup_user'@'%' IDENTIFIED BY 'strong_password';
GRANT SELECT, LOCK TABLES, SHOW VIEW, EVENT, TRIGGER ON *.* TO 'backup_user'@'%';
FLUSH PRIVILEGES;
```

3. **限制网络访问**
```sql
-- 只允许特定IP访问
CREATE USER 'backup_user'@'backup_server_ip' IDENTIFIED BY 'strong_password';
```

### 密码策略

- 使用强密码（至少12位，包含大小写字母、数字、特殊字符）
- 定期更换密码（建议每90天）
- 不要重复使用密码
- 使用密码管理器生成和存储密码

## ☁️ 云存储安全

### Backblaze B2配置

1. **使用应用密钥而非主密钥**
```bash
# 在B2控制台创建应用密钥，限制权限
# 只授予必要的存储桶访问权限
```

2. **启用存储桶加密**
```bash
# 在B2控制台启用服务器端加密
# 或使用客户端加密
```

3. **配置生命周期规则**
```bash
# 自动删除过期备份
# 设置合理的保留策略
```

### 访问控制

- 定期轮换B2应用密钥
- 监控B2访问日志
- 使用最小权限原则
- 启用B2的访问控制列表(ACL)

## 🐳 容器安全

### Docker安全

1. **使用非root用户运行**
```dockerfile
# 在Dockerfile中添加
RUN adduser --disabled-password --gecos '' appuser
USER appuser
```

2. **限制容器权限**
```yaml
# docker-compose.yml
security_opt:
  - no-new-privileges:true
read_only: true
tmpfs:
  - /tmp
```

3. **扫描镜像漏洞**
```bash
# 使用Docker Scout或其他工具
docker scout cves mysql-backup-system:latest
```

### 网络安全

1. **限制端口暴露**
```yaml
# 只暴露必要的端口
ports:
  - "127.0.0.1:8080:8080"  # 只绑定本地
```

2. **使用防火墙**
```bash
# 配置iptables或ufw
ufw allow from trusted_ip to any port 8080
```

## 🔍 监控和审计

### 日志安全

1. **敏感信息脱敏**
```python
# 在日志中隐藏密码
logger.info(f"连接数据库: {host}:{port}/{database}")
# 不要记录: logger.info(f"连接字符串: {connection_string}")
```

2. **日志轮转和保留**
```bash
# 配置logrotate
/var/log/mysql-backup.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
}
```

### 安全监控

1. **设置告警**
- 备份失败告警
- 异常访问告警
- 资源使用异常告警

2. **定期安全检查**
```bash
# 运行安全检查脚本
python scripts/security_check.py
```

## 🚨 事件响应

### 安全事件处理

1. **密钥泄露响应**
```bash
# 立即轮换所有相关密钥
# 检查访问日志
# 评估影响范围
```

2. **数据泄露响应**
```bash
# 立即停止服务
# 评估泄露范围
# 通知相关方
# 修复安全漏洞
```

### 恢复计划

- 备份恢复程序
- 服务恢复时间目标(RTO)
- 数据恢复点目标(RPO)
- 通信计划

## 🔧 安全工具

### 自动化安全检查

```bash
# 运行完整的安全检查
make security-check

# 检查敏感信息泄露
python scripts/security_check.py

# 检查依赖漏洞
pip audit
```

### 定期安全任务

1. **每周任务**
- 检查日志异常
- 验证备份完整性
- 更新依赖包

2. **每月任务**
- 轮换访问密钥
- 安全配置审查
- 漏洞扫描

3. **每季度任务**
- 全面安全评估
- 渗透测试
- 应急响应演练

## 📋 安全检查清单

### 部署前检查

- [ ] 所有敏感信息都通过环境变量配置
- [ ] .env文件已添加到.gitignore
- [ ] 使用强密码和密钥
- [ ] 启用SSL连接
- [ ] 配置防火墙规则
- [ ] 设置日志监控
- [ ] 配置备份加密

### 运行时检查

- [ ] 监控系统日志
- [ ] 检查异常访问
- [ ] 验证备份完整性
- [ ] 监控资源使用
- [ ] 检查安全更新

### 定期维护

- [ ] 轮换密钥和密码
- [ ] 更新依赖包
- [ ] 审查访问权限
- [ ] 测试恢复程序
- [ ] 更新安全策略

## 🆘 安全支持

### 报告安全问题

如果发现安全漏洞，请：

1. **不要**在公开的Issue中报告
2. 发送邮件到：security@yourproject.com
3. 包含详细的漏洞描述
4. 提供复现步骤
5. 建议修复方案（如果有）

### 安全更新

- 关注项目的安全公告
- 及时更新到最新版本
- 订阅安全邮件列表
- 定期检查依赖更新

## 📚 参考资源

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Docker Security Best Practices](https://docs.docker.com/engine/security/)
- [MySQL Security Guidelines](https://dev.mysql.com/doc/refman/8.0/en/security-guidelines.html)
- [Backblaze B2 Security](https://www.backblaze.com/b2/docs/security.html)

---

**记住：安全是一个持续的过程，不是一次性的任务。定期审查和更新你的安全措施。**
