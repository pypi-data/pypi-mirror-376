"""
快速认证测试脚本 - 最简单的测试方式
"""
import file_upload_sdk

def main():
    print("🚀 快速SDK认证测试")
    print("-" * 40)
    
    # 配置信息 - 请修改为你的实际值
    SERVER_URL = "http://your-server:8000"  # 修改为你的服务器地址
    USER_ID = 12345                         # 修改为你的用户ID
    
    print(f"服务器: {SERVER_URL}")
    print(f"用户ID: {USER_ID}")
    print()
    
    try:
        # 1. 初始化SDK（自动申请API Key）
        print("📡 初始化SDK...")
        file_upload_sdk.init_sdk(
            base_url=SERVER_URL,
            user_id=USER_ID
        )
        print("✅ SDK初始化成功！")
        
        # 2. 创建测试文件
        print("\n📝 创建测试文件...")
        with open('quick_test.txt', 'w', encoding='utf-8') as f:
            f.write("Hello from SDK with authentication!\n")
            f.write("This is a test file for auth system.\n")
            f.write("测试中文内容\n")
        print("✅ 测试文件创建成功！")
        
        # 3. 上传文件
        print("\n📤 开始上传...")
        result = file_upload_sdk.upload_file(
            file_path='quick_test.txt',
            dataset_name='quick-test'
        )
        
        # 4. 检查结果
        if result.get('success'):
            print("🎉 上传成功！")
            print(f"文件ID: {result.get('file_id')}")
            print(f"文件URL: {result.get('file_url')}")
            print("\n✅ 认证系统工作正常！")
        else:
            print(f"❌ 上传失败: {result.get('error')}")
            
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        print("\n可能的原因:")
        print("1. 服务器地址不正确")
        print("2. 服务器未启动")
        print("3. 网络连接问题")
        print("4. 用户ID无效")
    
    finally:
        # 清理测试文件
        try:
            import os
            if os.path.exists('quick_test.txt'):
                os.remove('quick_test.txt')
                print("\n🧹 清理测试文件")
        except:
            pass

if __name__ == "__main__":
    main()
