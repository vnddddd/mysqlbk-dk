# 更新日志

## [修复版本] - 2025-06-03

### 🐛 Bug修复

#### 1. 调度时间格式错误修复
- **问题**: Docker部署时出现 `Invalid time format for a daily job` 错误
- **原因**: schedule库期望 `"04:00"` 格式，但代码生成了 `"4:00"`
- **修复**: 在 `src/scheduler.py` 第84行，使用 `f"{hour_int:02d}:00"` 确保两位数格式
- **影响**: 解决了容器启动失败的问题

#### 2. B2上传失败修复
- **问题**: 上传到B2时出现 `'_io.BufferedReader' object has no attribute 'get_content_length'` 错误
- **原因**: 使用了不兼容的 `bucket.upload()` 方法
- **修复**: 在 `src/b2_uploader.py` 第68-72行，改用 `bucket.upload_local_file()` 方法
- **影响**: 解决了备份文件无法上传到B2的问题

### ✨ 功能改进

#### 3. 简化文件命名和目录结构
- **更改**: 修改了B2上传的文件命名和目录结构
- **之前**: 
  - 文件名: `backup_mysql.sqlpub.com:3306_alist12_20250603`
  - 位置: 存储桶根目录
- **现在**: 
  - 文件名: `backup_alist12_20250603_151338.sql.gz` (保持原始格式)
  - 位置: `mysql-backups/` 目录下
- **修改文件**: 
  - `src/main.py` 第192-194行: 简化远程文件名生成逻辑
  - `src/b2_uploader.py` 第81-105行: 更新文件列表方法以支持新目录结构
- **优势**: 
  - 文件名更简洁易读
  - 统一的目录结构便于管理
  - 保持了原始备份文件的时间戳信息

### 📁 文件结构变化

#### B2存储桶结构
```
neo-api/
└── mysql-backups/
    ├── backup_caoxian_20250603_151338.sql.gz
    ├── backup_alist12_20250603_151338.sql.gz
    └── ...
```

#### 本地备份文件命名
- 格式: `backup_{database}_{timestamp}.sql.gz`
- 示例: `backup_alist12_20250603_151338.sql.gz`
- 时间戳格式: `YYYYMMDD_HHMMSS`

### 🔧 技术细节

#### 调度器修复
```python
# 修复前
return f"{hour}:00"  # 生成 "4:00"

# 修复后  
hour_int = int(hour)
return f"{hour_int:02d}:00"  # 生成 "04:00"
```

#### B2上传修复
```python
# 修复前
with open(file_path, 'rb') as file_data:
    file_info = self.bucket.upload(file_data, remote_filename, ...)

# 修复后
file_info = self.bucket.upload_local_file(
    local_file=file_path,
    file_name=remote_filename,
    content_type='application/gzip'
)
```

#### 文件命名修复
```python
# 修复前
remote_filename = f"backup_{group_name}_{name_parts[1]}_{name_parts[2]}"

# 修复后
original_filename = os.path.basename(backup_file)
remote_filename = f"mysql-backups/{original_filename}"
```

### ✅ 验证结果

1. **调度器**: 成功设置时间 `使用schedule库调度备份任务: 每天 04:00`
2. **B2上传**: 使用推荐的API方法，避免了兼容性问题
3. **文件结构**: 备份文件现在上传到 `mysql-backups/` 目录，保持原始文件名

### 🚀 部署说明

1. 重新构建Docker镜像: `docker build -t mysqlbk-dk .`
2. 使用现有的环境变量配置运行容器
3. 备份文件将自动上传到B2存储桶的 `mysql-backups/` 目录下
4. 文件清理功能会自动清理该目录下的过期文件

### 📝 注意事项

- 现有的备份文件（如果在根目录）不会自动迁移到新目录
- 清理功能现在只会清理 `mysql-backups/` 目录下的文件
- 文件名格式保持与本地备份文件一致，便于识别和管理
