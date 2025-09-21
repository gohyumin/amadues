from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, Response
import os
import re
import boto3
from botocore.exceptions import ClientError, NoCredentialsError, EndpointConnectionError
import requests
from flask_bcrypt import Bcrypt
import uuid
from boto3.dynamodb.conditions import Key
from werkzeug.utils import secure_filename
import json
import tempfile
import time
from decimal import Decimal

# ===== VisionLingo =====
import cv2
import numpy as np
import threading
import warnings
from utils.aws_rekognition_infer import AWSRekognitionDetector
from utils.overlay import draw_dots_and_labels
from translate import translate_text

# Suppress OpenCV warnings
os.environ['OPENCV_LOG_LEVEL'] = 'ERROR'
warnings.filterwarnings('ignore')

app = Flask(__name__)
app.secret_key = "dev-secret-change-me"
bcrypt = Bcrypt(app)

# AWS S3 客户端配置 - 用于存储音频文件
# 你已经创建了名为 "chatbot-audio-url" 的S3存储桶
s3_client = boto3.client('s3', region_name=os.environ.get("AWS_REGION", "ap-southeast-1"))
S3_BUCKET_NAME = "chatbot-audio-url"

# DynamoDB setup (uses environment or local credentials)
DYNAMODB_TABLE = os.environ.get("DDB_USERS_TABLE", "Users")
EMAIL_GSI = os.environ.get("DDB_EMAIL_GSI", "email-index")
dynamodb = boto3.resource("dynamodb", region_name=os.environ.get("AWS_REGION", "ap-southeast-1"))
users_table = dynamodb.Table(DYNAMODB_TABLE)
PREFS_TABLE = os.environ.get("DDB_PREFS_TABLE", "users_preferences")
prefs_table = dynamodb.Table(PREFS_TABLE)

# 聊天记录DynamoDB表配置
# 你已经创建了名为 "chatbot_logs" 的DynamoDB表
# 表结构：
# - users_id (Partition Key): 用户ID
# - chatbot_logs_id (Sort Key): 聊天记录唯一ID
# - sender: 发送者 ('user' 或 'bot')
# - timestamp: 消息时间戳
# - message: 消息内容 (JSON格式，包含type和content)
CHATBOT_LOGS_TABLE = "chat_logs"
chatbot_logs_table = dynamodb.Table(CHATBOT_LOGS_TABLE)

# Simple in-memory storage for learning check-ins (in production, use database)
learning_checkins = {}  # {user_id: [{'date': 'YYYY-MM-DD', 'timestamp': '...'}]}

# ===== VisionLingo =====
class CameraManager:
    def __init__(self):
        self.current_camera = None
        self.camera_type = None  # 'laptop', 'phone', or 'photo'
        self.phone_ip = "192.168.0.180"  # Updated IP
        self.phone_port = "8080"
        self.camera_lock = threading.Lock()
        self.uploaded_frame = None  # Store uploaded photo frame
        
    def get_phone_url(self):
        return f"http://{self.phone_ip}:{self.phone_port}/video"
    
    def test_camera(self, camera_source, camera_type):
        try:
            test_cap = cv2.VideoCapture(camera_source)
            if test_cap.isOpened():
                ret, frame = test_cap.read()
                test_cap.release()
                if ret and frame is not None:
                    print(f"✅ {camera_type} camera test successful")
                    return True
            test_cap.release()
            print(f"❌ {camera_type} camera test failed")
            return False
        except Exception as e:
            print(f"❌ {camera_type} camera error: {e}")
            return False
    
    def switch_to_laptop(self):
        with self.camera_lock:
            if self.current_camera:
                self.current_camera.release()
            
            for i in range(3):
                if self.test_camera(i, f"Laptop Camera {i}"):
                    self.current_camera = cv2.VideoCapture(i)
                    self.camera_type = 'laptop'
                    self.uploaded_frame = None
                    print(f"🎥 Switched to Laptop Camera {i}")
                    return True
            
            print("❌ No laptop camera available")
            return False
    
    def switch_to_phone(self, ip=None, port=None):
        if ip:
            self.phone_ip = ip
        if port:
            self.phone_port = port
        
        phone_url = self.get_phone_url()
        
        with self.camera_lock:
            if self.current_camera:
                self.current_camera.release()
            
            if self.test_camera(phone_url, "Phone Camera"):
                self.current_camera = cv2.VideoCapture(phone_url)
                self.camera_type = 'phone'
                self.uploaded_frame = None
                print(f"📱 Switched to Phone Camera: {phone_url}")
                return True
            else:
                print(f"❌ Phone camera not available at {phone_url}")
                self.switch_to_laptop()
                return False
    
    def switch_to_photo(self, photo_frame):
        """Switch to uploaded photo mode"""
        with self.camera_lock:
            if self.current_camera:
                self.current_camera.release()
                self.current_camera = None
            
            self.uploaded_frame = cv2.resize(photo_frame, (640, 480))
            self.camera_type = 'photo'
            print("🖼️ Switched to uploaded photo")
            return True
    
    def read_frame(self):
        with self.camera_lock:
            if self.camera_type == 'photo' and self.uploaded_frame is not None:
                return True, self.uploaded_frame.copy()
            elif self.current_camera and self.current_camera.isOpened():
                ret, frame = self.current_camera.read()
                if ret:
                    return True, frame
        return False, None
    
    def get_status(self):
        if self.camera_type == 'photo':
            return "🖼️ Uploaded Photo ✅"
        elif self.current_camera and self.current_camera.isOpened():
            return f"{self.camera_type.title()} Camera ✅"
        return "No Camera ❌"

# Initialize camera manager
camera_manager = CameraManager()
camera_manager.switch_to_laptop()

# Selection state
selected_object_idx = None
current_detections = []

# Initialize AWS Rekognition detector
detector = AWSRekognitionDetector()

# Initialize camera manager
camera_manager = CameraManager()
camera_manager.switch_to_laptop()

# Selection state for object detection
selected_object_idx = None
current_detections = []

