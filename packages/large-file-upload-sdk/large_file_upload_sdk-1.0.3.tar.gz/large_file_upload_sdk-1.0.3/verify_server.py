#!/usr/bin/env python3
"""
服务器验证脚本 - 验证文件上传服务是否正常工作
"""
import os
import json
import time
import hashlib
import requests
from pathlib import Path

class ServerVerifier:
    """服务器验证器"""
    
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        
    def print_step(self, step, message):
        """打印步骤信息"""
        print(f"\n{'='*60}")
        print(f"步骤 {step}: {message}")
        print('='*60)
    
    def print_result(self, success, message):
        """打印结果"""
        if success:
            print(f"✅ {message}")
        else:
            print(f"❌ {message}")
        return success
    
    def verify_health(self):
        """验证健康检查"""
        self.print_step(1, "检查服务健康状态")
        
        try:
            response = self.session.get(f"{self.base_url}/health", timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                print(f"响应: {json.dumps(data, indent=2, ensure_ascii=False)}")
                return self.print_result(True, "健康检查通过")
            else:
                return self.print_result(False, f"健康检查失败，状态码: {response.status_code}")
                
        except Exception as e:
            return self.print_result(False, f"健康检查异常: {str(e)}")
    
    def verify_service_info(self):
        """验证服务信息"""
        self.print_step(2, "获取服务信息")
        
        try:
            response = self.session.get(f"{self.base_url}/", timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                print(f"服务信息: {json.dumps(data, indent=2, ensure_ascii=False)}")
                return self.print_result(True, "服务信息获取成功")
            else:
                return self.print_result(False, f"获取服务信息失败，状态码: {response.status_code}")
                
        except Exception as e:
            return self.print_result(False, f"获取服务信息异常: {str(e)}")
    
    def verify_api_docs(self):
        """验证API文档"""
        self.print_step(3, "检查API文档")
        
        try:
            response = self.session.get(f"{self.base_url}/docs", timeout=5)
            
            if response.status_code == 200:
                return self.print_result(True, f"API文档可访问: {self.base_url}/docs")
            else:
                return self.print_result(False, f"API文档访问失败，状态码: {response.status_code}")
                
        except Exception as e:
            return self.print_result(False, f"API文档访问异常: {str(e)}")
    
    def create_test_file(self, filename="test_upload.txt", size_mb=1):
        """创建测试文件"""
        content = "这是一个测试文件，用于验证大文件上传功能。\n" * (size_mb * 1024 * 32)  # 约1MB
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return filename
    
    def verify_file_upload(self):
        """验证文件上传功能"""
        self.print_step(4, "测试文件上传功能")
        
        # 创建测试文件
        test_file = self.create_test_file("verify_test.txt", 1)
        
        try:
            file_size = os.path.getsize(test_file)
            file_id = f"verify_test_{int(time.time())}"
            
            print(f"测试文件: {test_file} ({file_size} bytes)")
            
            # 1. 检查文件状态
            print("\n1) 检查文件状态...")
            check_data = {
                "file_id": file_id,
                "file_name": "verify_test.txt",
                "file_size": file_size,
                "total_chunks": 1
            }
            
            response = self.session.post(f"{self.base_url}/api/upload/check", json=check_data)
            
            if response.status_code != 200:
                return self.print_result(False, f"文件检查失败: {response.status_code}")
            
            result = response.json()
            print(f"检查结果: {json.dumps(result, indent=2, ensure_ascii=False)}")
            
            # 2. 上传文件分片
            print("\n2) 上传文件分片...")
            with open(test_file, 'rb') as f:
                files = {'chunk_file': ('chunk', f.read(), 'application/octet-stream')}
            
            data = {
                'file_id': file_id,
                'file_name': 'verify_test.txt',
                'file_size': file_size,
                'chunk_index': 0,
                'total_chunks': 1,
                'chunk_size': file_size
            }
            
            response = self.session.post(f"{self.base_url}/api/upload/chunk", files=files, data=data)
            
            if response.status_code != 200:
                return self.print_result(False, f"分片上传失败: {response.status_code}")
            
            result = response.json()
            print(f"上传结果: {json.dumps(result, indent=2, ensure_ascii=False)}")
            
            # 3. 合并文件
            print("\n3) 合并文件...")
            merge_data = {
                "file_id": file_id,
                "file_name": "verify_test.txt",
                "total_chunks": 1
            }
            
            response = self.session.post(f"{self.base_url}/api/upload/merge", json=merge_data)
            
            if response.status_code != 200:
                return self.print_result(False, f"文件合并失败: {response.status_code}")
            
            result = response.json()
            print(f"合并结果: {json.dumps(result, indent=2, ensure_ascii=False)}")
            
            # 4. 验证下载
            if result.get('file_url'):
                print("\n4) 验证文件下载...")
                download_url = f"{self.base_url}{result['file_url']}"
                response = self.session.get(download_url)
                
                if response.status_code == 200:
                    print(f"文件下载成功，大小: {len(response.content)} bytes")
                    return self.print_result(True, "文件上传和下载功能验证成功")
                else:
                    return self.print_result(False, f"文件下载失败: {response.status_code}")
            
            return self.print_result(True, "文件上传功能验证成功")
            
        except Exception as e:
            return self.print_result(False, f"文件上传测试异常: {str(e)}")
        
        finally:
            # 清理测试文件
            if os.path.exists(test_file):
                os.remove(test_file)
    
    def verify_sdk_integration(self):
        """验证SDK集成"""
        self.print_step(5, "测试SDK集成")
        
        try:
            # 导入SDK
            import file_upload_sdk as api
            
            # 初始化SDK
            api.init_sdk(self.base_url)
            
            # 创建测试文件
            test_file = self.create_test_file("sdk_test.txt", 0.5)  # 0.5MB
            
            print(f"使用SDK上传文件: {test_file}")
            
            # 上传文件
            result = api.upload_file(
                file_path=test_file,
                file_name="sdk_test.txt"
            )
            
            print(f"SDK上传结果: {json.dumps(result, indent=2, ensure_ascii=False)}")
            
            # 清理测试文件
            if os.path.exists(test_file):
                os.remove(test_file)
            
            if result.get('success'):
                return self.print_result(True, "SDK集成验证成功")
            else:
                return self.print_result(False, f"SDK上传失败: {result.get('error')}")
                
        except ImportError:
            return self.print_result(False, "SDK模块未找到，请确保file_upload_sdk.py在当前目录")
        except Exception as e:
            return self.print_result(False, f"SDK测试异常: {str(e)}")
    
    def run_all_verifications(self):
        """运行所有验证"""
        print(f"🚀 开始验证文件上传服务: {self.base_url}")
        
        results = []
        
        # 执行所有验证步骤
        results.append(self.verify_health())
        results.append(self.verify_service_info())
        results.append(self.verify_api_docs())
        results.append(self.verify_file_upload())
        results.append(self.verify_sdk_integration())
        
        # 总结结果
        self.print_step("总结", "验证结果汇总")
        
        passed = sum(results)
        total = len(results)
        
        print(f"\n验证通过: {passed}/{total}")
        
        if passed == total:
            print("🎉 所有验证都通过了！服务运行正常。")
        else:
            print("⚠️  部分验证失败，请检查服务配置。")
        
        return passed == total


def main():
    """主函数"""
    import sys
    
    # 默认服务器地址
    server_url = "http://localhost:8000"
    
    # 如果提供了参数，使用自定义地址
    if len(sys.argv) > 1:
        server_url = sys.argv[1]
    
    print(f"验证服务器: {server_url}")
    
    verifier = ServerVerifier(server_url)
    success = verifier.run_all_verifications()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
