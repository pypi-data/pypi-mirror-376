"""
带认证的文件上传SDK使用示例
"""
import file_upload_sdk

def main():
    # 示例1：使用user_id自动申请API Key（推荐新用户）
    print("=== 示例1：自动申请API Key ===")
    try:
        # 初始化SDK，提供用户ID，SDK会自动申请API Key
        file_upload_sdk.init_sdk(
            base_url='https://file-upload-server.ai4s.com.cn',
            user_id=12345  # 替换为您的用户ID
        )
        
        # 上传文件
        result = file_upload_sdk.upload_file(
            file_path='test_upload.txt',
            dataset_name='my-dataset'
        )
        
        if result['success']:
            print("✅ 上传成功！")
            print(f"文件ID: {result['file_id']}")
            print(f"文件URL: {result['file_url']}")
        else:
            print(f"❌ 上传失败: {result['error']}")
            
    except Exception as e:
        print(f"错误: {e}")
    
    print("\n" + "="*50 + "\n")
    
    # 示例2：使用已有的API Key（推荐老用户）
    print("=== 示例2：使用已有API Key ===")
    try:
        # 如果您已经有API Key，可以直接使用
        api_key = "ak_12345_abc123def456_xyz789"  # 替换为您的API Key
        
        file_upload_sdk.init_sdk(
            base_url='https://file-upload-server.ai4s.com.cn',
            api_key=api_key
        )
        
        # 上传文件
        result = file_upload_sdk.upload_file(
            file_path='test_upload.txt',
            dataset_name='my-dataset'
        )
        
        if result['success']:
            print("✅ 上传成功！")
            print(f"文件ID: {result['file_id']}")
            print(f"文件URL: {result['file_url']}")
        else:
            print(f"❌ 上传失败: {result['error']}")
            
    except Exception as e:
        print(f"错误: {e}")
    
    print("\n" + "="*50 + "\n")
    
    # 示例3：面向对象的使用方式
    print("=== 示例3：面向对象使用 ===")
    try:
        # 创建SDK实例
        sdk = file_upload_sdk.FileUploadSDK(
            base_url='https://file-upload-server.ai4s.com.cn',
            user_id=12345  # 或使用 api_key="your_api_key"
        )
        
        # 上传文件
        result = sdk.upload_file(
            file_path='test_upload.txt',
            dataset_name='my-dataset',
            progress_callback=lambda p: print(f"上传进度: {p:.1f}%")
        )
        
        if result['success']:
            print("✅ 上传成功！")
            print(f"文件ID: {result['file_id']}")
            print(f"文件URL: {result['file_url']}")
        else:
            print(f"❌ 上传失败: {result['error']}")
            
    except Exception as e:
        print(f"错误: {e}")


if __name__ == "__main__":
    # 创建测试文件
    with open('test_upload.txt', 'w', encoding='utf-8') as f:
        f.write("这是一个测试文件，用于验证带认证的文件上传功能。\n")
        f.write("测试时间：2024年\n")
    
    main()
