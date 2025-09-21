from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
import os
import re
import boto3
from botocore.exceptions import ClientError, NoCredentialsError, EndpointConnectionError
from flask_bcrypt import Bcrypt
import uuid
from boto3.dynamodb.conditions import Key
from werkzeug.utils import secure_filename
import json
import tempfile
import time
from decimal import Decimal

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
CHATBOT_LOGS_TABLE = "chatbot_logs"
chatbot_logs_table = dynamodb.Table(CHATBOT_LOGS_TABLE)

# Simple in-memory storage for learning check-ins (in production, use database)
learning_checkins = {}  # {user_id: [{'date': 'YYYY-MM-DD', 'timestamp': '...'}]}

# ===== S3 和 DynamoDB 辅助函数 =====

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
        original_filename = secure_filename(audio_file.filename or "audio.webm")
        unique_filename = f"{timestamp}_{original_filename}"
        
        # 根据音频类型选择存储路径
        if is_bot_audio:
            s3_key = f"audio/bot/{user_id}/{unique_filename}"
        else:
            s3_key = f"audio/user/{user_id}/{unique_filename}"
        
        # 上传文件到S3
        s3_client.upload_fileobj(
            audio_file,
            S3_BUCKET_NAME,
            s3_key,
            ExtraArgs={
                'ContentType': 'audio/webm',
                'CacheControl': 'max-age=31536000'
            }
        )
        
        # 生成S3文件URL
        s3_url = f"https://{S3_BUCKET_NAME}.s3.{os.environ.get('AWS_REGION', 'ap-southeast-1')}.amazonaws.com/{s3_key}"
        
        print(f"✅ 音频上传成功: {s3_url}")
        return s3_url
        
    except Exception as e:
        print(f"❌ S3上传失败: {str(e)}")
        return None

