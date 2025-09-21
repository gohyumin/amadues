#!/usr/bin/env python3
"""
检查AWS S3实际存储情况
"""
import boto3
import os
from botocore.exceptions import ClientError, NoCredentialsError
import json

def check_s3_bucket_contents():
    """检查S3存储桶的实际内容"""
    print("🔍 检查S3存储桶实际内容...")
    print("=" * 60)
    
    try:
        # 配置S3客户端
        s3_client = boto3.client('s3', region_name=os.environ.get("AWS_REGION", "ap-southeast-1"))
        bucket_name = "chatbot-audio-url"
        
        print(f"🗄️  存储桶: {bucket_name}")
        print(f"🌍 区域: {os.environ.get('AWS_REGION', 'ap-southeast-1')}")
        
        # 列出存储桶中的所有对象
        print("\n📋 列出存储桶中的所有对象...")
        
        paginator = s3_client.get_paginator('list_objects_v2')
        page_iterator = paginator.paginate(Bucket=bucket_name)
        
        total_objects = 0
        for page in page_iterator:
            if 'Contents' in page:
                for obj in page['Contents']:
                    total_objects += 1
                    print(f"  📄 {obj['Key']}")
                    print(f"     大小: {obj['Size']} bytes")
                    print(f"     修改时间: {obj['LastModified']}")
                    print(f"     存储类型: {obj.get('StorageClass', 'STANDARD')}")
                    print()
        
        if total_objects == 0:
            print("❌ 存储桶为空！没有找到任何文件")
            
            # 检查存储桶权限
            print("\n🔍 检查存储桶权限...")
            try:
                # 尝试获取存储桶ACL
                acl_response = s3_client.get_bucket_acl(Bucket=bucket_name)
                print("✅ 有权限查看存储桶ACL")
                
                # 尝试获取存储桶策略
                try:
                    policy_response = s3_client.get_bucket_policy(Bucket=bucket_name)
                    print("✅ 有权限查看存储桶策略")
                except ClientError as e:
                    if e.response['Error']['Code'] == 'NoSuchBucketPolicy':
                        print("ℹ️  存储桶没有设置策略")
                    else:
                        print(f"⚠️  无法获取存储桶策略: {e.response['Error']['Code']}")
                        
            except ClientError as e:
                print(f"❌ 权限检查失败: {e.response['Error']['Code']}")
                
        else:
            print(f"✅ 找到 {total_objects} 个对象")
            
        # 检查特定文件夹
        print("\n🗂️  检查音频文件夹结构...")
        folders_to_check = [
            "audio/",
            "audio/user/",
            "audio/bot/",
            "audio/test/"
        ]
        
        for folder in folders_to_check:
            response = s3_client.list_objects_v2(
                Bucket=bucket_name,
                Prefix=folder,
                MaxKeys=5
            )
            
            count = response.get('KeyCount', 0)
            print(f"  📁 {folder}: {count} 个对象")
            
            if count > 0 and 'Contents' in response:
                for obj in response['Contents'][:3]:  # 只显示前3个
                    print(f"    - {obj['Key']} ({obj['Size']} bytes)")
                if count > 3:
                    print(f"    ... 还有 {count - 3} 个对象")
        
        return total_objects > 0
        
    except NoCredentialsError:
        print("❌ AWS凭证未配置")
        return False
    except ClientError as e:
        error_code = e.response['Error']['Code']
        print(f"❌ S3错误: {error_code}")
        
        if error_code == 'NoSuchBucket':
            print("💡 存储桶不存在！")
            print("   请检查存储桶名称或在AWS控制台创建存储桶")
        elif error_code == 'AccessDenied':
            print("💡 访问被拒绝！")
            print("   请检查AWS凭证和IAM权限")
        
        return False
    except Exception as e:
        print(f"❌ 其他错误: {str(e)}")
        return False