def gen_frames():
    """Generate frames with object detection using HARDCODED translations"""
    global selected_object_idx, current_detections
    while True:
        success, frame = camera_manager.read_frame()
        if not success or frame is None:
            # Handle error frames
            error_frame = np.zeros((480, 640, 3), dtype=np.uint8)
            cv2.putText(error_frame, "Camera Error - Check Connection", 
                       (120, 220), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
            ret, buffer = cv2.imencode('.jpg', error_frame)
            frame_bytes = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            time.sleep(0.1)
            continue

        try:
            frame = cv2.resize(frame, (640, 480))
            # Get raw detections from AWS Rekognition
            raw_detections = detector.infer(frame)
            
            # ✅ Transform detections with HARDCODED translations
            current_detections = []
            for detection in raw_detections:
                # Extract from AWS detector format
                label = detection.get('label', 'Unknown')
                confidence = detection.get('conf', 0.0)
                
                # Format object names properly
                english_name = label.replace('_', ' ').title()
                
                # ✅ USE HARDCODED TRANSLATIONS from ZH_CN_MAP
                chinese_name = get_hardcoded_translation(english_name)
                
                print(f"🔍 Hardcoded Translation: {english_name} → {chinese_name}")
                
                # Create detection in expected format
                formatted_detection = {
                    'en': english_name,      # English name  
                    'cn': chinese_name,      # Hardcoded Chinese translation
                    'confidence': confidence # 0-1 format
                }
                current_detections.append(formatted_detection)
            
            # Draw overlay with raw detections
            frame = draw_dots_and_labels(
                frame, raw_detections,
                selected_idx=selected_object_idx,
                show_confidence=False
            )

            # Add camera status overlay
            camera_info = f"{camera_manager.camera_type.upper()} CAM" if camera_manager.camera_type else "NO CAM"
            color = (255, 0, 0) if camera_manager.camera_type == 'laptop' else \
                    (0, 255, 0) if camera_manager.camera_type == 'phone' else \
                    (0, 165, 255) if camera_manager.camera_type == 'photo' else (255, 255, 255)
                    
            cv2.putText(frame, camera_info, (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            cv2.putText(frame, camera_info, (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 1)

        except Exception as e:
            print(f"❌ Detection error: {e}")
            current_detections = []

        ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 90])
        frame_bytes = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        time.sleep(0.033)  # ~30 FPS


def get_hardcoded_translation(english_text):
    """Get hardcoded translation from ZH_CN_MAP in translate.py"""
    from translate import ZH_CN_MAP
    
    # Try exact match first
    if english_text.lower() in ZH_CN_MAP:
        return ZH_CN_MAP[english_text.lower()]
    
    # Try common AWS Rekognition labels
    aws_to_common = {
        'Adult': 'person',
        'Female': 'female', 
        'Woman': 'female',
        'Man': 'person',
        'Male': 'person',
        'Human': 'person',
        'Face': 'face',
        'Head': 'head',
        'Selfie': 'person',  # Fallback to person
        'Portrait': 'person', # Fallback to person
        'Photography': 'person',
        'Smile': 'smile',
        'Machine': 'laptop',  # Fallback to laptop
        'Electronics': 'laptop',
        'Device': 'laptop'
    }
    
    # Map AWS labels to common dictionary terms
    common_term = aws_to_common.get(english_text, english_text.lower())
    
    # Look up in ZH_CN_MAP
    translation = ZH_CN_MAP.get(common_term, english_text)
    
    return translation


# ===== S3 和 DynamoDB 辅助函数 =====

def get_username_by_user_id(user_id):
    """
    根据用户ID获取用户名
    
    参数:
    - user_id: 用户ID
    
    返回:
    - 用户名字符串，失败返回"Unknown User"
    """
    try:
        response = users_table.get_item(Key={'id': user_id})
        if 'Item' in response:
            return response['Item'].get('username', 'Unknown User')
        else:
            return 'Unknown User'
    except Exception as e:
        print(f"❌ 获取用户名失败: {str(e)}")
        return 'Unknown User'

def get_user_language_preferences(user_id):
    """
    根据用户ID获取用户偏好设置
    
    参数:
    - user_id: 用户ID
    
    返回:
    - 用户偏好字典，失败返回默认设置
    """
    try:
        response = prefs_table.get_item(Key={'users_id': user_id})
        if 'Item' in response:
            prefs = response['Item']
            return {
                'target_language': prefs.get('target_language', 'English'),
                'native_language': prefs.get('native_language', 'Chinese'),
                'level': prefs.get('level', 'Beginner'),
                'age': prefs.get('age', ''),
                'country': prefs.get('country', ''),
                'interest1': prefs.get('interest1', ''),
                'interest2': prefs.get('interest2', '')
            }
        else:
            print(f"⚠️ 用户 {user_id} 的偏好设置未找到，使用默认设置")
            return {
                'target_language': 'English',
                'native_language': 'Chinese', 
                'level': 'Beginner'
            }
    except Exception as e:
        print(f"❌ 获取用户偏好失败: {str(e)}")
        return {
            'target_language': 'English',
            'native_language': 'Chinese',
            'level': 'Beginner'
        }

def analyze_pronunciation_accuracy(audio_file, target_language, user_level):
    """
    分析语音发音准确率 - 使用与frontend.html相同的webhook调用方式
    将音频转换为base64格式发送JSON数据
    
    参数:
    - audio_file: 音频文件对象或音频文件路径
    - target_language: 目标语言
    - user_level: 用户水平
    
    返回:
    - 分析结果字典
    """
    try:
        import base64
        
        # 准备发送到发音评估API的数据
        api_url = "https://n8n.smart87.me/webhook/pronunciation-assessment"
        
        print(f"🎤 开始处理音频文件...")
        
        # 读取音频文件内容
        if hasattr(audio_file, 'read'):
            # 如果是文件对象，重置指针到开始并读取内容
            audio_file.seek(0)
            audio_content = audio_file.read()
            filename = getattr(audio_file, 'filename', 'audio.webm')
            print(f"📁 处理文件对象: {filename}")
        else:
            # 如果是文件路径，读取文件
            with open(audio_file, 'rb') as f:
                audio_content = f.read()
            filename = audio_file
            print(f"📁 处理文件路径: {filename}")
        
        print(f"📊 音频文件大小: {len(audio_content)} bytes")
        
        # 转换音频为base64（使用与frontend.html相同的方法）
        print(f"🔄 转换音频为base64...")
        base64_audio = base64.b64encode(audio_content).decode('utf-8')
        print(f"📝 Base64编码长度: {len(base64_audio)}")
        
        # 准备JSON负载（与frontend.html相同的格式）
        payload = {
            'audio': base64_audio,
            'referenceText': "各个国家有各个国家的国歌",  # 使用相同的参考文本
            'language': "zh-CN"  # 使用相同的语言设置
        }
        
        print(f"📤 发送JSON数据到webhook...")
        print(f"🌐 目标URL: {api_url}")
        
        # 记录API请求开始时间
        api_start_time = time.time()
        
        # 发送POST请求（与frontend.html相同的方式）
        response = requests.post(
            api_url,
            json=payload,  # 使用JSON而不是form-data
            timeout=30,
            headers={
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
        )
        
        # 计算API响应时间
        api_response_time = round(time.time() - api_start_time, 2)
        
        print(f"📥 响应状态: {response.status_code}")
        print(f"⏱️ API响应时间: {api_response_time} 秒")
        
        # 检查响应状态
        response.raise_for_status()
        
        # 解析API响应 - 处理数组格式的响应（参考frontend.html的逻辑）
        api_result = response.json()
        print(f"✅ 收到API响应: {type(api_result)}")
        
        # 添加详细的API响应调试
        print(f"🔍 完整API响应结构:")
        print(json.dumps(api_result, indent=2, ensure_ascii=False))
        
        # 使用与frontend.html相同的逻辑处理数组响应
        if not isinstance(api_result, list):
            print("❌ API响应不是数组格式")
            return {
                'error': True,
                'message': 'API响应格式错误，期待数组格式',
                'transcript': '',
                'target_language': target_language,
                'user_level': user_level,
                'analysis_timestamp': int(time.time()),
                'api_response': api_result
            }
        
        # 查找包含语音评估数据的对象（有'success'和'data'字段）
        speech_assessment_response = None
        for item in api_result:
            if (isinstance(item, dict) and 
                'success' in item and 
                'data' in item and 
                isinstance(item.get('data'), dict)):
                speech_assessment_response = item
                break
        
        # 查找包含文本响应的对象（有'text'字段）
        text_response = None
        for item in api_result:
            if isinstance(item, dict) and 'text' in item:
                text_response = item
                break
        
        print(f"🔍 找到语音评估响应: {speech_assessment_response is not None}")
        print(f"🔍 找到文本响应: {text_response is not None}")
        
        if not speech_assessment_response:
            print("❌ 在API响应中未找到语音评估数据")
            return {
                'error': True,
                'message': '未找到语音评估数据',
                'transcript': '',
                'target_language': target_language,
                'user_level': user_level,
                'analysis_timestamp': int(time.time()),
                'api_response': api_result
            }
        
        # 检查是否成功
        success = speech_assessment_response.get('success', True)
        print(f"🔍 API成功状态: {success}")
        
        if not success:
            print("❌ API响应显示处理失败")
            return {
                'error': True,
                'message': 'API响应显示处理失败',
                'transcript': '',
                'target_language': target_language,
                'user_level': user_level,
                'analysis_timestamp': int(time.time()),
                'api_response': api_result
            }
        
        # 提取实际数据对象
        actual_data = speech_assessment_response.get('data', {})
        
        print(f"🔍 提取到的actual_data类型: {type(actual_data)}")
        print(f"🔍 actual_data内容: {actual_data}")
        
        # 提取转录文本
        transcript = ''
        reference_text = ''
        
        if isinstance(actual_data, dict):
            print(f"🔍 actual_data的所有字段: {list(actual_data.keys())}")
            
            # 直接提取recognizedText和referenceText
            transcript = actual_data.get('recognizedText', '').strip()
            reference_text = actual_data.get('referenceText', '').strip()
            
            print(f"✅ 识别文本 (recognizedText): '{transcript}'")
            print(f"✅ 参考文本 (referenceText): '{reference_text}'")
            
        else:
            print(f"❌ actual_data不是字典类型: {type(actual_data)}")
        
        # 如果仍然没有找到转录文本
        if not transcript:
            print("❌ 无法从API响应中找到转录文本")
            print(f"🔍 完整响应结构调试:")
            print(f"  - api_result类型: {type(api_result)}")
            print(f"  - speech_assessment_response类型: {type(speech_assessment_response)}")
            print(f"  - actual_data类型: {type(actual_data)}")
            if isinstance(actual_data, dict):
                print(f"  - actual_data字段: {list(actual_data.keys())}")
            
            # 使用明确的错误信息
            transcript = f"[语音识别失败] API响应解析错误"
        
        # 提取综合评分
        overall_scores = actual_data.get('overall', {}) if isinstance(actual_data, dict) else {}
        pronunciation_score = overall_scores.get('pronunciationScore', 0) if isinstance(overall_scores, dict) else 0
        accuracy_score = overall_scores.get('accuracyScore', 0) if isinstance(overall_scores, dict) else 0
        fluency_score = overall_scores.get('fluencyScore', 0) if isinstance(overall_scores, dict) else 0
        completeness_score = overall_scores.get('completenessScore', 0) if isinstance(overall_scores, dict) else 0
        prosody_score = overall_scores.get('prosodyScore', 0) if isinstance(overall_scores, dict) else 0
        
        # 提取词汇详情
        words_data = actual_data.get('words', []) if isinstance(actual_data, dict) else []
        
        print(f"🎯 识别文本: {transcript}")
        print(f"🎯 参考文本: {reference_text}")
        print(f"📊 发音得分: {pronunciation_score}")
        print(f"📊 准确度: {accuracy_score}")
        print(f"📊 流利度: {fluency_score}")
        print(f"� 完整度: {completeness_score}")
        print(f"📊 韵律得分: {prosody_score}")
        print(f"�📝 词汇数量: {len(words_data) if isinstance(words_data, list) else 0}")
        
        print(f"📝 词汇数量: {len(words_data) if isinstance(words_data, list) else 0}")
        
        # 处理文本响应（AI反馈）
        ai_feedback_text = ''
        if text_response and isinstance(text_response, dict) and 'text' in text_response:
            ai_feedback_text = text_response.get('text', '')
            print(f"🤖 AI反馈: {ai_feedback_text[:100]}..." if len(ai_feedback_text) > 100 else f"🤖 AI反馈: {ai_feedback_text}")
        
        # 构建返回结果，保持与原有格式兼容
        analysis_result = {
            'transcript': transcript,
            'reference_text': reference_text,
            'target_language': target_language,
            'user_level': user_level,
            'pronunciation_score': pronunciation_score,
            'accuracy_score': accuracy_score,
            'fluency_score': fluency_score,
            'completeness_score': completeness_score,  # 添加完整度评分
            'prosody_score': prosody_score,  # 添加韵律评分
            'api_response_time': api_response_time,  # 添加API响应时间
            'ai_feedback': ai_feedback_text,  # 添加AI反馈
            'feedback': {
                'overall': ai_feedback_text if ai_feedback_text else f"识别文本: {transcript}",
                'strengths': [],
                'improvements': [],
                'suggestions': []
            },
            'analysis_timestamp': int(time.time()),
            'api_response': api_result,  # 保存完整的API响应用于调试
            'words_analysis': words_data  # 保存词汇分析数据
        }
        
        return analysis_result
        
    except requests.exceptions.Timeout:
        # 处理超时错误
        return {
            'error': True,
            'message': '发音评估API请求超时，请稍后重试',
            'transcript': '',
            'target_language': target_language,
            'user_level': user_level,
            'pronunciation_score': 0,
            'feedback': {
                'overall': '系统暂时无法分析，请稍后重试',
                'strengths': [],
                'improvements': [],
                'suggestions': ['请检查网络连接后重试']
            },
            'analysis_timestamp': int(time.time())
        }
        
    except requests.exceptions.RequestException as e:
        # 处理其他网络请求错误
        return {
            'error': True,
            'message': f'发音评估API请求失败: {str(e)}',
            'transcript': '',
            'target_language': target_language,
            'user_level': user_level,
            'pronunciation_score': 0,
            'feedback': {
                'overall': '系统暂时无法分析，请稍后重试',
                'strengths': [],
                'improvements': [],
                'suggestions': ['请检查网络连接后重试']
            },
            'analysis_timestamp': int(time.time())
        }
        
    except json.JSONDecodeError:
        # 处理JSON解析错误
        return {
            'error': True,
            'message': '发音评估API返回数据格式错误',
            'transcript': '',
            'target_language': target_language,
            'user_level': user_level,
            'pronunciation_score': 0,
            'feedback': {
                'overall': '系统暂时无法分析，请稍后重试',
                'strengths': [],
                'improvements': [],
                'suggestions': ['请联系系统管理员']
            },
            'analysis_timestamp': int(time.time())
        }
        
    except Exception as e:
        # 处理其他未知错误
        return {
            'error': True,
            'message': f'发音评估过程中出现未知错误: {str(e)}',
            'transcript': '',
            'target_language': target_language,
            'user_level': user_level,
            'pronunciation_score': 0,
            'feedback': {
                'overall': '系统暂时无法分析，请稍后重试',
                'strengths': [],
                'improvements': [],
                'suggestions': ['请联系系统管理员']
            },
            'analysis_timestamp': int(time.time())
        }

def upload_audio_to_s3(audio_file, user_id, is_bot_audio=False):
    """
    上传音频文件到S3存储桶
    
    参数:
    - audio_file: 上传的文件对象
    - user_id: 用户ID
    - is_bot_audio: 是否是机器人音频
    
    返回:
    - S3文件的完整URL，失败返回None
    """
    try:
        timestamp = str(int(time.time() * 1000))
        
        # 获取文件名，支持不同类型的文件对象
        if hasattr(audio_file, 'filename') and audio_file.filename:
            original_filename = secure_filename(audio_file.filename)
        elif hasattr(audio_file, 'name') and audio_file.name:
            # 如果是普通文件对象，从路径中提取文件名
            original_filename = secure_filename(os.path.basename(audio_file.name))
        else:
            original_filename = "recording.webm"
        
        unique_filename = f"{timestamp}_{original_filename}"
        
        # 根据文件扩展名判断音频格式和Content-Type
        file_extension = original_filename.lower().split('.')[-1] if '.' in original_filename else 'webm'
        
        content_type_map = {
            'wav': 'audio/wav',
            'webm': 'audio/webm', 
            'mp3': 'audio/mpeg',
            'ogg': 'audio/ogg',
            'flac': 'audio/flac',
            'm4a': 'audio/mp4'
        }
        
        content_type = content_type_map.get(file_extension, 'audio/wav')  # 默认为WAV
        
        # 根据音频类型选择存储路径
        if is_bot_audio:
            s3_key = f"audio/bot/{user_id}/{unique_filename}"
        else:
            s3_key = f"audio/user/{user_id}/{unique_filename}"
        
        print(f"📤 开始上传音频到S3:")
        print(f"   存储桶: {S3_BUCKET_NAME}")
        print(f"   文件路径: {s3_key}")
        print(f"   Content-Type: {content_type}")
        
        # 上传文件到S3
        s3_client.upload_fileobj(
            audio_file,
            S3_BUCKET_NAME,
            s3_key,
            ExtraArgs={
                'ContentType': content_type,  # 使用检测到的Content-Type
                'CacheControl': 'max-age=31536000'
            }
        )
        
        # 生成S3文件URL
        s3_url = f"https://{S3_BUCKET_NAME}.s3.{os.environ.get('AWS_REGION', 'ap-southeast-1')}.amazonaws.com/{s3_key}"
        
        print(f"✅ 音频上传成功 ({file_extension.upper()}): {s3_url}")
        print(f"🎵 Content-Type: {content_type}")
        return s3_url
        
    except Exception as e:
        print(f"❌ S3上传失败详细错误: {type(e).__name__}: {str(e)}")
        import traceback
        print(f"🔍 错误堆栈:")
        traceback.print_exc()
        return None

def save_chat_message_to_dynamodb(users_id, sender, message_content, message_type="text", audio_url=None, pronunciation_assessment=None):
    """
    保存聊天消息到DynamoDB
    
    参数:
    - users_id: 用户ID (Partition Key)
    - sender: 发送者名称 (用户名或 'system')
    - message_content: 消息文本内容
    - message_type: 消息类型 ('text' 或 'audio')
    - audio_url: 音频文件的S3 URL (可选)
    - pronunciation_assessment: 发音评估结果 (可选)
    
    返回:
    - 保存成功返回chatbot_logs_id，失败返回None
    """
    try:
        # 生成唯一的聊天记录ID和时间戳
        chatbot_logs_id = str(uuid.uuid4())
        timestamp = int(time.time())
        
        # 构建消息JSON格式
        message_json = {
            "type": message_type,
            "content": message_content
        }
        
        # 如果有音频URL，添加到消息中
        if audio_url:
            message_json["audio_url"] = audio_url
            
        # 如果有发音评估结果，添加到消息中
        if pronunciation_assessment:
            message_json["pronunciation_assessment"] = pronunciation_assessment
        
        # 构建要保存的数据项
        item = {
            'users_id': users_id,              # Partition Key
            'chatbot_logs_id': chatbot_logs_id, # Sort Key
            'sender': sender,
            'timestamp': timestamp,
            'message': message_json  # 直接存储为普通 JSON 对象
        }
        
        # 保存到DynamoDB (使用 Table resource 确保正确的数据类型转换)
        response = chatbot_logs_table.put_item(Item=item)
        
        print(f"✅ 聊天记录保存成功: 用户{users_id}, 发送者{sender}, 类型{message_type}")
        print(f"📊 保存的 message 数据: {message_json}")  # 显示实际保存的 JSON
        print(f"🔑 生成的 chatbot_logs_id: {chatbot_logs_id}")  # 显示生成的ID
        return chatbot_logs_id
        
    except Exception as e:
        print(f"❌ DynamoDB保存失败: {str(e)}")
        return None

def get_chat_history_from_dynamodb(users_id, limit=20, last_chatbot_logs_id=None):
    """
    从DynamoDB获取用户的聊天历史记录
    
    参数:
    - users_id: 用户ID
    - limit: 返回的消息数量限制
    - last_chatbot_logs_id: 上次查询的最后一个记录ID，用于分页
    
    返回:
    - 聊天历史记录列表
    """
    try:
        # 构建查询参数
        query_params = {
            'KeyConditionExpression': Key('users_id').eq(users_id),
            'Limit': limit
        }
        
        # 如果提供了last_chatbot_logs_id，则从该位置开始查询
        if last_chatbot_logs_id:
            query_params['ExclusiveStartKey'] = {
                'users_id': users_id,
                'chatbot_logs_id': last_chatbot_logs_id
            }
        
        # 执行查询
        response = chatbot_logs_table.query(**query_params)
        
        # 转换消息格式
        messages = []
        for item in response['Items']:
            # 直接使用JSON对象，无需解析字符串
            message_data = item['message']  # 直接获取JSON对象
            
            formatted_message = {
                'chatbot_logs_id': item['chatbot_logs_id'],
                'sender': item['sender'],
                'message_type': message_data.get('type', 'text'),
                'message_content': message_data.get('content', ''),
                'timestamp': item['timestamp']
            }
            
            # 如果有音频URL，添加到响应中
            if 'audio_url' in message_data:
                formatted_message['audio_url'] = message_data['audio_url']
            
            messages.append(formatted_message)
        
        # 按时间戳和发送者排序：确保用户消息在前，系统回复在后
        # 首先按时间戳排序，然后在相同时间段内，用户消息优先于系统消息
        messages.sort(key=lambda x: (x['timestamp'], x['sender'] == 'system'))
        
        print(f"✅ 获取聊天历史成功: 用户{users_id}, 共{len(messages)}条消息")
        return {
            'messages': messages,
            'has_more': 'LastEvaluatedKey' in response,
            'last_chatbot_logs_id': response.get('LastEvaluatedKey', {}).get('chatbot_logs_id')
        }
        
    except Exception as e:
        print(f"❌ 获取聊天历史失败: {str(e)}")
        return {'messages': [], 'has_more': False, 'last_chatbot_logs_id': None}
    
def translate_text(text, target_language='Chinese', source_language='English'):
    """Simple translation fallback function"""
    translations = {
        'Person': '人', 'people': '人们', 'man': '男人', 'woman': '女人',
        'Cup': '杯子', 'mug': '马克杯', 'glass': '玻璃杯',
        'Bottle': '瓶子', 'water bottle': '水瓶',
        'Chair': '椅子', 'seat': '座位',
        'Book': '书', 'notebook': '笔记本',
        'Cell Phone': '手机', 'Mobile Phone': '手机', 'smartphone': '智能手机',
        'Laptop': '笔记本电脑', 'Computer': '电脑',
        'Car': '汽车', 'vehicle': '车辆',
        'Clock': '钟表', 'watch': '手表',
        'Dog': '狗', 'puppy': '小狗',
        'Cat': '猫', 'kitten': '小猫',
        'Table': '桌子', 'desk': '书桌',
        'Bed': '床',
        'Door': '门',
        'Window': '窗户',
        'Mouse': '鼠标',
        'Keyboard': '键盘',
        'Monitor': '显示器',
        'Bag': '包',
        'Shoe': '鞋',
        'Glasses': '眼镜'
    }
    return translations.get(text, text)  # Return original if no translation found

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/login", methods=["POST"])
def login():
    email = request.form.get("email", "").strip()
    password = request.form.get("password", "")
    if not email or not password:
        flash("Email and password are required.", "danger")
        return redirect(url_for("register_page", tab="login"))
    try:
        resp = users_table.query(IndexName=EMAIL_GSI, KeyConditionExpression=Key("email").eq(email))
        items = resp.get("Items", [])
        user = items[0] if items else None
        if not user:
            flash("Invalid email or password.", "danger")
            return redirect(url_for("register_page", tab="login"))
        if bcrypt.check_password_hash(user.get("password_hash", ""), password):
            session["user_id"] = user.get("id")
            session["username"] = user.get("username")
            session["email"] = user.get("email")
        else:
            flash("Invalid email or password.", "danger")
            return redirect(url_for("register_page", tab="login"))
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        print(f"DynamoDB ClientError - Code: {error_code}, Message: {error_message}")
        flash(f"Login error: {error_code} - {error_message}", "danger")
        return redirect(url_for("register_page", tab="login"))
    except NoCredentialsError:
        print("AWS credentials not found")
        flash("Login error: AWS credentials not configured", "danger")
        return redirect(url_for("register_page", tab="login"))
    except EndpointConnectionError:
        print("Cannot connect to DynamoDB endpoint")
        flash("Login error: Cannot connect to database", "danger")
        return redirect(url_for("register_page", tab="login"))
    except Exception as e:
        print(f"Unexpected login error: {str(e)}")
        flash(f"Login error: {str(e)}", "danger")
        return redirect(url_for("register_page", tab="login"))
    
    # If preferences already exist, skip onboarding
    try:
        pref = prefs_table.get_item(Key={"users_id": session.get("user_id")})
        if pref.get("Item"):
            return redirect(url_for("dashboard"))
    except Exception:
        pass
    return redirect(url_for("onboarding"))

@app.route("/register", methods=["POST"])
def register():
    username = request.form.get("username", "").strip()
    email = request.form.get("email", "").strip()
    password = request.form.get("password", "")
    confirm_password = request.form.get("confirm_password", "")

    # Basic validations
    if not username or not email or not password:
        flash("Please fill in all required fields.", "danger")
        return redirect(url_for("register_page"))
    if "@" not in email:
        flash("Email must contain @.", "danger")
        return redirect(url_for("register_page"))
    if len(username) > 50 or re.search(r"\s", username):
        flash("Username must be <= 50 chars with no spaces.", "danger")
        return redirect(url_for("register_page"))
    if password != confirm_password:
        flash("Passwords do not match.", "danger")
        return redirect(url_for("register_page"))

    # Ensure email not already registered (via GSI)
    try:
        existing = users_table.query(IndexName=EMAIL_GSI, KeyConditionExpression=Key("email").eq(email))
        if existing.get("Count", 0) > 0:
            flash("Email already registered.", "danger")
            return redirect(url_for("register_page"))

        # Create user with generated id (PK)
        password_hash = bcrypt.generate_password_hash(password).decode("utf-8")
        users_table.put_item(
            Item={
                "id": str(uuid.uuid4()),
                "username": username,
                "email": email,
                "password_hash": password_hash,
            },
            ConditionExpression="attribute_not_exists(id)",
        )
        flash("Congratulations, you've registered successfully.", "success")
    except ClientError as e:
        code = e.response.get("Error", {}).get("Code", "ClientError")
        msg = e.response.get("Error", {}).get("Message", "")
        if code == "ConditionalCheckFailedException":
            flash("Username already exists.", "danger")
        else:
            flash(f"Registration error: {code} {msg}", "danger")
    except NoCredentialsError:
        flash("Registration error: No AWS credentials found. Configure AWS credentials.", "danger")
    except EndpointConnectionError as e:
        flash("Registration error: Cannot reach DynamoDB endpoint/region. Check AWS_REGION and network.", "danger")
    return redirect(url_for("register_page"))

@app.route("/service-details")
def service_details():
    return render_template("service-details.html")

@app.route("/register", methods=["GET"])
def register_page():
    return render_template("register.html")

@app.route("/onboarding")
def onboarding():
    user_name = session.get("username", "Learner")
    # If already onboarded, go straight to dashboard
    try:
        user_id = session.get("user_id")
        if user_id:
            pref = prefs_table.get_item(Key={"users_id": user_id})
            if pref.get("Item"):
                return redirect(url_for("dashboard"))
    except Exception:
        pass
    return render_template("onboarding.html", username=user_name)

@app.route("/onboarding", methods=["POST"])
def onboarding_save():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"ok": False, "error": "not_authenticated"}), 401
    data = request.get_json(silent=True) or {}
    age = data.get("age")
    country = data.get("country")
    interests = data.get("interests")
    native_language = data.get("native_language")
    target_language = data.get("target_language")
    level = data.get("level")
    
    # 将逗号分隔的interests转换为interest1和interest2
    interest1 = ""
    interest2 = ""
    if interests:
        interests_list = interests.split(',')
        interest1 = interests_list[0].strip() if len(interests_list) > 0 else ""
        interest2 = interests_list[1].strip() if len(interests_list) > 1 else ""
    
    try:
        prefs_table.put_item(Item={
            "users_id": user_id,
            "age": age,
            "country": country,
            "interest1": interest1,
            "interest2": interest2,
            "native_language": native_language,
            "target_language": target_language,
            "level": level,
        })
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

@app.route("/dashboard")
def dashboard():
    user_name = session.get("username", "Learner")
    return render_template("dashboard.html", username=user_name)

@app.route("/api/user/preferences", methods=["GET"])
def get_user_preferences():
    """Get user preferences including interests"""
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    
    try:
        pref = prefs_table.get_item(Key={"users_id": user_id})
        if pref.get("Item"):
            prefs = pref["Item"]
            return jsonify({
                "success": True,
                "preferences": {
                    "age": prefs.get("age", ""),
                    "country": prefs.get("country", ""),
                    "interest1": prefs.get("interest1", ""),
                    "interest2": prefs.get("interest2", ""),
                    "native_language": prefs.get("native_language", ""),
                    "target_language": prefs.get("target_language", ""),
                    "level": prefs.get("level", "")
                }
            })
        else:
            return jsonify({"success": False, "error": "Preferences not found"}), 404
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# Learning Check-in APIs
@app.route("/api/checkin", methods=["POST"])
def daily_checkin():
    """Daily learning check-in"""
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    
    from datetime import datetime
    today = datetime.now().strftime("%Y-%m-%d")
    timestamp = datetime.now().isoformat()
    
    # Initialize user checkins if not exists
    if user_id not in learning_checkins:
        learning_checkins[user_id] = []
    
    # Check if already checked in today
    user_records = learning_checkins[user_id]
    if any(record['date'] == today for record in user_records):
        return jsonify({"success": False, "error": "Already checked in today"})
    
    # Add checkin record
    learning_checkins[user_id].append({
        "date": today,
        "timestamp": timestamp
    })
    
    return jsonify({"success": True, "date": today})

@app.route("/api/checkin/stats", methods=["GET"])
def get_checkin_stats():
    """Get learning check-in statistics"""
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    
    from datetime import datetime, timedelta
    
    user_records = learning_checkins.get(user_id, [])
    
    # Calculate statistics
    today = datetime.now().date()
    current_month_start = today.replace(day=1)
    
    # This month checkins
    month_checkins = len([r for r in user_records 
                         if datetime.fromisoformat(r['date']).date() >= current_month_start])
    
    # Calculate current streak
    current_streak = 0
    if user_records:
        sorted_records = sorted(user_records, key=lambda x: x['date'], reverse=True)
        check_date = today
        
        for record in sorted_records:
            record_date = datetime.fromisoformat(record['date']).date()
            if record_date == check_date or record_date == check_date - timedelta(days=1):
                current_streak += 1
                check_date = record_date - timedelta(days=1)
            else:
                break
    
    # Calculate longest streak
    longest_streak = 0
    if user_records:
        sorted_records = sorted(user_records, key=lambda x: x['date'])
        current_streak_count = 1
        
        for i in range(1, len(sorted_records)):
            prev_date = datetime.fromisoformat(sorted_records[i-1]['date']).date()
            curr_date = datetime.fromisoformat(sorted_records[i]['date']).date()
            
            if (curr_date - prev_date).days == 1:
                current_streak_count += 1
            else:
                longest_streak = max(longest_streak, current_streak_count)
                current_streak_count = 1
        
        longest_streak = max(longest_streak, current_streak_count)
    
    # Check if checked in today
    today_str = today.isoformat()
    has_checked_today = any(record['date'] == today_str for record in user_records)
    
    # Get checkin dates for calendar
    checkin_dates = [r['date'] for r in user_records]
    
    return jsonify({
        "success": True,
        "stats": {
            "total_days": len(user_records),
            "current_streak": current_streak,
            "longest_streak": longest_streak,
            "this_month": month_checkins,
            "checked_today": has_checked_today
        },
        "checkin_dates": checkin_dates
    })

@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return redirect(url_for("home"))

@app.route("/chatbot")
def chatbot_page():
    if not session.get("user_id"):
        return redirect(url_for("register_page"))
    return render_template("chatbot.html")

# Chatbot APIs (集成S3和DynamoDB)
@app.route("/api/chatbot/message", methods=["POST"])
def chatbot_message():
    """
    文本聊天接口 - 保存到DynamoDB
    """
    try:
        # 检查用户是否已登录
        user_id = session.get("user_id")
        if not user_id:
            return jsonify({"error": "User not authenticated"}), 401
            
        data = request.get_json(silent=True) or {}
        text = (data.get("text") or "").strip()
        if not text:
            return jsonify({"reply": "Please type something."})
        
        print(f"💬 接收到用户 {user_id} 的文本消息: {text}")
        
        # 获取用户名
        username = get_username_by_user_id(user_id)
        
        # 保存用户消息到DynamoDB
        user_log_id = save_chat_message_to_dynamodb(
            users_id=user_id,
            sender=username,  # 使用实际用户名
            message_content=text,
            message_type="text"
        )
        
        # 生成简洁的机器人回复
        chatbot_response = f"我收到了你的消息: \"{text}\"\n\n"
        
        # 根据用户输入生成更自然的回复
        text_lower = text.lower()
        if any(word in text_lower for word in ['你好', 'hello', 'hi', '嗨']):
            chatbot_response = f"你好！很高兴和你聊天。你想练习什么呢？"
        elif any(word in text_lower for word in ['谢谢', 'thank', '感谢']):
            chatbot_response = f"不用客气！我很乐意帮助你学习。"
        elif any(word in text_lower for word in ['怎么', 'how', '如何', 'what', '什么']):
            chatbot_response = f"这是个好问题！我们可以一起探讨一下。你想了解哪个方面呢？"
        elif any(word in text_lower for word in ['学习', 'learn', 'study', '练习']):
            chatbot_response = f"学习很棒！你可以尝试和我对话来提高语言技能。"
        else:
            chatbot_response = f"明白了！继续和我聊天吧，这样可以帮助你提高语言能力。"
        
        print(f"🤖 机器人回复: {chatbot_response}")
        
        # 保存机器人回复到DynamoDB
        bot_log_id = save_chat_message_to_dynamodb(
            users_id=user_id,
            sender="system",  # 使用 "system" 而不是 "bot"
            message_content=chatbot_response,
            message_type="text"
        )
        
        return jsonify({"reply": chatbot_response})
        
    except Exception as e:
        print(f"❌ 文本聊天处理错误: {str(e)}")
        return jsonify({"error": f"服务器错误: {str(e)}"}), 500

@app.route("/api/chatbot/message-audio", methods=["POST"])
def chatbot_message_audio():
    """
    完整的语音聊天接口 - 使用与frontend.html相同的JSON格式处理
    
    工作流程：
    1. 接收JSON格式的base64音频数据
    2. 将base64音频转换为临时文件
    3. 使用语音转文字服务获取转录文本
    4. 处理聊天逻辑生成回复
    5. 保存用户消息和机器人回复到DynamoDB
    6. 返回完整的聊天响应
    """
    try:
        import base64
        import tempfile
        import os
        
        # 检查用户是否已登录
        user_id = session.get("user_id")
        if not user_id:
            return jsonify({"error": "User not authenticated"}), 401
        
        # 步骤1: 接收和验证JSON数据
        json_data = request.get_json()
        if not json_data:
            return jsonify({"error": "No JSON data received"}), 400
        
        base64_audio = json_data.get('audio')
        if not base64_audio:
            return jsonify({"error": "No audio data in JSON"}), 400
        
        print(f"📤 接收到用户 {user_id} 的base64音频数据")
        print(f"📊 Base64数据长度: {len(base64_audio)}")
        
        # 步骤2: 将base64音频转换为临时文件
        try:
            audio_data = base64.b64decode(base64_audio)
            print(f"📁 解码后音频大小: {len(audio_data)} bytes")
            
            # 创建临时文件
            with tempfile.NamedTemporaryFile(delete=False, suffix='.webm') as temp_file:
                temp_file.write(audio_data)
                temp_file_path = temp_file.name
            
            print(f"📂 创建临时文件: {temp_file_path}")
            
        except Exception as e:
            print(f"❌ Base64解码失败: {str(e)}")
            return jsonify({"error": f"Invalid base64 audio data: {str(e)}"}), 400
        
        # 生成请求唯一标识
        import hashlib
        audio_hash = hashlib.md5(audio_data).hexdigest()
        request_id = f"{user_id}_{int(time.time())}_{audio_hash[:8]}"
        
        print(f" 请求ID: {request_id}")
        
        # 步骤3: 获取用户语言学习偏好
        user_preferences = get_user_language_preferences(user_id)
        target_language = user_preferences.get('target_language', 'English')
        user_level = user_preferences.get('level', 'Beginner')
        
        # 步骤4: 语音发音评估 - 使用临时文件路径
        print(f"🎯 开始发音评估分析...")
        pronunciation_result = analyze_pronunciation_accuracy(
            audio_file=temp_file_path,  # 传递临时文件路径
            target_language=target_language,
            user_level=user_level
        )
        print(f"📊 发音评估完成: {pronunciation_result.get('pronunciation_score', 0)}分")
        
        # 步骤5: 创建一个类似文件对象来上传到S3
        class AudioFileObj:
            def __init__(self, file_path):
                self.filename = 'recording.webm'
                self._file_path = file_path
                self._file = None
                self._position = 0
            
            def read(self, size=-1):
                """读取文件内容"""
                if self._file is None:
                    self._file = open(self._file_path, 'rb')
                    self._file.seek(self._position)
                
                if size == -1:
                    data = self._file.read()
                else:
                    data = self._file.read(size)
                
                self._position = self._file.tell()
                return data
            
            def seek(self, position, whence=0):
                """设置文件指针位置"""
                if self._file is None:
                    self._file = open(self._file_path, 'rb')
                
                self._file.seek(position, whence)
                self._position = self._file.tell()
            
            def tell(self):
                """获取当前文件指针位置"""
                return self._position
            
            def close(self):
                """关闭文件"""
                if self._file:
                    self._file.close()
                    self._file = None
        
        # 使用实际文件对象上传到S3（更简单的方法）
        print(f"📂 准备上传音频文件到S3: {temp_file_path}")
        try:
            with open(temp_file_path, 'rb') as audio_file:
                user_audio_s3_url = upload_audio_to_s3(audio_file, user_id, is_bot_audio=False)
        except Exception as e:
            print(f"❌ 打开临时音频文件失败: {e}")
            user_audio_s3_url = None
        
        # 步骤6: 改进转录文本的处理
        transcript = pronunciation_result.get('transcript', '').strip()
        
        print(f"🎤 原始转录结果: '{transcript}'")
        print(f"🎤 转录结果长度: {len(transcript)}")
        print(f"🎤 转录结果是否为空: {not transcript}")
        
        # 检查是否是错误信息
        if (not transcript or 
            transcript.startswith('[语音识别失败]') or 
            transcript.startswith('[错误]') or
            transcript.startswith('(demo)')):
            
            print("⚠️ 转录失败，生成基于实际语音的回复")
            
            # 不使用demo文本，而是基于用户确实录制了语音的事实来回复
            display_transcript = "已录制语音 (转录处理中...)"
            
            chatbot_response = f"🎤 我听到了你的语音录制！\n\n"
            chatbot_response += f"虽然语音转文字服务暂时遇到了一些技术问题，但我知道你在练习发音，这很棒！\n\n"
            chatbot_response += f"📊 音频信息:\n"
            chatbot_response += f"• 音频长度: {len(audio_data)} 字节\n"
            chatbot_response += f"• 目标语言: {target_language}\n"
            chatbot_response += f"• 你的级别: {user_level}\n\n"
            
            if pronunciation_result.get('error'):
                chatbot_response += f"⚠️ 技术问题: {pronunciation_result.get('message', '未知错误')}\n\n"
            
            chatbot_response += f"✅ 继续保持练习！每一次开口都是进步！"
            
        else:
            # 成功转录，生成基于转录内容的智能回复
            print(f"✅ 转录成功: {transcript}")
            display_transcript = transcript
            
            # 构建智能回复
            score = pronunciation_result.get('pronunciation_score', 0)
            accuracy = pronunciation_result.get('accuracy_score', 0)
            fluency = pronunciation_result.get('fluency_score', 0)
            
            chatbot_response = f"🎤 我听到你说: '{transcript}'\n\n"
            
            # 根据转录内容生成更智能的回复
            if any(word in transcript.lower() for word in ['hello', 'hi', '你好', 'nihao']):
                chatbot_response += f"👋 很高兴听到你的问候！你的发音听起来不错。\n\n"
            elif any(word in transcript.lower() for word in ['how', 'what', 'where', '什么', '怎么', '哪里']):
                chatbot_response += f"🤔 我听到你在问问题，这是学习语言的好方法！\n\n"
            elif any(word in transcript.lower() for word in ['thank', 'thanks', '谢谢', 'xiexie']):
                chatbot_response += f"😊 不用客气！很高兴能帮助你学习。\n\n"
            else:
                chatbot_response += f"👍 很好！我能理解你说的内容。\n\n"
            
            if score > 0:
                chatbot_response += f"📊 发音评估:\n"
                chatbot_response += f"• 发音得分: {score}/100\n"
                chatbot_response += f"• 准确度: {accuracy}/100\n"
                chatbot_response += f"• 流利度: {fluency}/100\n\n"
                
                if score >= 80:
                    chatbot_response += f"🌟 优秀！你的发音很棒，继续保持！"
                elif score >= 60:
                    chatbot_response += f"👍 不错！多练习会让你的发音更完美。"
                else:
                    chatbot_response += f"💪 继续努力！每天练习一点，你会看到进步的。"
            else:
                chatbot_response += f"🎯 继续练习发音，你做得很好！"
        
        print(f"🎤 最终使用的转录结果: {display_transcript}")
        
        # 获取用户名
        username = get_username_by_user_id(user_id)
        
        # 步骤7: 保存用户消息到DynamoDB (JSON格式) - 包含发音评估结果
        print(f"💾 开始保存用户音频消息...")
        user_log_id = save_chat_message_to_dynamodb(
            users_id=user_id,
            sender=username,  # 使用实际用户名
            message_content=display_transcript,  # 使用处理后的转录文本
            message_type="audio",
            audio_url=user_audio_s3_url,
            pronunciation_assessment=pronunciation_result  # 添加发音评估结果
        )
        
        if not user_log_id:
            print("⚠️ 用户消息保存到DynamoDB失败")
            # 不返回错误，继续处理
        else:
            print(f"✅ 用户音频消息保存成功，ID: {user_log_id}")
        
        # 步骤8: 使用已经处理好的聊天回复，不再重新生成
        # chatbot_response 已经在步骤6中根据转录成功与否生成了合适的回复
        
        # 如果需要添加额外的调试信息(可选)
        if pronunciation_result.get('error'):
            # 在原有回复基础上添加技术信息
            chatbot_response += f"\n\n� **技术信息:**\n"
            chatbot_response += f"• 请求ID: {request_id}\n"
            chatbot_response += f"• 错误详情: {pronunciation_result.get('message', '未知错误')}\n"
        
        # 清理临时文件
        try:
            os.unlink(temp_file_path)
            print(f"🗑️ 清理临时文件: {temp_file_path}")
        except Exception as e:
            print(f"⚠️ 清理临时文件失败: {str(e)}")
        
        # 步骤9: 保存机器人回复到DynamoDB
        print(f"🤖 开始保存机器人回复...")
        bot_log_id = save_chat_message_to_dynamodb(
            users_id=user_id,
            sender="system",  # 机器人消息使用'system'作为发送者
            message_content=chatbot_response,
            message_type="text",
            audio_url=None,  # 机器人回复通常是文本
            pronunciation_assessment=None  # 机器人回复不需要发音评估
        )
        
        if not bot_log_id:
            print("⚠️ 机器人回复保存到DynamoDB失败")
        else:
            print(f"✅ 机器人回复保存成功，ID: {bot_log_id}")
        
        # 打印完整的聊天会话保存状态
        print(f"📊 聊天会话保存状态:")
        print(f"   👤 用户消息ID: {user_log_id}")
        print(f"   🤖 机器人回复ID: {bot_log_id}")
        print(f"   💾 会话完整性: {'✅ 完整' if user_log_id and bot_log_id else '⚠️ 不完整'}")
        
        # 处理单词级别的分析结果，为前端提供颜色标注信息
        words_analysis = pronunciation_result.get('words_analysis', [])
        
        # 创建单词颜色映射函数
        def get_word_color_class(word_data):
            """根据单词的错误类型和准确度返回CSS类名"""
            if not isinstance(word_data, dict):
                return 'word-normal'
                
            error_type = word_data.get('errorType', '').strip()
            error_type_en = word_data.get('errorTypeEn', '').strip()
            accuracy_score = word_data.get('accuracyScore', 0)
            
            print(f"🔍 处理单词: '{word_data.get('word', '')}', 错误类型: '{error_type}', 英文类型: '{error_type_en}', 准确度: {accuracy_score}")
            
            # 如果是遗漏（Omission），不上色
            if error_type_en == 'Omission' or error_type == '遗漏':
                print(f"  -> 遗漏单词，不上色")
                return 'word-omission'  # 特殊类，不显示颜色
            
            # 如果是正确的单词，根据准确度分数给颜色
            if error_type_en == 'None' or error_type == '正确':
                if accuracy_score >= 90:
                    print(f"  -> 优秀 (绿色)")
                    return 'word-excellent'     # 绿色 - 优秀
                elif accuracy_score >= 80:
                    print(f"  -> 良好 (蓝色)")
                    return 'word-good'          # 蓝色 - 良好  
                elif accuracy_score >= 70:
                    print(f"  -> 一般 (黄色)")
                    return 'word-fair'          # 黄色 - 一般
                elif accuracy_score > 0:
                    print(f"  -> 需要改进 (橙色)")
                    return 'word-poor'          # 橙色 - 需要改进
                else:
                    print(f"  -> 正常颜色")
                    return 'word-normal'        # 正常颜色
            else:
                # 其他错误类型，根据准确度给颜色
                if accuracy_score >= 70:
                    print(f"  -> 错误但分数高 (黄色)")
                    return 'word-fair'          # 黄色
                else:
                    print(f"  -> 错误分数低 (红色)")
                    return 'word-poor'          # 红色
        
        
        # 处理单词分析结果
        formatted_words = []
        if isinstance(words_analysis, list):
            for word_info in words_analysis:
                if isinstance(word_info, dict):
                    formatted_word = {
                        'word': word_info.get('word', ''),
                        'index': word_info.get('index', 0),
                        'errorType': word_info.get('errorType', ''),
                        'errorTypeEn': word_info.get('errorTypeEn', ''),
                        'accuracyScore': word_info.get('accuracyScore', 0),
                        'colorClass': get_word_color_class(word_info)
                    }
                    formatted_words.append(formatted_word)
        
        # 返回响应
        return jsonify({
            "reply": chatbot_response,
            "transcript": display_transcript,  # 使用处理后的转录文本
            "pronunciation_score": pronunciation_result.get('pronunciation_score', 0),
            "accuracy_score": pronunciation_result.get('accuracy_score', 0),
            "fluency_score": pronunciation_result.get('fluency_score', 0),
            "words_analysis": formatted_words,  # 添加格式化后的单词分析
            "reference_text": pronunciation_result.get('reference_text', ''),  # 参考文本
            "recognized_text": pronunciation_result.get('transcript', display_transcript),  # 识别文本
            "user_audio_url": user_audio_s3_url,  # 添加S3音频URL
            "tts_url": None  # TTS URL（如果有的话）
        })
        
    except Exception as e:
        print(f"❌ 语音聊天处理错误: {str(e)}")
        
        # 确保清理临时文件
        if 'temp_file_path' in locals():
            try:
                os.unlink(temp_file_path)
                print(f"🗑️ 异常清理临时文件: {temp_file_path}")
            except:
                pass
        
        return jsonify({"error": f"服务器错误: {str(e)}"}), 500

@app.route("/api/chatbot/history", methods=["GET"])
def chatbot_history():
    """
    获取用户聊天历史记录API
    
    支持分页查询，返回用户的所有聊天记录，包括文本和音频消息
    
    URL参数:
    - limit: 每页返回的消息数量 (默认20)
    - last_chatbot_logs_id: 上次查询的最后一个记录ID，用于分页
    """
    try:
        # 检查用户是否已登录
        user_id = session.get("user_id")
        if not user_id:
            return jsonify({"error": "User not authenticated"}), 401
        
        # 获取查询参数
        limit = int(request.args.get('limit', 20))
        last_chatbot_logs_id = request.args.get('last_chatbot_logs_id')
        
        print(f"📜 获取用户 {user_id} 的聊天历史，限制: {limit}")
        
        # 从DynamoDB获取聊天历史
        history_data = get_chat_history_from_dynamodb(user_id, limit, last_chatbot_logs_id)
        
        if not history_data['messages']:
            return jsonify({
                "success": True,
                "messages": [],
                "has_more": False,
                "message": "No chat history found"
            })
        
        # 格式化返回数据
        formatted_messages = []
        for msg in history_data['messages']:
            formatted_msg = {
                "chatbot_logs_id": msg['chatbot_logs_id'],
                "sender": msg['sender'],
                "message": msg['message_content'],
                "message_type": msg['message_type'],
                "timestamp": msg['timestamp']
            }
            
            # 如果有音频文件，添加音频URL
            if 'audio_url' in msg:
                formatted_msg['audio_url'] = msg['audio_url']
            
            formatted_messages.append(formatted_msg)
        
        print(f"✅ 聊天历史获取成功: {len(formatted_messages)} 条消息")
        
        return jsonify({
            "success": True,
            "messages": formatted_messages,
            "has_more": history_data['has_more'],
            "last_chatbot_logs_id": history_data['last_chatbot_logs_id']
        })
        
    except Exception as e:
        print(f"❌ 获取聊天历史错误: {str(e)}")
        return jsonify({
            "error": f"Failed to get chat history: {str(e)}",
            "success": False
        }), 500

# ===== 调试和验证 API =====

@app.route("/api/debug/test-connections", methods=["GET"])
def test_connections():
    """
    测试 AWS S3 和 DynamoDB 连接
    """
    results = {
        "s3_connection": False,
        "dynamodb_users_table": False,
        "dynamodb_chatbot_logs_table": False,
        "errors": []
    }
    
    # 测试 S3 连接
    try:
        s3_client.list_objects_v2(Bucket=S3_BUCKET_NAME, MaxKeys=1)
        results["s3_connection"] = True
        print(f"✅ S3 连接成功: {S3_BUCKET_NAME}")
    except Exception as e:
        error_msg = f"S3 连接失败: {str(e)}"
        results["errors"].append(error_msg)
        print(f"❌ {error_msg}")
    
    # 测试 Users 表连接
    try:
        users_table.table_status
        results["dynamodb_users_table"] = True
        print(f"✅ Users 表连接成功: {DYNAMODB_TABLE}")
    except Exception as e:
        error_msg = f"Users 表连接失败: {str(e)}"
        results["errors"].append(error_msg)
        print(f"❌ {error_msg}")
    
    # 测试 Chatbot Logs 表连接
    try:
        chatbot_logs_table.table_status
        results["dynamodb_chatbot_logs_table"] = True
        print(f"✅ Chatbot Logs 表连接成功: {CHATBOT_LOGS_TABLE}")
    except Exception as e:
        error_msg = f"Chatbot Logs 表连接失败: {str(e)}"
        results["errors"].append(error_msg)
        print(f"❌ {error_msg}")
        
        # 如果表不存在，提供创建表的信息
        if "ResourceNotFoundException" in str(e):
            results["chatbot_logs_table_missing"] = True
            results["create_table_info"] = {
                "message": "需要创建 chat_logs 表",
                "table_name": CHATBOT_LOGS_TABLE,
                "partition_key": "users_id",
                "sort_key": "chatbot_logs_id"
            }
    
    return jsonify(results)

@app.route("/api/debug/view-chatbot-logs", methods=["GET"])
def view_all_chatbot_logs():
    """
    查看所有用户的聊天记录 (调试用) - 显示原始数据格式
    """
    try:
        # 扫描整个 chatbot_logs 表 (仅用于调试，生产环境不推荐)
        response = chatbot_logs_table.scan()
        
        items = response.get('Items', [])
        
        # 不格式化，直接返回原始数据以便查看存储格式
        print(f"🔍 查看所有聊天记录: 共 {len(items)} 条")
        
        return jsonify({
            'success': True,
            'total_records': len(items),
            'raw_data': items,  # 返回原始数据
            'note': '这是原始DynamoDB数据，message字段现在是JSON对象而不是字符串'
        })
        
    except Exception as e:
        error_msg = f"查看聊天记录失败: {str(e)}"
        print(f"❌ {error_msg}")
        return jsonify({
            'success': False,
            'error': error_msg
        }), 500

@app.route("/api/debug/view-my-chatbot-logs", methods=["GET"])
def view_my_chatbot_logs():
    """
    查看当前登录用户的聊天记录
    """
    try:
        user_id = session.get("user_id")
        if not user_id:
            return jsonify({"error": "User not authenticated"}), 401
        
        # 获取用户的聊天历史
        history_data = get_chat_history_from_dynamodb(user_id, limit=50)
        
        print(f"🔍 查看用户 {user_id} 的聊天记录: 共 {len(history_data['messages'])} 条")
        
        return jsonify({
            'success': True,
            'user_id': user_id,
            'total_records': len(history_data['messages']),
            'logs': history_data['messages']
        })
        
    except Exception as e:
        error_msg = f"查看用户聊天记录失败: {str(e)}"
        print(f"❌ {error_msg}")
        return jsonify({
            'success': False,
            'error': error_msg
        }), 500

@app.route("/api/debug/test-s3-files", methods=["GET"])
def test_s3_files():
    """
    测试 S3 存储桶中的音频文件
    """
    try:
        user_id = session.get("user_id")
        if not user_id:
            return jsonify({"error": "User not authenticated"}), 401
        
        # 列出用户的音频文件
        prefix = f"audio/user/{user_id}/"
        response = s3_client.list_objects_v2(
            Bucket=S3_BUCKET_NAME,
            Prefix=prefix,
            MaxKeys=10  # 只显示最近的10个文件
        )
        
        files = []
        if 'Contents' in response:
            for obj in response['Contents']:
                file_info = {
                    'key': obj['Key'],
                    'size': obj['Size'],
                    'last_modified': obj['LastModified'].isoformat(),
                    'url': f"https://{S3_BUCKET_NAME}.s3.{os.environ.get('AWS_REGION', 'ap-southeast-1')}.amazonaws.com/{obj['Key']}"
                }
                files.append(file_info)
        
        # 也检查机器人音频文件
        bot_prefix = f"audio/bot/{user_id}/"
        bot_response = s3_client.list_objects_v2(
            Bucket=S3_BUCKET_NAME,
            Prefix=bot_prefix,
            MaxKeys=10
        )
        
        bot_files = []
        if 'Contents' in bot_response:
            for obj in bot_response['Contents']:
                file_info = {
                    'key': obj['Key'],
                    'size': obj['Size'],
                    'last_modified': obj['LastModified'].isoformat(),
                    'url': f"https://{S3_BUCKET_NAME}.s3.{os.environ.get('AWS_REGION', 'ap-southeast-1')}.amazonaws.com/{obj['Key']}"
                }
                bot_files.append(file_info)
        
        return jsonify({
            'success': True,
            'user_id': user_id,
            'bucket': S3_BUCKET_NAME,
            'user_audio_files': files,
            'bot_audio_files': bot_files,
            'total_user_files': len(files),
            'total_bot_files': len(bot_files)
        })
        
    except Exception as e:
        error_msg = f"检查 S3 文件失败: {str(e)}"
        print(f"❌ {error_msg}")
        return jsonify({
            'success': False,
            'error': error_msg
        }), 500

@app.route("/api/debug/download-s3-file", methods=["GET"])
def download_s3_file():
    """
    生成 S3 文件的预签名下载链接
    """
    try:
        user_id = session.get("user_id")
        if not user_id:
            return jsonify({"error": "User not authenticated"}), 401
        
        s3_key = request.args.get('key')
        if not s3_key:
            return jsonify({"error": "Missing 'key' parameter"}), 400
        
        # 验证用户只能访问自己的文件
        if not (s3_key.startswith(f"audio/user/{user_id}/") or s3_key.startswith(f"audio/bot/{user_id}/")):
            return jsonify({"error": "Access denied"}), 403
        
        # 生成预签名 URL（有效期1小时）
        presigned_url = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': S3_BUCKET_NAME, 'Key': s3_key},
            ExpiresIn=3600  # 1小时
        )
        
        return jsonify({
            'success': True,
            'key': s3_key,
            'presigned_url': presigned_url,
            'expires_in': 3600
        })
        
    except Exception as e:
        error_msg = f"生成下载链接失败: {str(e)}"
        print(f"❌ {error_msg}")
        return jsonify({
            'success': False,
            'error': error_msg
        }), 500


