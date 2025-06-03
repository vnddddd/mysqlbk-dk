# GitHub Actions 自动构建设置指南

本指南将帮助你设置GitHub Actions自动构建和发布Docker镜像到Docker Hub。

## 🚀 快速设置

### 步骤1: 创建Docker Hub访问令牌

1. 登录 [Docker Hub](https://hub.docker.com/)
2. 点击右上角的用户名 → **Account Settings**
3. 选择 **Security** 标签页
4. 点击 **New Access Token**
5. 输入令牌描述（如：`GitHub Actions`）
6. 选择权限：**Read, Write, Delete**
7. 点击 **Generate** 并**复制生成的令牌**（只显示一次！）

### 步骤2: 在GitHub仓库中添加Secrets

1. 进入你的GitHub仓库
2. 点击 **Settings** 标签页
3. 在左侧菜单中选择 **Secrets and variables** → **Actions**
4. 点击 **New repository secret** 添加以下secrets：

#### 必需的Secrets

| Secret名称 | 值 | 说明 |
|-----------|-----|------|
| `DOCKERHUB_USERNAME` | 你的Docker Hub用户名 | 用于登录Docker Hub |
| `DOCKERHUB_TOKEN` | 刚才生成的访问令牌 | 用于认证（不是密码！） |

### 步骤3: 验证设置

1. 推送代码到`main`分支或创建Pull Request
2. 查看 **Actions** 标签页中的工作流运行状态
3. 如果设置正确，你应该看到：
   - ✅ 构建成功
   - ✅ 镜像推送到Docker Hub（仅限main分支）

## 🔧 工作流说明

### 触发条件

工作流在以下情况下自动运行：
- 推送到 `main` 或 `develop` 分支
- 创建版本标签（如 `v1.0.0`）
- 创建Pull Request到 `main` 分支

### 构建行为

| 触发条件 | 构建 | 推送到Docker Hub | 标签 | 说明 |
|---------|------|----------------|------|------|
| Push到main分支 | ✅ | ✅* | `latest` | *需要Docker Hub凭据 |
| Push到develop分支 | ✅ | ✅* | `develop` | *需要Docker Hub凭据 |
| 创建版本标签 | ✅ | ✅* | 版本号（如`v1.0.0`, `1.0`, `1`） | *需要Docker Hub凭据 |
| Pull Request | ✅ | ❌ | 仅构建测试 | 永远不推送 |
| 无Docker Hub凭据 | ✅ | ❌ | 仅构建测试 | 安全地跳过推送步骤 |

### 支持的架构

- `linux/amd64` (x86_64)
- `linux/arm64` (ARM64)

## 🛠️ 自定义配置

### 修改镜像名称

编辑 `.github/workflows/docker-build.yml` 文件：

```yaml
env:
  REGISTRY: docker.io
  IMAGE_NAME: your-custom-image-name  # 修改这里
```

### 修改触发分支

```yaml
on:
  push:
    branches:
      - main
      - your-branch  # 添加其他分支
```

### 添加自定义标签

```yaml
tags: |
  type=ref,event=branch
  type=ref,event=pr
  type=semver,pattern={{version}}
  type=raw,value=custom-tag  # 添加自定义标签
```

## 🚨 故障排除

### 常见错误

#### 1. "Username and password required"
**原因**: 缺少Docker Hub凭据
**解决**: 确保已添加 `DOCKERHUB_USERNAME` 和 `DOCKERHUB_TOKEN` secrets
**注意**: 新版本的工作流会自动跳过推送步骤如果没有凭据

#### 2. "denied: requested access to the resource is denied"
**原因**: Docker Hub权限不足或用户名错误
**解决**: 
- 检查用户名是否正确
- 确保访问令牌有写入权限
- 验证仓库名称格式：`username/repository`

#### 3. "repository does not exist"
**原因**: Docker Hub上不存在对应的仓库
**解决**: 
- 在Docker Hub上创建仓库
- 或者让GitHub Actions自动创建（首次推送时）

#### 4. 构建成功但没有推送
**原因**: 这是正常行为，当：
- 是Pull Request时（安全考虑）
- 缺少Docker Hub凭据时
**解决**: 检查日志中的提示信息

### 调试步骤

1. **查看工作流日志**：
   - 进入 **Actions** 标签页
   - 点击失败的工作流运行
   - 查看详细的错误信息

2. **验证Secrets**：
   ```bash
   # 在工作流中添加调试步骤（注意：不要打印实际的secret值）
   - name: Debug secrets
     run: |
       echo "Username exists: ${{ secrets.DOCKERHUB_USERNAME != '' }}"
       echo "Token exists: ${{ secrets.DOCKERHUB_TOKEN != '' }}"
   ```

3. **本地测试Docker构建**：
   ```bash
   docker build -t test-image .
   docker run --rm test-image
   ```

## 🔒 安全最佳实践

### 1. 使用访问令牌而非密码
- ✅ 使用Docker Hub访问令牌
- ❌ 不要使用账户密码

### 2. 限制令牌权限
- 只授予必要的权限
- 定期轮换访问令牌

### 3. 保护Secrets
- 不要在代码中硬编码secrets
- 不要在日志中打印secret值
- 定期审查和更新secrets

### 4. 分支保护
- 对main分支启用保护规则
- 要求Pull Request审查
- 要求状态检查通过

## 📊 监控和维护

### 1. 定期检查
- 监控工作流运行状态
- 检查Docker Hub镜像大小和层数
- 验证多架构构建

### 2. 性能优化
- 使用构建缓存
- 优化Dockerfile层
- 考虑使用多阶段构建

### 3. 更新依赖
- 定期更新GitHub Actions版本
- 更新基础镜像
- 更新构建工具

## 🎯 下一步

设置完成后，你可以：

1. **自动化部署**: 结合其他工具实现自动部署
2. **添加测试**: 在构建前运行自动化测试
3. **通知集成**: 添加Slack、邮件等通知
4. **安全扫描**: 集成容器安全扫描工具

## 📞 获取帮助

如果遇到问题：

1. 查看 [GitHub Actions文档](https://docs.github.com/en/actions)
2. 查看 [Docker Hub文档](https://docs.docker.com/docker-hub/)
3. 在项目中创建Issue并提供详细的错误信息

---

**提示**: 首次设置可能需要几分钟来验证所有配置。请耐心等待并查看工作流日志以确认一切正常运行。
