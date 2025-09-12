# File Upload SDK 安装和使用指南

## 安装方式

### 方法1：从wheel文件安装（推荐）

1. **下载SDK文件**
   ```bash
   # 下载 file_upload_sdk-1.0.0-py3-none-any.whl 文件
   ```

2. **安装SDK**
   ```bash
   pip install file_upload_sdk-1.0.0-py3-none-any.whl
   ```

### 方法2：从源码安装

1. **下载整个项目**
   ```bash
   git clone <repository-url>
   cd file-upload-server
   ```

2. **安装SDK**
   ```bash
   pip install -e .
   # 或者
   pip install .
   ```

### 方法3：直接使用源文件

1. **下载SDK文件**
   - 只需要下载 `file_upload_sdk.py` 文件

2. **安装依赖**
   ```bash
   pip install requests>=2.25.0 urllib3>=1.26.0
   ```

3. **直接导入使用**
   ```python
   # 将 file_upload_sdk.py 放在你的项目目录中
   import file_upload_sdk as api
   ```

## 使用示例

### 基础用法

```python
import file_upload_sdk as api

# 初始化SDK
api.init_sdk("http://your-server:8000")

# 上传文件
result = api.upload_file(
    file_path="/path/to/your/file.txt",
    file_name="uploaded_file.txt"
)

if result['success']:
    print(f"上传成功！文件URL: {result['file_url']}")
else:
    print(f"上传失败: {result['error']}")
```

### 带进度显示

```python
import file_upload_sdk as api

api.init_sdk("http://your-server:8000")

def show_progress(progress):
    print(f"\r上传进度: {progress:.1f}%", end="", flush=True)

result = api.upload_file(
    file_path="/path/to/large_file.zip",
    file_name="large_file.zip",
    progress_callback=show_progress
)
```

### 面向对象用法

```python
from file_upload_sdk import FileUploadSDK

sdk = FileUploadSDK(
    base_url="http://your-server:8000",
    chunk_size=5 * 1024 * 1024,  # 5MB分片
    retry_times=5
)

result = sdk.upload_file(
    file_path="/path/to/file.txt",
    file_name="file.txt",
    enable_md5_check=True
)
```

## 依赖要求

- Python >= 3.7
- requests >= 2.25.0
- urllib3 >= 1.26.0

## 功能特性

- ✅ 自动分片上传
- ✅ 断点续传
- ✅ MD5校验
- ✅ 进度回调
- ✅ 自动重试
- ✅ 错误处理

## 环境配置

使用前请确保：

1. **服务器地址正确**
2. **网络连接正常**
3. **服务器支持大文件上传**

## 故障排除

### 常见问题

1. **导入错误**
   ```bash
   pip install requests urllib3
   ```

2. **连接错误**
   - 检查服务器地址和端口
   - 确认服务器正在运行

3. **上传失败**
   - 检查文件路径是否正确
   - 确认文件大小是否超过限制

## 技术支持

如有问题请联系开发团队