# ===== 用户管理 API =====

@app.route("/api/user/profile", methods=["GET"])
def get_user_profile():
    """
    获取当前登录用户的个人资料和偏好设置
    
    返回:
    - 当前用户的基本信息和偏好设置
    """
    try:
        # 检查用户是否已登录
        user_id = session.get("user_id")
        if not user_id:
            return jsonify({"error": "User not authenticated"}), 401
        
        # 获取用户基本信息
        user_response = users_table.get_item(Key={'id': user_id})
        if 'Item' not in user_response:
            return jsonify({"error": "User not found"}), 404
            
        user_info = user_response['Item']
        
        # 获取用户偏好设置
        prefs_response = prefs_table.get_item(Key={'users_id': user_id})
        user_preferences = {}
        
        if 'Item' in prefs_response:
            prefs_item = prefs_response['Item']
            user_preferences = {
                'target_language': prefs_item.get('target_language', ''),
                'native_language': prefs_item.get('native_language', ''),
                'level': prefs_item.get('level', ''),
                'age': prefs_item.get('age', ''),
                'country': prefs_item.get('country', ''),
                'interest1': prefs_item.get('interest1', ''),
                'interest2': prefs_item.get('interest2', '')
            }
        
        # 构建返回数据
        profile_data = {
            'success': True,
            'user': {
                'id': user_info['id'],
                'username': user_info['username'],
                'email': user_info['email'],
                'preferences': user_preferences
            }
        }
        
        print(f"✅ 获取用户资料成功: 用户{user_id}")
        return jsonify(profile_data)
        
    except Exception as e:
        error_msg = f"获取用户资料失败: {str(e)}"
        print(f"❌ {error_msg}")
        return jsonify({
            'success': False,
            'error': error_msg
        }), 500

