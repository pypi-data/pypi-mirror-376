# 带认证功能的文件上传服务器部署指南

## 🚀 新功能说明

### ✅ API Key认证系统
- 用户通过 `user_id` 申请 API Key
- 所有上传操作需要 API Key 认证
- 支持用户权限控制和速率限制

### ✅ SDK自动认证
- SDK可自动申请 API Key
- 支持已有 API Key 直接使用
- 用户体验简单流畅

## 📦 部署步骤

### 1. 上传代码到服务器
```bash
# 在服务器上
git pull origin dev  # 或你的分支名
```

### 2. 安装新的依赖
```bash
pip install pydantic-settings python-dotenv typing-inspection
```

### 3. 环境变量配置（可选）
```bash
# 如果需要自定义路径
export UPLOAD_BASE_DIR="/your/custom/path"
export TEMP_DIR="/your/temp/path"
```

### 4. 启动服务器
```bash
python main.py
# 或使用 uvicorn
uvicorn main:app --host 0.0.0.0 --port 8000
```

## 🧪 测试认证功能

### 1. 测试 API Key 申请
```bash
curl -X POST "http://your-server:8000/api/auth/generate-key" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 12345,
    "key_name": "测试API Key"
  }'
```

预期响应：
```json
{
  "key_id": "key_12345_1",
  "api_key": "ak_12345_abc123def456_xyz789",
  "key_name": "测试API Key",
  "permissions": ["upload"],
  "expires_at": null,
  "created_at": "2024-01-01T12:00:00"
}
```

### 2. 测试带认证的文件上传
```bash
# 先检查文件状态（需要 X-API-Key 头）
curl -X POST "http://your-server:8000/api/upload/check" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: ak_12345_abc123def456_xyz789" \
  -d '{
    "file_id": "test_123",
    "file_name": "test.txt",
    "file_size": 100,
    "total_chunks": 1,
    "dataset_name": "test-dataset"
  }'
```

### 3. 测试 SDK 使用
```python
import file_upload_sdk

# 方式1：自动申请 API Key
file_upload_sdk.init_sdk(
    base_url='http://your-server:8000',
    user_id=12345
)

# 方式2：使用已有 API Key
file_upload_sdk.init_sdk(
    base_url='http://your-server:8000',
    api_key='ak_12345_abc123def456_xyz789'
)

# 上传文件
result = file_upload_sdk.upload_file('test.txt', 'my-dataset')
print(result)
```

## 🔧 故障排除

### 问题1：服务器启动失败 - 目录权限
如果遇到 `/cpfs-nfs` 目录权限问题：
```bash
# 确保目录存在且有写权限
sudo mkdir -p /cpfs-nfs/sais/data-plaza-svc/datasets
sudo mkdir -p /cpfs-nfs/sais/data-plaza-svc/temp
sudo chown -R your-user:your-group /cpfs-nfs/sais/data-plaza-svc/
```

### 问题2：API Key 申请失败
检查服务器日志：
```bash
# 查看服务器输出
tail -f server.log
```

### 问题3：认证失败
检查请求头是否正确：
- 请求头名称：`X-API-Key`
- API Key 格式：`ak_{user_id}_{random}_{checksum}`

## 📊 用户管理

### 查看用户的 API Key
```bash
curl "http://your-server:8000/api/auth/user/12345/keys"
```

### 撤销 API Key
```bash
curl -X DELETE "http://your-server:8000/api/auth/user/12345/keys/key_12345_1"
```

### 验证 API Key
```bash
curl -X POST "http://your-server:8000/api/auth/validate-key?api_key=ak_12345_abc123def456_xyz789"
```

## 🔐 安全说明

1. **API Key 格式**: 包含用户ID和校验码，防止伪造
2. **权限控制**: 支持数据集访问限制
3. **速率限制**: 每日上传次数限制
4. **文件大小**: 用户级别的文件大小限制
5. **撤销机制**: 支持 API Key 撤销

## 📝 数据存储

用户和 API Key 数据存储在 `users.json` 文件中：
```json
{
  "users": {
    "12345": {
      "user_id": 12345,
      "username": "user_12345",
      "email": "user_12345@example.com",
      "is_active": true,
      "allowed_datasets": [],
      "max_file_size": 104857600,
      "daily_upload_limit": 100,
      "created_at": "2024-01-01T12:00:00"
    }
  },
  "api_keys": {
    "key_12345_1": {
      "key_id": "key_12345_1",
      "user_id": 12345,
      "key_name": "测试API Key",
      "key_hash": "sha256_hash_of_api_key",
      "permissions": ["upload"],
      "is_active": true,
      "created_at": "2024-01-01T12:00:00",
      "usage_count": 0,
      "daily_usage": 0
    }
  }
}
```

## 🎯 成功验证标志

如果一切正常，你应该看到：
1. ✅ 服务器正常启动（无错误日志）
2. ✅ API Key 申请成功
3. ✅ 带认证的文件上传成功
4. ✅ SDK 自动申请 API Key 成功
5. ✅ 文件正确保存到指定数据集目录

有问题随时联系！🚀
