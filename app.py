import streamlit as st
import os
from dotenv import load_dotenv
import openai
from PIL import Image
import requests
import io
import base64
import time
from datetime import datetime
import json
from pathlib import Path

# 환경 변수 로드
load_dotenv()

# API 키 설정
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MAX_REQUESTS_PER_HOUR = 10  # 시간당 최대 요청 수 제한

# DALL-E 3 가격 설정 (USD)
DALLE_PRICE_PER_IMAGE = 0.080  # 1792x1024 크기 기준

# 스타일별 최적화된 프롬프트 설정
STYLE_PROMPTS = {
    "기본": {
        "style": "기본",
        "color": "밝고 선명한",
        "lighting": "자연스러운",
        "composition": "균형잡힌",
        "mood": "전문적인"
    },
    "사진": {
        "style": "사진",
        "color": "자연스러운",
        "lighting": "사진같은",
        "composition": "사진적",
        "mood": "현실적인"
    },
    "일러스트레이션": {
        "style": "일러스트레이션",
        "color": "선명하고 밝은",
        "lighting": "부드러운",
        "composition": "창의적인",
        "mood": "친근한"
    },
    "디지털 아트": {
        "style": "디지털 아트",
        "color": "강렬하고 현대적인",
        "lighting": "극적인",
        "composition": "동적인",
        "mood": "미래지향적인"
    },
    "수채화": {
        "style": "수채화",
        "color": "부드럽고 투명한",
        "lighting": "자연스러운",
        "composition": "유동적인",
        "mood": "시원한"
    },
    "유화": {
        "style": "유화",
        "color": "풍부하고 따뜻한",
        "lighting": "극적인",
        "composition": "고전적인",
        "mood": "우아한"
    }
}

# 기본 시스템 프롬프트
DEFAULT_SYSTEM_PROMPT = """당신은 일러스트레이트 전문가입니다.
AI 학습 데이터셋을 판매하는 웹 사이트에 게시할 일러스트 이미지를 생성해야합니다. 주어질 주제와 키워드의 정보를 이해하고 주제에 어울리는 이미지를 [디자인 기준]에 맞춰 생성합니다.

[디자인 기준]
현대 벡터 아트 스타일의 디지털 일러스트레이션입니다. 
푸른 계열, 노란 계열, 보라 계열, 붉은 계열의 색감이 주가 되어 조화를 이룹니다. 휘도를 적당히 하여 그림자와 하이라이트가 빛나게 보이게 해주세요. 채도를 밝게 해주세요. 
전체적인 미학은 미래지향적이면서도 메탈릭합니다. 초현실적인 마무리가 특징입니다. 
기술적인 그래픽의 요소를 사용하고 최소한으로 사용하여 직관적으로 보이게 합니다. 또한 이미지 내 언어(글자, 단어, 문장)은 최대한 사용하지 않습니다.
웹사이트에 게시할 때 이미지가 잘릴수 있으니, 태두리에 여백을 많이 넣어주세요.
이미지 크기는 1536X1024입니다.
흰색을 포인트로 사용합니다. 전체 그림에서 최대 2%정도만 사용합니다. 

-------------------
- 다음 내용을 참고해서 관련된 썸네일을 생성하세요:"""

# OpenAI 클라이언트 설정
openai_client = openai.OpenAI(api_key=OPENAI_API_KEY)

# 캐시 디렉토리 설정
CACHE_DIR = Path("image_cache")
CACHE_DIR.mkdir(exist_ok=True)

def check_api_key():
    if not OPENAI_API_KEY:
        st.error("OpenAI API 키가 설정되지 않았습니다. .env 파일에 OPENAI_API_KEY를 설정해주세요.")
        return False
    return True

def check_rate_limit():
    """요청 제한 확인"""
    cache_file = CACHE_DIR / "rate_limit.json"
    if cache_file.exists():
        with open(cache_file, 'r') as f:
            data = json.load(f)
            if time.time() - data['timestamp'] < 3600:  # 1시간
                if data['count'] >= MAX_REQUESTS_PER_HOUR:
                    st.error("시간당 최대 요청 수를 초과했습니다. 잠시 후 다시 시도해주세요.")
                    return False
    return True

def update_rate_limit():
    """요청 제한 업데이트"""
    cache_file = CACHE_DIR / "rate_limit.json"
    current_time = time.time()
    
    if cache_file.exists():
        with open(cache_file, 'r') as f:
            data = json.load(f)
            if current_time - data['timestamp'] < 3600:
                data['count'] += 1
            else:
                data = {'timestamp': current_time, 'count': 1}
    else:
        data = {'timestamp': current_time, 'count': 1}
    
    with open(cache_file, 'w') as f:
        json.dump(data, f)

