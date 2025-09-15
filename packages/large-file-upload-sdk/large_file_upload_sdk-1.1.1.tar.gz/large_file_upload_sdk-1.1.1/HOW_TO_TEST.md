# 🧪 SDK认证功能测试指南

## 📋 测试前准备

### 1. 确保服务器已部署
- 按照 `DEPLOY_AUTH.md` 部署服务器
- 确认服务器正常运行：`python main.py`

### 2. 安装最新SDK
```bash
pip install --upgrade large-file-upload-sdk==1.0.3
```

### 3. 获取测试参数
- **服务器地址**: 你的服务器URL (如: `http://your-server:8000`)
- **用户ID**: 任意整数 (如: `12345`)

## 🚀 快速测试（推荐）

### 使用快速测试脚本
```bash
# 1. 修改 quick_auth_test.py 中的配置
#    SERVER_URL = "http://your-server:8000"  # 改为你的服务器
#    USER_ID = 12345                         # 改为你的用户ID

# 2. 运行测试
python quick_auth_test.py
```

**预期输出**:
```
🚀 快速SDK认证测试
服务器: http://your-server:8000
用户ID: 12345

📡 初始化SDK...
✅ API Key申请成功！
用户ID: 12345
API Key: ak_12345_abc123def456_xyz789
请妥善保存您的API Key，后续可直接使用。
✅ SDK初始化成功！

📝 创建测试文件...
✅ 测试文件创建成功！

📤 开始上传...
🎉 上传成功！
文件ID: abcd1234
文件URL: http://your-server:8000/api/download/quick_test.txt

✅ 认证系统工作正常！
```

## 🔬 完整测试

### 使用完整测试脚本
```bash
# 1. 修改 test_auth_sdk.py 中的配置
python test_auth_sdk.py
```

包含以下测试场景：
- ✅ 用户ID自动申请API Key
- ✅ 使用已有API Key
- ✅ 面向对象使用方式
- ✅ 错误场景处理

## 📝 手动测试代码

### 最简单的使用方式
```python
import file_upload_sdk

# 自动申请API Key方式
file_upload_sdk.init_sdk(
    base_url='http://your-server:8000',
    user_id=12345  # 你的用户ID
)

# 上传文件
result = file_upload_sdk.upload_file('test.txt', 'my-dataset')
print(result)
```

### 使用已有API Key
```python
import file_upload_sdk

# 如果你已经有API Key
file_upload_sdk.init_sdk(
    base_url='http://your-server:8000',
    api_key='ak_12345_abc123def456_xyz789'  # 你的API Key
)

# 上传文件
result = file_upload_sdk.upload_file('test.txt', 'my-dataset')
print(result)
```

### 面向对象方式
```python
import file_upload_sdk

# 创建SDK实例
sdk = file_upload_sdk.FileUploadSDK(
    base_url='http://your-server:8000',
    user_id=12345
)

# 上传文件
result = sdk.upload_file('test.txt', 'my-dataset')
print(result)
```

## 🔍 测试验证点

### ✅ 成功标志
1. **API Key申请成功**: 控制台输出API Key
2. **上传成功**: 返回 `{"success": True, "file_id": "...", "file_url": "..."}`
3. **文件存在**: 在服务器路径找到文件 `/cpfs-nfs/sais/data-plaza-svc/datasets/{dataset_name}/full/download/`

### ❌ 常见错误

#### 连接错误
```
❌ 测试失败: 申请API Key时发生错误: HTTPConnectionPool(host='your-server', port=8000): Max retries exceeded
```
**解决**: 检查服务器地址和端口，确认服务器已启动

#### 认证错误
```
❌ 上传失败: 无效的API Key
```
**解决**: 检查API Key格式，重新申请

#### 权限错误
```
❌ 上传失败: 无权访问数据集: my-dataset
```
**解决**: 检查数据集权限设置

#### 文件大小错误
```
❌ 上传失败: 文件大小超过用户限制
```
**解决**: 检查文件大小和用户限制

## 🛠 故障排除

### 1. 检查服务器日志
```bash
# 在服务器上查看日志
tail -f server.log
# 或查看控制台输出
```

### 2. 测试API直接调用
```bash
# 测试API Key申请
curl -X POST "http://your-server:8000/api/auth/generate-key" \
  -H "Content-Type: application/json" \
  -d '{"user_id": 12345, "key_name": "测试"}'

# 测试文件检查API
curl -X POST "http://your-server:8000/api/upload/check" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your_api_key" \
  -d '{"file_id": "test", "file_name": "test.txt", "file_size": 100, "total_chunks": 1, "dataset_name": "test"}'
```

### 3. 检查用户数据
```bash
# 查看用户数据文件
cat users.json
```

### 4. 重置测试环境
```bash
# 删除用户数据重新开始
rm users.json
# 重启服务器
python main.py
```

## 📞 获取帮助

如果测试中遇到问题：
1. 检查 `DEPLOY_AUTH.md` 部署文档
2. 查看服务器日志输出
3. 确认网络连接和服务器状态
4. 验证配置参数是否正确

测试成功后，认证系统就可以正常使用了！🎉