def save_chat_message_to_dynamodb(users_id, sender, message_content, message_type="text", audio_url=None):
    """
    保存聊天消息到DynamoDB
    
    参数:
    - users_id: 用户ID (Partition Key)
    - sender: 发送者 ('user' 或 'bot')
    - message_content: 消息文本内容
    - message_type: 消息类型 ('text' 或 'audio')
    - audio_url: 音频文件的S3 URL (可选)
    
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
        
        # 构建要保存的数据项
        item = {
            'users_id': users_id,              # Partition Key
            'chatbot_logs_id': chatbot_logs_id, # Sort Key
            'sender': sender,
            'timestamp': timestamp,
            'message': json.dumps(message_json, ensure_ascii=False)  # JSON格式存储
        }
        
        # 保存到DynamoDB
        chatbot_logs_table.put_item(Item=item)
        
        print(f"聊天记录保存成功: 用户{users_id}, 发送者{sender}, 类型{message_type}")
        return chatbot_logs_id
        
    except Exception as e:
        print(f"DynamoDB保存失败: {str(e)}")
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
            'ScanIndexForward': False,  # 按sort key倒序 (最新的在前面)
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
            # 解析JSON格式的消息内容
            message_data = json.loads(item['message'])
            
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
        
        print(f"获取聊天历史成功: 用户{users_id}, 共{len(messages)}条消息")
        return {
            'messages': messages,
            'has_more': 'LastEvaluatedKey' in response,
            'last_chatbot_logs_id': response.get('LastEvaluatedKey', {}).get('chatbot_logs_id')
        }
        
    except Exception as e:
        print(f"获取聊天历史失败: {str(e)}")
        return {'messages': [], 'has_more': False, 'last_chatbot_logs_id': None}

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
        
        # 保存用户消息到DynamoDB
        user_log_id = save_chat_message_to_dynamodb(
            users_id=user_id,
            sender="user",
            message_content=text,
            message_type="text"
        )
        
        # 生成机器人回复
        chatbot_reply = f"You said: {text}"
        print(f"🤖 机器人回复: {chatbot_reply}")
        
        # 保存机器人回复到DynamoDB
        bot_log_id = save_chat_message_to_dynamodb(
            users_id=user_id,
            sender="bot",
            message_content=chatbot_reply,
            message_type="text"
        )
        
        return jsonify({"reply": chatbot_reply})
        
    except Exception as e:
        print(f"❌ 文本聊天处理错误: {str(e)}")
        return jsonify({"error": f"服务器错误: {str(e)}"}), 500

@app.route("/api/chatbot/message-audio", methods=["POST"])
def chatbot_message_audio():
    """
    完整的语音聊天接口 - 集成S3存储和DynamoDB记录
    
    工作流程：
    1. 接收用户上传的语音文件
    2. 上传音频文件到S3存储桶
    3. 使用语音转文字服务获取转录文本 (Demo版本)
    4. 处理聊天逻辑生成回复
    5. 保存用户消息和机器人回复到DynamoDB (JSON格式)
    6. 返回完整的聊天响应
    """
    try:
        # 检查用户是否已登录
        user_id = session.get("user_id")
        if not user_id:
            return jsonify({"error": "User not authenticated"}), 401
        
        # 步骤1: 接收和验证音频文件
        audio_file = request.files.get("audio")
        if not audio_file:
            return jsonify({"error": "No audio file received"}), 400
        
        print(f"📤 接收到用户 {user_id} 的音频文件: {audio_file.filename}")
        
        # 步骤2: 上传用户音频到S3
        audio_file.seek(0)  # 重置文件指针
        user_audio_s3_url = upload_audio_to_s3(audio_file, user_id, is_bot_audio=False)
        
        if not user_audio_s3_url:
            return jsonify({"error": "Failed to upload audio to S3"}), 500
        
        # 步骤3: 语音转文字 (STT) - Demo版本
        # 在实际生产中，这里可以集成AWS Transcribe或Azure Speech Services
        transcript = f"(demo) 从音频文件转录的文字内容"
        print(f"🎤 转录结果: {transcript}")
        
        # 步骤4: 保存用户消息到DynamoDB (JSON格式)
        user_log_id = save_chat_message_to_dynamodb(
            users_id=user_id,
            sender="user",
            message_content=transcript,
            message_type="audio",
            audio_url=user_audio_s3_url
        )
        
        if not user_log_id:
            print("⚠️ 用户消息保存到DynamoDB失败")
        
        # 步骤5: 处理聊天逻辑生成机器人回复
        if transcript and not transcript.startswith("(demo)") and not "错误" in transcript:
            # 这里可以集成你的聊天机器人逻辑
            chatbot_response = f"我听到你说：{transcript}。这是我的回复。"
        else:
            # Demo 回复
            chatbot_response = "我收到了你的语音消息！这是一个演示回复。"
        
        print(f"🤖 机器人回复: {chatbot_response}")
        
        # 步骤6: 保存机器人回复到DynamoDB (JSON格式)
        bot_log_id = save_chat_message_to_dynamodb(
            users_id=user_id,
            sender="bot",
            message_content=chatbot_response,
            message_type="text"
        )
        
        if not bot_log_id:
            print("⚠️ 机器人回复保存到DynamoDB失败")
        
        # 步骤7: 返回完整响应
        response_data = {
            "success": True,
            "reply": chatbot_response,
            "transcript": transcript,
            "user_audio_url": user_audio_s3_url,
            "bot_audio_url": None  # 暂时不生成机器人语音
        }
        
        # 为了兼容前端，也包含原有的字段名
        response_data["tts_url"] = None
        
        print(f"✅ 音频聊天处理完成，用户: {user_id}")
        return jsonify(response_data)
        
    except Exception as e:
        print(f"❌ 音频聊天处理错误: {str(e)}")
        return jsonify({
            "error": f"服务器错误: {str(e)}",
            "success": False
        }), 500

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

if __name__ == "__main__":
    app.run(debug=True)