@app.route("/api/user/preferences", methods=["POST"])
def update_user_preferences():
    """
    更新当前登录用户的偏好设置
    
    请求体:
    {
        "target_language": "目标语言",
        "native_language": "母语",
        "level": "水平",
        "age": "年龄",
        "country": "国家",
        "interest1": "兴趣1",
        "interest2": "兴趣2"
    }
    """
    try:
        # 检查用户是否已登录
        user_id = session.get("user_id")
        if not user_id:
            return jsonify({"error": "User not authenticated"}), 401
        
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        # 构建更新的偏好数据
        preferences_data = {
            'users_id': user_id,
            'target_language': data.get('target_language', ''),
            'native_language': data.get('native_language', ''),
            'level': data.get('level', ''),
            'age': data.get('age', ''),
            'country': data.get('country', ''),
            'interest1': data.get('interest1', ''),
            'interest2': data.get('interest2', '')
        }
        
        # 更新用户偏好到DynamoDB
        prefs_table.put_item(Item=preferences_data)
        
        print(f"✅ 用户偏好更新成功: 用户{user_id}")
        return jsonify({
            "success": True,
            "message": "偏好设置更新成功",
            "preferences": {k: v for k, v in preferences_data.items() if k != 'users_id'}
        })
        
    except Exception as e:
        error_msg = f"更新用户偏好失败: {str(e)}"
        print(f"❌ {error_msg}")
        return jsonify({
            'success': False,
            'error': error_msg
        }), 500
    
