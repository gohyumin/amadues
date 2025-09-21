# -*- coding: utf-8 -*-


import requests
import json
from typing import Dict
from urllib.parse import quote
import time

# Cache for translations
_translation_cache: Dict[tuple, str] = {}

# Fallback translations for offline/error cases
ZH_CN_MAP = {
    "person": "人", "bicycle": "自行车", "car": "汽车", "motorcycle": "摩托车",
    "bus": "公共汽车", "train": "火车", "truck": "卡车", "boat": "船",
    "traffic light": "红绿灯", "fire hydrant": "消防栓", "stop sign": "停止标志",
    "parking meter": "停车计时器", "bench": "长凳", "bird": "鸟", "cat": "猫", "dog": "狗",
    "horse": "马", "sheep": "羊", "cow": "牛", "elephant": "大象", "bear": "熊",
    "zebra": "斑马", "giraffe": "长颈鹿", "backpack": "背包", "umbrella": "雨伞",
    "handbag": "手提包", "tie": "领带", "suitcase": "手提箱", "frisbee": "飞盘",
    "skis": "滑雪板", "snowboard": "滑雪板", "sports ball": "运动球", "kite": "风筝",
    "baseball bat": "棒球棒", "baseball glove": "棒球手套", "skateboard": "滑板",
    "surfboard": "冲浪板", "tennis racket": "网球拍", "bottle": "瓶子", "wine glass": "酒杯",
    "cup": "杯子", "fork": "叉子", "knife": "刀", "spoon": "勺子", "bowl": "碗",
    "banana": "香蕉", "apple": "苹果", "sandwich": "三明治", "orange": "橙子",
    "broccoli": "西兰花", "carrot": "胡萝卜", "hot dog": "热狗", "pizza": "披萨",
    "donut": "甜甜圈", "cake": "蛋糕", "chair": "椅子", "couch": "沙发",
    "potted plant": "盆栽", "bed": "床", "dining table": "餐桌", "toilet": "马桶",
    "tv": "电视", "laptop": "笔记本电脑", "mouse": "鼠标", "remote": "遥控器",
    "keyboard": "键盘", "cell phone": "手机", "microwave": "微波炉", "oven": "烤箱",
    "toaster": "烤面包机", "sink": "水槽", "refrigerator": "冰箱", "book": "书",
    "clock": "钟", "vase": "花瓶", "scissors": "剪刀", "teddy bear": "玩具熊",
    "hair drier": "吹风机", "toothbrush": "牙刷", "face": "脸", "teeth": "牙齿", 
    "wallet": "钱包", "bottle": "水瓶", "female": "女人", "smile": "微笑", 
    "head": "头", "chair": "椅子", "table": "桌子"
}

def translate_with_mymemory(text: str, target_lang: str) -> str:
    """Free MyMemory API translation - no API key required"""
    try:
        # Convert language codes
        lang_map = {
            "zh-CN": "zh-CN", "zh": "zh-CN", "chinese": "zh-CN",
            "en": "en", "english": "en",
            "es": "es", "spanish": "es",
            "fr": "fr", "french": "fr",
            "de": "de", "german": "de",
            "ja": "ja", "japanese": "ja",
            "ko": "ko", "korean": "ko"
        }
        
        target = lang_map.get(target_lang.lower(), target_lang)
        
        url = f"https://api.mymemory.translated.net/get"
        params = {
            'q': text,
            'langpair': f'en|{target}'
        }
        
        response = requests.get(url, params=params, timeout=3)
        if response.status_code == 200:
            data = response.json()
            if data.get('responseStatus') == 200:
                return data['responseData']['translatedText']
    except Exception as e:
        print(f"MyMemory API error: {e}")
    return None

def translate_with_libretranslate(text: str, target_lang: str) -> str:
    """LibreTranslate public instance - free with limits"""
    try:
        lang_map = {
            "zh-CN": "zh", "zh": "zh", "chinese": "zh",
            "en": "en", "english": "en",
            "es": "es", "fr": "fr", "de": "de", "ja": "ja"
        }
        
        target = lang_map.get(target_lang.lower(), "zh")
        
        url = "https://libretranslate.de/translate"
        data = {
            'q': text,
            'source': 'en',
            'target': target,
            'format': 'text'
        }
        
        response = requests.post(url, data=data, timeout=5)
        if response.status_code == 200:
            result = response.json()
            return result.get('translatedText', '')
    except Exception as e:
        print(f"LibreTranslate API error: {e}")
    return None

def translate_with_googletrans(text: str, target_lang: str) -> str:
    """Unofficial Google Translate - install with: pip install googletrans==4.0.0rc1"""
    try:
        from googletrans import Translator
        translator = Translator()
        
        lang_map = {
            "zh-CN": "zh-cn", "zh": "zh-cn", "chinese": "zh-cn",
            "en": "en", "spanish": "es", "french": "fr"
        }
        
        target = lang_map.get(target_lang.lower(), "zh-cn")
        result = translator.translate(text, src='en', dest=target)
        return result.text
    except ImportError:
        print("googletrans not installed. Run: pip install googletrans==4.0.0rc1")
        return None
    except Exception as e:
        print(f"GoogleTrans error: {e}")
        return None

def translate_text(text_en: str, target_lang: str) -> str:
    """Main translation function with multiple free API fallbacks"""
    # Check cache first
    cache_key = (text_en.lower(), target_lang.lower())
    if cache_key in _translation_cache:
        return _translation_cache[cache_key]
    
    # Don't translate if target is English
    if target_lang.lower() in ['en', 'english']:
        _translation_cache[cache_key] = text_en
        return text_en
    
    # Try free APIs in order of preference
    translation_methods = [
        translate_with_mymemory,      # Most reliable, no setup
        translate_with_libretranslate, # Good quality, public instance
        translate_with_googletrans     # Requires pip install googletrans
    ]
    
    for method in translation_methods:
        try:
            result = method(text_en, target_lang)
            if result and result != text_en:
                _translation_cache[cache_key] = result
                return result
        except Exception as e:
            print(f"Translation method failed: {e}")
            continue
    
    # Fallback to local dictionary for Chinese
    if target_lang.lower().startswith("zh"):
        result = ZH_CN_MAP.get(text_en, text_en)
        _translation_cache[cache_key] = result
        return result
    
    # Final fallback
    return text_en

# Optional: Install googletrans for better quality
def install_googletrans():
    """Helper to install googletrans if needed"""
    try:
        import subprocess
        subprocess.check_call(['pip', 'install', 'googletrans==4.0.0rc1'])
        print("googletrans installed successfully!")
    except Exception as e:
        print(f"Failed to install googletrans: {e}")