def get_style_prompt(style):
    """선택된 스타일에 따른 최적화된 프롬프트 생성"""
    style_config = STYLE_PROMPTS.get(style, STYLE_PROMPTS["기본"])
    return DEFAULT_SYSTEM_PROMPT.format(**style_config)

def generate_image(prompt, system_prompt):
    try:
        # 시스템 프롬프트와 사용자 프롬프트 결합
        full_prompt = f"{system_prompt}\n\n[내용]: {prompt}"
        
        response = openai_client.images.generate(
            model="dall-e-3",
            prompt=full_prompt,
            size="1792x1024",
            quality="standard",
            n=1,
        )
        return response.data[0].url, DALLE_PRICE_PER_IMAGE
    except Exception as e:
        st.error(f"이미지 생성 중 오류 발생: {str(e)}")
        return None, None

def download_image_from_url(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.content
        else:
            st.error(f"이미지 다운로드 실패: HTTP {response.status_code}")
            return None
    except Exception as e:
        st.error(f"이미지 다운로드 중 오류 발생: {str(e)}")
        return None

def save_to_cache(image_data, prompt):
    """이미지를 캐시에 저장"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"image_{timestamp}.jpg"
    filepath = CACHE_DIR / filename
    
    with open(filepath, 'wb') as f:
        f.write(image_data)
    
    # 메타데이터 저장
    metadata = {
        'filename': filename,
        'prompt': prompt,
        'timestamp': timestamp
    }
    
    metadata_file = CACHE_DIR / "metadata.json"
    if metadata_file.exists():
        with open(metadata_file, 'r') as f:
            data = json.load(f)
    else:
        data = []
    
    data.append(metadata)
    
    with open(metadata_file, 'w') as f:
        json.dump(data, f)

def main():
    st.set_page_config(
        page_title="AI 이미지 생성기",
        page_icon="🎨",
        layout="wide"
    )
    
    st.title("🎨 AI 이미지 생성기")
    st.write("OpenAI DALL-E 3를 사용하여 이미지를 생성합니다.")

    # API 키 확인
    if not check_api_key():
        return

    # 사이드바 설정
    with st.sidebar:
        st.header("설정")
        
        # 시스템 프롬프트 설정
        st.subheader("시스템 프롬프트")
        system_prompt = st.text_area(
            "시스템 프롬프트를 입력하세요",
            value=DEFAULT_SYSTEM_PROMPT,
            height=400
        )
        
        st.header("이전 생성 이미지")
        if (CACHE_DIR / "metadata.json").exists():
            with open(CACHE_DIR / "metadata.json", 'r') as f:
                metadata = json.load(f)
                for item in reversed(metadata[-5:]):  # 최근 5개만 표시
                    if st.button(f"{item['timestamp']} - {item['prompt'][:30]}..."):
                        image_path = CACHE_DIR / item['filename']
                        if image_path.exists():
                            st.image(str(image_path), use_column_width=True)

    # 메인 컨텐츠
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # 프롬프트 입력
        prompt = st.text_area("이미지 생성을 위한 내용을 입력하세요:", height=100)
        
        if st.button("이미지 생성"):
            if not prompt:
                st.warning("프롬프트를 입력해주세요.")
            else:
                if not check_rate_limit():
                    return
                    
                with st.spinner("이미지 생성 중..."):
                    image_url, cost = generate_image(prompt, system_prompt)
                    
                    if image_url:
                        # 이미지 표시
                        st.image(image_url, caption="생성된 이미지", use_column_width=True)
                        
                        # 비용 정보 표시
                        st.info(f"이미지 생성 비용: ${cost:.3f} USD")
                        
                        # 이미지 다운로드 및 캐시 저장
                        image_data = download_image_from_url(image_url)
                        if image_data:
                            save_to_cache(image_data, prompt)
                            update_rate_limit()
                            
                            st.download_button(
                                label="JPG로 다운로드",
                                data=image_data,
                                file_name=f"generated_image_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg",
                                mime="image/jpeg"
                            )

    with col2:
        st.info("""
        ### 💡 프롬프트 작성 팁
        chatgpt에서 테스트하다가 느려지면 쓰세여...
        """)
        
        st.info("""
        ### 💰 비용 정보
        - 이미지 크기: 1792x1024
        - 이미지당 비용: $0.080 USD
        - 많이 안비쌉니다
        - 김신우 연구용 api를 씁니다.
        """)

if __name__ == "__main__":
    main() 