@app.route('/visionlingo')
def visionlingo():
    return render_template('visionlingo.html')

@app.route('/video_feed')
def video_feed():
    """Stream video with object detection overlay"""
    return Response(gen_frames(), 
                   mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/select_object', methods=['POST'])
def select_object():
    global selected_object_idx
    data = request.get_json()
    selected_object_idx = data.get('index')
    return jsonify({'success': True})

@app.route('/switch_camera', methods=['POST'])
def switch_camera():
    data = request.get_json()
    camera_type = data.get('type')
    
    if camera_type == 'laptop':
        success = camera_manager.switch_to_laptop()
    elif camera_type == 'phone':
        success = camera_manager.switch_to_phone()
    
    return jsonify({'success': success, 'status': camera_manager.get_status()})

@app.route('/upload_photo', methods=['POST'])
def upload_photo():
    """Handle photo upload and switch to photo mode"""
    try:
        if 'photo' not in request.files:
            return jsonify({'success': False, 'error': 'No photo uploaded'})
        
        file = request.files['photo']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No photo selected'})
        
        # Read image directly from upload
        image_data = file.read()
        nparr = np.frombuffer(image_data, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if frame is None:
            return jsonify({'success': False, 'error': 'Invalid image format'})
        
        # Switch camera manager to photo mode
        camera_manager.switch_to_photo(frame)
        
        # Save uploaded file (optional)
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        # Save original file
        with open(filepath, 'wb') as f:
            f.write(image_data)
        
        print(f"🖼️ Photo uploaded: {filename}")
        return jsonify({'success': True, 'filename': filename})
        
    except Exception as e:
        print(f"❌ Photo upload error: {e}")
        return jsonify({'success': False, 'error': str(e)})
    
@app.route('/log_selection', methods=['POST'])
def log_selection():
    """Log selected object and get learning content from n8n webhook"""
    try:
        data = request.get_json()
        english_name = data.get('en', '')
        chinese_name = data.get('cn', '')
        
        if not english_name or not chinese_name:
            return jsonify({
                'status': 'error', 
                'message': 'Missing English or Chinese name'
            })
        
        # Create selection data
        selection_data = {
            "cn": chinese_name,
            "en": english_name
        }
        
        # Send to n8n webhook for learning content
        webhook_url = "https://n8n.smart87.me/webhook/related-item"
        try:
            response = requests.post(
                webhook_url,
                json=selection_data,
                headers={'Content-Type': 'application/json'},
                timeout=15
            )
            
            print(f"🔍 n8n webhook status: {response.status_code}")
            print(f"🔍 n8n webhook response: {response.text}")
            
            if response.status_code == 200:
                webhook_data = response.json()
                print(f"🔍 Parsed n8n data: {webhook_data}")
                
                # ✅ FIX: Handle your n8n response format - it's an array!
                if isinstance(webhook_data, list) and len(webhook_data) > 0:
                    response_data = webhook_data[0]  # Get first item from array
                    
                    return jsonify({
                        'status': 'success',
                        'data': selection_data,
                        'related_items': response_data.get('related_items', []),
                        'example_sentences': response_data.get('example_sentences', [])
                    })
                else:
                    # Handle case where response is not an array or is empty
                    return jsonify({
                        'status': 'success',
                        'data': selection_data,
                        'related_items': [],
                        'example_sentences': []
                    })
            else:
                print(f"❌ n8n webhook failed with status: {response.status_code}")
                return jsonify({
                    'status': 'success',
                    'data': selection_data,
                    'related_items': [],
                    'example_sentences': []
                })
                
        except Exception as webhook_error:
            print(f"❌ Webhook error: {webhook_error}")
            return jsonify({
                'status': 'success',
                'data': selection_data,
                'related_items': [],
                'example_sentences': []
            })
        
    except Exception as e:
        print(f"❌ log_selection error: {e}")
        return jsonify({'status': 'error', 'message': str(e)})
    
@app.route('/get_detections')
def get_detections():
    """Get current object detections"""
    global current_detections
    return jsonify({
        'detections': current_detections,
        'camera_status': camera_manager.get_status()
    })

@app.route('/clear_selection', methods=['POST'])
def clear_selection():
    global selected_object_idx
    selected_object_idx = None
    print("🔄 Selection cleared")
    return jsonify({'status': 'cleared'})
    
@app.route('/webcam')
def webcam_section():
    """VisionLingo main page"""
    if not session.get("user_id"):
        return redirect(url_for("register_page"))
    return render_template('partial/webcam_section.html')

if __name__ == "__main__":
    print("🚀 启动 Flask 应用...")
    print(f"📊 DynamoDB 表: {CHATBOT_LOGS_TABLE}")
    print(f"🗄️  S3 存储桶: {S3_BUCKET_NAME}")
    print("🔧 调试端点:")
    print("   - GET /api/debug/test-connections (测试 AWS 连接)")
    print("   - GET /api/debug/view-chatbot-logs (查看所有聊天记录原始数据)")
    print("   - GET /api/debug/view-my-chatbot-logs (查看我的聊天记录)")
    print("   - GET /api/debug/test-s3-files (查看我的 S3 音频文件)")
    print("   - GET /api/debug/download-s3-file?key=<s3_key> (下载 S3 文件)")
    print("🔧 用户管理端点:")
    print("   - GET /api/user/profile (获取当前用户资料和偏好)")
    print("   - POST /api/user/preferences (更新当前用户偏好)")
    app.run(debug=True)