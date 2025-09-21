import boto3
import cv2
import numpy as np
from typing import List, Dict
import os
import time
from botocore.exceptions import ClientError, TokenRetrievalError, NoCredentialsError

class AWSRekognitionDetector:
    def __init__(self, region_name='us-east-1', confidence_threshold=0.5, max_retries=3):
        """
        Initialize AWS Rekognition detector with better error handling
        """
        self.region_name = region_name
        self.confidence_threshold = confidence_threshold * 100  # AWS uses percentage
        self.max_retries = max_retries
        self.rekognition_client = None
        
        # Initialize with retry logic
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize AWS client with comprehensive error handling"""
        for attempt in range(self.max_retries):
            try:
                print(f"🔗 Attempting to connect to AWS Rekognition (attempt {attempt + 1}/{self.max_retries})")
                
                # Clear any cached credentials that might be expired
                self._clear_cached_credentials()
                
                # Create new client
                self.rekognition_client = boto3.client(
                    'rekognition', 
                    region_name=self.region_name
                )
                
                # Test connection with a lightweight call
                self._test_connection()
                print(f"✅ AWS Rekognition connected successfully!")
                return
                
            except ClientError as e:
                error_code = e.response['Error']['Code']
                error_message = e.response['Error']['Message']
                
                if error_code == 'ExpiredTokenException':
                    print(f"⏰ Token expired (attempt {attempt + 1}). Getting fresh credentials...")
                    if attempt < self.max_retries - 1:
                        self._handle_expired_token()
                        time.sleep(2)  # Wait before retry
                        continue
                    else:
                        raise Exception("❌ Token expired. Please generate new AWS credentials!")
                        
                elif error_code == 'UnauthorizedOperation':
                    raise Exception("❌ Access denied. Please check your AWS permissions for Rekognition.")
                    
                elif error_code == 'InvalidUserID.NotFound':
                    raise Exception("❌ Invalid AWS credentials. Please check your Access Key and Secret Key.")
                    
                else:
                    print(f"⚠️ AWS error: {error_code} - {error_message}")
                    if attempt < self.max_retries - 1:
                        time.sleep(2)
                        continue
                    else:
                        raise
                        
            except NoCredentialsError:
                raise Exception("❌ No AWS credentials found. Please run 'aws configure' or set environment variables.")
                
            except TokenRetrievalError as e:
                print(f"⚠️ Token retrieval error: {e}")
                if attempt < self.max_retries - 1:
                    self._handle_expired_token()
                    continue
                else:
                    raise Exception("❌ Unable to retrieve valid AWS token. Please refresh your credentials.")
                    
            except Exception as e:
                print(f"⚠️ Connection error: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(2)
                    continue
                else:
                    raise
    
    def _clear_cached_credentials(self):
        """Clear cached AWS credentials that might be expired"""
        try:
            # Clear boto3 session cache
            if hasattr(boto3.DEFAULT_SESSION, '_session'):
                boto3.DEFAULT_SESSION = None
            
            # Force new session
            boto3.setup_default_session()
            
        except Exception:
            pass  # Ignore errors in cache clearing
    
    def _handle_expired_token(self):
        """Handle expired token by providing user guidance"""
        print("\n" + "="*60)
        print("🔑 AWS TOKEN EXPIRED - ACTION REQUIRED!")
        print("="*60)
        print("Please choose one of these options:")
        print("\n1️⃣  Generate NEW AWS credentials:")
        print("   • Go to AWS Console → Security credentials")
        print("   • Deactivate old Access Key")
        print("   • Create new Access Key")
        print("   • Update ~/.aws/credentials file")
        
        print("\n2️⃣  Use environment variables:")
        print("   $env:AWS_ACCESS_KEY_ID = \"YOUR_NEW_KEY\"")
        print("   $env:AWS_SECRET_ACCESS_KEY = \"YOUR_NEW_SECRET\"")
        
        print("\n3️⃣  Clear cached credentials:")
        print("   Remove-Item -Recurse $env:USERPROFILE\\.aws\\sso")
        print("="*60)
        
        # Wait for user action
        input("Press Enter after updating your credentials...")
    
    def _test_connection(self):
        """Test AWS connection with minimal API call"""
        try:
            # Use get-caller-identity which is free and lightweight
            sts_client = boto3.client('sts', region_name=self.region_name)
            identity = sts_client.get_caller_identity()
            print(f"📋 Connected as: {identity.get('Arn', 'Unknown')}")
            
        except Exception as e:
            # If STS fails, try a minimal Rekognition call
            test_image = np.zeros((50, 50, 3), dtype=np.uint8)
            _, buffer = cv2.imencode('.jpg', test_image)
            
            self.rekognition_client.detect_labels(
                Image={'Bytes': buffer.tobytes()},
                MaxLabels=1,
                MinConfidence=95  # Very high threshold to minimize results
            )
    
    def infer(self, frame_bgr: np.ndarray) -> List[Dict]:
        """Detect objects with automatic retry on token expiration"""
        for attempt in range(self.max_retries):
            try:
                return self._perform_detection(frame_bgr)
                
            except ClientError as e:
                if e.response['Error']['Code'] == 'ExpiredTokenException':
                    print(f"⏰ Token expired during detection. Refreshing... (attempt {attempt + 1})")
                    self._initialize_client()
                    continue
                else:
                    print(f"⚠️ Detection error: {e}")
                    return []
                    
            except Exception as e:
                print(f"⚠️ Unexpected detection error: {e}")
                return []
        
        print("❌ Failed to detect objects after multiple attempts")
        return []
    
    def _perform_detection(self, frame_bgr: np.ndarray) -> List[Dict]:
        """Perform the actual object detection"""
        # Convert to JPEG
        _, buffer = cv2.imencode('.jpg', frame_bgr, [cv2.IMWRITE_JPEG_QUALITY, 85])
        
        # Call AWS Rekognition
        response = self.rekognition_client.detect_labels(
            Image={'Bytes': buffer.tobytes()},
            MaxLabels=25,
            MinConfidence=self.confidence_threshold
        )
        
        # Process results
        detections = []
        height, width = frame_bgr.shape[:2]
        
        for i, label in enumerate(response.get('Labels', [])):
            label_name = label['Name'].lower()
            confidence = label['Confidence'] / 100.0
            
            # Handle instances with bounding boxes
            if label.get('Instances'):
                for instance in label['Instances']:
                    if 'BoundingBox' in instance:
                        bbox = instance['BoundingBox']
                        x1 = max(0, int(bbox['Left'] * width))
                        y1 = max(0, int(bbox['Top'] * height))
                        x2 = min(width, int(x1 + bbox['Width'] * width))
                        y2 = min(height, int(y1 + bbox['Height'] * height))
                    else:
                        # Fallback bounding box
                        x1, y1 = width//3, height//3
                        x2, y2 = 2*width//3, 2*height//3
                    
                    detections.append({
                        "bbox": (x1, y1, x2, y2),
                        "center": ((x1+x2)//2, (y1+y2)//2),
                        "conf": confidence,
                        "cls_id": i,
                        "label": label_name
                    })
            else:
                # General scene detection
                cx, cy = width//2, height//2
                size = min(width, height) // 8
                
                detections.append({
                    "bbox": (max(0, cx-size), max(0, cy-size), min(width, cx+size), min(height, cy+size)),
                    "center": (cx, cy),
                    "conf": confidence,
                    "cls_id": i,
                    "label": label_name
                })
        
        return detections[:10]  # Limit to top 10 detections

# Compatibility wrapper
YoloDetector = AWSRekognitionDetector