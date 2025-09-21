#!/usr/bin/env python3
"""
测试修复后的S3上传功能
"""

import os
import sys
import tempfile
import base64

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入应用的上传函数
from app import upload_audio_to_s3, s3_client, S3_BUCKET_NAME

def test_s3_upload_fix():
    """测试修复后的S3上传功能"""
    print("🧪 测试修复后的S3上传功能...")
    print("=" * 50)
    
    # 1. 创建测试音频数据
    test_audio_data = b"fake_webm_audio_data_for_testing_12345"
    print(f"📊 测试数据大小: {len(test_audio_data)} bytes")
    
    # 2. 创建临时文件（模拟真实场景）
    with tempfile.NamedTemporaryFile(delete=False, suffix='.webm') as temp_file:
        temp_file.write(test_audio_data)
        temp_file_path = temp_file.name
    
    print(f"📁 临时文件路径: {temp_file_path}")
    
    try:
        # 3. 测试上传功能
        user_id = "test_user_123"
        
        print(f"\n🚀 开始测试上传...")
        with open(temp_file_path, 'rb') as audio_file:
            s3_url = upload_audio_to_s3(audio_file, user_id, is_bot_audio=False)
        
        if s3_url:
            print(f"\n✅ 上传测试成功!")
            print(f"🔗 S3 URL: {s3_url}")
            
            # 4. 验证文件是否真的存在于S3中
            print(f"\n🔍 验证文件是否存在于S3中...")
            
            # 从URL提取S3 key
            s3_key = s3_url.split('.com/')[-1]
            print(f"📁 S3 Key: {s3_key}")
            
            try:
                response = s3_client.head_object(Bucket=S3_BUCKET_NAME, Key=s3_key)
                print(f"✅ 文件确实存在于S3中!")
                print(f"📊 文件大小: {response['ContentLength']} bytes")
                print(f"📅 上传时间: {response['LastModified']}")
                print(f"🎵 Content-Type: {response.get('ContentType', 'unknown')}")
                
                # 5. 清理测试文件
                print(f"\n🗑️ 清理测试文件...")
                s3_client.delete_object(Bucket=S3_BUCKET_NAME, Key=s3_key)
                print(f"✅ 测试文件已从S3删除")
                
                return True
                
            except Exception as e:
                print(f"❌ 验证S3文件存在时失败: {e}")
                return False
        else:
            print(f"\n❌ 上传测试失败 - 返回了None")
            return False
            
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # 清理临时文件
        try:
            os.unlink(temp_file_path)
            print(f"🧹 临时文件已清理: {temp_file_path}")
        except:
            pass

def test_base64_to_s3_workflow():
    """测试完整的base64到S3的工作流程"""
    print(f"\n🔄 测试完整的base64到S3工作流程...")
    print("=" * 50)
    
    # 1. 模拟前端发送的base64音频数据
    original_audio_data = b"test_webm_audio_content_from_frontend"
    base64_audio = base64.b64encode(original_audio_data).decode('utf-8')
    
    print(f"📤 模拟base64音频数据长度: {len(base64_audio)}")
    
    try:
        # 2. 解码base64（模拟应用中的流程）
        audio_data = base64.b64decode(base64_audio)
        print(f"📥 解码后音频大小: {len(audio_data)} bytes")
        
        # 3. 创建临时文件
        with tempfile.NamedTemporaryFile(delete=False, suffix='.webm') as temp_file:
            temp_file.write(audio_data)
            temp_file_path = temp_file.name
        
        # 4. 上传到S3
        user_id = "test_base64_user"
        with open(temp_file_path, 'rb') as audio_file:
            s3_url = upload_audio_to_s3(audio_file, user_id, is_bot_audio=False)
        
        if s3_url:
            print(f"✅ base64到S3工作流程测试成功!")
            print(f"🔗 S3 URL: {s3_url}")
            
            # 清理测试文件
            s3_key = s3_url.split('.com/')[-1]
            s3_client.delete_object(Bucket=S3_BUCKET_NAME, Key=s3_key)
            print(f"🗑️ 测试文件已清理")
            
            return True
        else:
            print(f"❌ base64到S3工作流程测试失败")
            return False
            
    except Exception as e:
        print(f"❌ base64工作流程测试失败: {e}")
        return False
    
    finally:
        try:
            os.unlink(temp_file_path)
        except:
            pass

if __name__ == "__main__":
    print("🎯 S3上传功能修复验证测试")
    print("=" * 60)
    
    # 测试1: 基本上传功能
    test1_result = test_s3_upload_fix()
    
    # 测试2: 完整工作流程
    test2_result = test_base64_to_s3_workflow()
    
    print(f"\n" + "=" * 60)
    print(f"📊 测试结果总结:")
    print(f"   基本上传功能: {'✅ 通过' if test1_result else '❌ 失败'}")
    print(f"   完整工作流程: {'✅ 通过' if test2_result else '❌ 失败'}")
    
    if test1_result and test2_result:
        print(f"\n🎉 所有测试通过！S3上传功能应该已修复")
        print(f"💡 现在可以测试你的应用了")
    else:
        print(f"\n⚠️ 部分测试失败，需要进一步调试")