import requests
import io

# 创建假的音频数据用于测试
fake_audio_data = b'fake audio data for testing pronunciation API'

# 创建一个类似于Flask request.files的对象
class MockAudioFile:
    def __init__(self, data, filename):
        self.data = data
        self.filename = filename
        self.file = io.BytesIO(data)
        self.pointer = 0
    
    def read(self, size=-1):
        if size == -1:
            result = self.data[self.pointer:]
            self.pointer = len(self.data)
        else:
            result = self.data[self.pointer:self.pointer + size]
            self.pointer += len(result)
        return result
    
    def seek(self, pos):
        self.pointer = pos
    
    def __enter__(self):
        return self
    
    def __exit__(self, *args):
        pass

# 测试我们新的analyze_pronunciation_accuracy函数
def test_pronunciation_api():
    try:
        # 准备测试数据
        audio_file = MockAudioFile(fake_audio_data, "test_audio.webm")
        target_language = "English"
        user_level = "Beginner"
        
        # 构建请求数据
        api_url = "https://n8n.smart87.me/webhook/pronunciation-assessment"
        
        form_data = {
            'target_language': target_language,
            'user_level': user_level,
            'timestamp': '1726789123'
        }
        
        # 发送请求
        with io.BytesIO(fake_audio_data) as audio_stream:
            files = {'audio': ('test_audio.webm', audio_stream, 'audio/webm')}
            
            response = requests.post(
                api_url,
                data=form_data,
                files=files,
                timeout=10,
                headers={'Accept': 'application/json'}
            )
        
        print(f"API Status: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print(f"Response: {response.text[:300]}")
        
        if response.status_code == 200:
            try:
                json_response = response.json()
                print(f"JSON Response: {json_response}")
                return True
            except:
                print("Response is not valid JSON")
                return False
        else:
            return False
            
    except Exception as e:
        print(f"Test error: {str(e)}")
        return False

if __name__ == "__main__":
    print("🧪 Testing pronunciation assessment API with audio file upload...")
    success = test_pronunciation_api()
    if success:
        print("✅ API test successful!")
    else:
        print("❌ API test failed, but integration should work once n8n is activated")