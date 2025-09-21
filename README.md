# LinguaDaily - Powered Language Learning Platform

## 🚀 Project Overview

LinguaDaily is a comprehensive language learning platform that combines computer vision, speech recognition, pronunciation assessment, and real-time translation to create an immersive learning experience. The system uses AWS services and Speech Cognitive Services to provide personalized language education through interactive object recognition and pronunciation feedback.

## ✨ Key Features

### 🎯 Core Functions

#### **1. Real-Time Object Detection & Translation**

- **AWS Rekognition Integration**: Real-time object detection using computer vision
- **Multi-Camera Support**: Laptop camera, phone camera (IP webcam), and photo upload modes
- **Hardcoded Translation Dictionary**: Instant Chinese-English translations for detected objects
- **Interactive Selection**: Click-to-select objects for detailed learning content

#### **2. Advanced Speech Processing**

- **Speech-to-Text (STT)**: AWS Transcribe integration supporting 13+ languages
- **Text-to-Speech (TTS)**: AWS Polly with neural voices and WAV output
- **Pronunciation Assessment**: Speech SDK with detailed scoring metrics
  - Accuracy Score (0-100)
  - Fluency Score (0-100)
  - Completeness Score (0-100)
  - Prosody Score (0-100)
  - Word-level error analysis

#### **3. Personalized Learning System**

- **User Management**: Registration, authentication, and preference management
- **Learning Analytics**: Daily check-ins, progress tracking, and streak counters
- **Adaptive Curriculum**: Based on user's native language, target language, and proficiency level
- **Interest-Based Content**: Personalized learning materials via n8n webhook integration

#### **4. Multi-Language Support**

- **Primary Languages**: Chinese (Simplified/Traditional), English, Japanese, Korean
- **Extended Support**: Spanish, French, German, Portuguese, Italian, Russian, Arabic
- **Dynamic Translation**: Real-time language switching and content localization

### 🏗️ Technical Architecture

#### **Backend Services**

- **Main Application**: Flask-based web server with user management
- **STT Service** (Port 3010): AWS Transcribe streaming API
- **Pronunciation Service** (Port 3001): Microsoft Speech SDK assessment
- **TTS Service** (Port 3011): AWS Polly neural voice synthesis

#### **Database & Storage**

- **DynamoDB Tables**: Users, preferences, chat logs, and learning analytics
- **S3 Integration**: Audio file storage with CDN delivery
- **Session Management**: Secure user authentication and state persistence

#### **Computer Vision Pipeline**

- **AWS Rekognition**: Object detection with confidence scoring
- **OpenCV**: Image preprocessing and overlay rendering
- **Multi-Source Input**: Camera switching and photo upload capabilities

## 🛠️ Technology Stack

### **AI & Machine Learning**

- AWS Rekognition (Computer Vision)
- AWS Transcribe (Speech-to-Text)
- AWS Polly (Text-to-Speech)
- Microsoft Cognitive Services (Pronunciation Assessment)

### **Backend Technologies**

- **Python**: Flask web framework, OpenCV, Boto3
- **Node.js**: Express.js microservices, Multer file handling
- **AWS SDK**: Complete cloud integration

### **Frontend & UI**

- **HTML5/CSS3**: Responsive web interface
- **JavaScript**: Real-time webcam streaming, AJAX communications
- **Bootstrap**: Modern UI components and responsive design

### **Cloud Infrastructure**

- **AWS Services**: DynamoDB, S3, Rekognition, Transcribe, Polly
- **Authentication**: AWS IAM and credential management
- **Storage**: Multi-region S3 buckets with CDN

## 📋 API Endpoints

### **Main Flask Application**

GET / # Home page
POST /login # User authentication
POST /register # User registration
GET /dashboard # User dashboard
GET /webcam # Main learning interface
POST /log-selection # Log selected objects for learning
GET /get-detections # Get current object detections
POST /api/checkin # Daily learning check-in
GET /api/checkin-stats # Learning analytics

### **STT Service (Port 3010)**

POST /speech-to-text # Single audio transcription
POST /batch-speech-to-text # Batch audio processing
GET /health # Service health check

### **Pronunciation Service (Port 3001)**

POST /pronunciation-assessment # Audio pronunciation scoring
GET /languages # Supported languages
GET /docs # API documentation

### **TTS Service (Port 3011)**

POST /tts # Text-to-speech conversion
GET /health # Service health check

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Node.js 14+
- AWS Account with configured credentials

### Installation

1. **Clone the repository**
   git clone https://github.com/gohyumin/amadues.git
   cd amadues

2. **Create virtual environment**
   python -m venv venv
   source venv/bin/activate # On Windows: venv\Scripts\activate

3. **Install dependencies**
   pip install -r requirements.txt

4. **Configure environment variables**
   AWS Configuration
   export AWS_ACCESS_KEY_ID="your_access_key"
   export AWS_SECRET_ACCESS_KEY="your_secret_key"
   export AWS_REGION="ap-southeast-1"

Microsoft Speech Service
export SPEECH_KEY="your_speech_service_key"
export REGION="southeastasia"

API Security
export API_KEY="your_secure_api_key"

5. **Start the services**
   Main Flask application
   python app.py

STT Service
node server.js # (Port 3010)

Pronunciation Service
node server.js # (Port 3001)

TTS Service
node index.js # (Port 3011)

## 📊 Learning Features

### **Progress Tracking**

- Daily learning streaks and check-ins
- Pronunciation improvement metrics
- Vocabulary acquisition tracking
- Personalized learning recommendations

### **Interactive Learning**

- Point-and-learn object recognition
- Voice practice with real-time feedback
- Contextual vocabulary building
- Cultural content integration

### **Gamification Elements**

- Achievement badges and milestones
- Competitive learning streaks
- Progress visualization and analytics
- Social learning features

## 🔧 Configuration

### **Camera Setup**

- **Laptop Camera**: Automatic detection (ports 0-2)
- **Phone Camera**: IP webcam at `http://10.193.110.135:8080/video`
- **Photo Upload**: JPEG/PNG support with automatic resizing

### **Language Configuration**

- **Default STT Language**: `zh-CN` (Chinese Simplified)
- **Default TTS Voice**: `Ruth` (Neural voice)
- **Translation Fallback**: Hardcoded dictionary with 50+ common objects

## 🤝 Contributing

We welcome contributions! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- AWS for comprehensive cloud services
- Microsoft Cognitive Services for speech technologies
- OpenCV community for computer vision tools
- Flask and Node.js communities for web frameworks

## 📞 Support

For support and questions:

- Create an issue in this repository
- Contact the development team
- Check the documentation in `/docs`

---

**Built with ❤️ for language learners worldwide**