def check_aws_credentials():
    """检查AWS凭证配置"""
    print("\n🔐 检查AWS凭证配置...")
    print("=" * 60)
    
    try:
        # 检查环境变量
        aws_access_key = os.environ.get('AWS_ACCESS_KEY_ID')
        aws_secret_key = os.environ.get('AWS_SECRET_ACCESS_KEY')
        aws_region = os.environ.get('AWS_REGION')
        
        print("📋 环境变量:")
        print(f"  AWS_ACCESS_KEY_ID: {'已设置' if aws_access_key else '未设置'}")
        print(f"  AWS_SECRET_ACCESS_KEY: {'已设置' if aws_secret_key else '未设置'}")
        print(f"  AWS_REGION: {aws_region or '未设置 (默认: ap-southeast-1)'}")
        
        # 检查AWS配置文件
        print("\n📄 检查AWS配置文件...")
        import pathlib
        aws_config_path = pathlib.Path.home() / '.aws' / 'credentials'
        aws_config_config_path = pathlib.Path.home() / '.aws' / 'config'
        
        print(f"  凭证文件 (~/.aws/credentials): {'存在' if aws_config_path.exists() else '不存在'}")
        print(f"  配置文件 (~/.aws/config): {'存在' if aws_config_config_path.exists() else '不存在'}")
        
        # 尝试获取当前身份
        print("\n🆔 获取当前AWS身份...")
        sts_client = boto3.client('sts', region_name=os.environ.get("AWS_REGION", "ap-southeast-1"))
        identity = sts_client.get_caller_identity()
        
        print(f"  用户ARN: {identity.get('Arn')}")
        print(f"  账户ID: {identity.get('Account')}")
        print(f"  用户ID: {identity.get('UserId')}")
        
        return True
        
    except ClientError as e:
        print(f"❌ 无法获取AWS身份: {e.response['Error']['Code']}")
        return False
    except Exception as e:
        print(f"❌ 凭证检查失败: {str(e)}")
        return False

def test_s3_permissions():
    """测试S3权限"""
    print("\n🔧 测试S3权限...")
    print("=" * 60)
    
    try:
        s3_client = boto3.client('s3', region_name=os.environ.get("AWS_REGION", "ap-southeast-1"))
        bucket_name = "chatbot-audio-url"
        
        # 测试各种权限
        permissions = {
            "ListBucket": False,
            "GetObject": False,
            "PutObject": False,
            "DeleteObject": False
        }
        
        # 测试列出对象
        try:
            s3_client.list_objects_v2(Bucket=bucket_name, MaxKeys=1)
            permissions["ListBucket"] = True
            print("✅ ListBucket权限正常")
        except ClientError as e:
            print(f"❌ ListBucket权限失败: {e.response['Error']['Code']}")
        
        # 测试上传对象 (创建一个小测试文件)
        test_key = "test-permissions.txt"
        test_content = b"Test file for permissions check"
        
        try:
            s3_client.put_object(
                Bucket=bucket_name,
                Key=test_key,
                Body=test_content
            )
            permissions["PutObject"] = True
            print("✅ PutObject权限正常")
            
            # 测试获取对象
            try:
                s3_client.get_object(Bucket=bucket_name, Key=test_key)
                permissions["GetObject"] = True
                print("✅ GetObject权限正常")
            except ClientError as e:
                print(f"❌ GetObject权限失败: {e.response['Error']['Code']}")
            
            # 测试删除对象
            try:
                s3_client.delete_object(Bucket=bucket_name, Key=test_key)
                permissions["DeleteObject"] = True
                print("✅ DeleteObject权限正常")
            except ClientError as e:
                print(f"❌ DeleteObject权限失败: {e.response['Error']['Code']}")
                
        except ClientError as e:
            print(f"❌ PutObject权限失败: {e.response['Error']['Code']}")
        
        # 总结权限状态
        print(f"\n📊 权限总结:")
        for perm, status in permissions.items():
            print(f"  {perm}: {'✅ 正常' if status else '❌ 失败'}")
        
        return all(permissions.values())
        
    except Exception as e:
        print(f"❌ 权限测试失败: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 开始AWS S3详细检查...")
    
    # 检查AWS凭证
    creds_ok = check_aws_credentials()
    
    if creds_ok:
        # 检查S3权限
        perms_ok = test_s3_permissions()
        
        # 检查存储桶内容
        has_content = check_s3_bucket_contents()
        
        print("\n" + "=" * 60)
        print("📊 检查结果汇总:")
        print(f"  AWS凭证: {'✅ 正常' if creds_ok else '❌ 失败'}")
        print(f"  S3权限: {'✅ 正常' if perms_ok else '❌ 失败'}")
        print(f"  存储桶内容: {'✅ 有文件' if has_content else '❌ 空的'}")
        
        if not has_content:
            print("\n💡 建议:")
            print("  1. 检查应用是否真正调用了上传函数")
            print("  2. 检查上传过程中是否有错误")
            print("  3. 确认AWS区域设置正确")
            print("  4. 检查存储桶名称是否正确")
    else:
        print("\n❌ 请先配置AWS凭证")
    
    print("\n🏁 检查完成!")