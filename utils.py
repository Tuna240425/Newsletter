import random
import re
import base64
import requests
from datetime import datetime
from config import MESSAGE_BANK, COMPANY_CONFIG
import streamlit as st

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    from zoneinfo import ZoneInfo  # Py>=3.9
except ImportError:
    ZoneInfo = None

def _get_kst_now():
    """한국 표준시 현재 시간 반환"""
    if ZoneInfo:
        return datetime.now(ZoneInfo("Asia/Seoul"))
    return datetime.now()

def _season_by_month(m: int) -> str:
    """월에 따른 계절 반환"""
    if 3 <= m <= 5: return "spring"
    if 6 <= m <= 8: return "summer"
    if 9 <= m <= 11: return "autumn"
    return "winter"

def pick_contextual_message(custom_bank: dict = None) -> str:
    """시즌, 요일, 특별일에 맞는 상황별 메시지 선택"""
    bank = custom_bank or MESSAGE_BANK
    now = _get_kst_now()
    mmdd = now.strftime("%m-%d")
    weekday = now.weekday()
    season_key = _season_by_month(now.month)

    candidates = []

    # 1) 특별일
    if mmdd in bank.get("special_dates", {}):
        candidates.extend(bank["special_dates"][mmdd])

    # 2) 시즌
    candidates.extend(bank.get("seasons", {}).get(season_key, []))

    # 3) 요일
    candidates.extend(bank.get("weekdays", {}).get(weekday, []))

    if not candidates:
        candidates = ["늘 믿고 함께해주셔서 감사합니다. 좋은 하루 보내세요."]

    return random.choice(candidates)

def generate_ai_message(topic="법률", tone="친근한"):
    """OpenAI API를 사용해서 맞춤형 메시지 생성 (자연스러운 인사말 형태)"""
    if not COMPANY_CONFIG.get('use_openai') or not COMPANY_CONFIG.get('openai_api_key'):
        return pick_contextual_message()
    
    try:
        client = OpenAI(api_key=COMPANY_CONFIG['openai_api_key'])
        
        prompt = f"""
        {COMPANY_CONFIG['company_name']}의 뉴스레터용 자연스러운 인사말을 작성해주세요.
        
        조건:
        - 주제: {topic}
        - 톤: {tone}
        - 길이: 1-2문장
        - 한국어로 작성
        - 법률사무소 특성에 맞게
        - 오늘 날짜: {datetime.now().strftime('%Y년 %m월 %d일 %A')}
        - 별도의 인용구나 박스 형태가 아닌, 인사말에 자연스럽게 녹아드는 문체
        
        예시 스타일: "새로운 한 주가 시작되었습니다. 언제나 여러분의 든든한 법률 파트너가 되겠습니다."
        """
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=150,
            temperature=0.7
        )
        
        return response.choices[0].message.content.strip()
        
    except ImportError:
        st.warning("OpenAI 라이브러리가 최신 버전이 아닙니다. 'pip install openai>=1.0.0' 으로 업데이트하세요")
        return pick_contextual_message()
    except Exception as e:
        st.warning(f"AI 메시지 생성 실패: {e}")
        return pick_contextual_message()

def create_svg_gradient_image(width=600, height=200, text="법률 뉴스레터"):
    """SVG 그라디언트 이미지 생성"""
    svg_content = f'''<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">
        <defs>
            <linearGradient id="grad1" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" style="stop-color:#667eea;stop-opacity:1" />
                <stop offset="100%" style="stop-color:#764ba2;stop-opacity:1" />
            </linearGradient>
        </defs>
        <rect width="100%" height="100%" fill="url(#grad1)" />
        <text x="50%" y="50%" font-family="Arial, sans-serif" font-size="24" font-weight="bold" 
              fill="white" text-anchor="middle" dominant-baseline="middle">{text}</text>
    </svg>'''
    return f"data:image/svg+xml;base64,{base64.b64encode(svg_content.encode()).decode()}"

def create_svg_gradient_image2(width=600, height=200, text="신뢰할 수 있는 법률 정보"):
    """두 번째 SVG 그라디언트 이미지 생성"""
    svg_content = f'''<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">
        <defs>
            <linearGradient id="grad2" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" style="stop-color:#4facfe;stop-opacity:1" />
                <stop offset="100%" style="stop-color:#00f2fe;stop-opacity:1" />
            </linearGradient>
        </defs>
        <rect width="100%" height="100%" fill="url(#grad2)" />
        <text x="50%" y="50%" font-family="Arial, sans-serif" font-size="20" font-weight="600" 
              fill="white" text-anchor="middle" dominant-baseline="middle">{text}</text>
    </svg>'''
    return f"data:image/svg+xml;base64,{base64.b64encode(svg_content.encode()).decode()}"

def get_reliable_image(width=600, height=200):
    """매우 안정적인 이미지 URL 반환"""
    
    # 옵션 1: 검증된 고정 이미지 URLs (가장 안정적)
    reliable_images = [
        "https://images.unsplash.com/photo-1589829545856-d10d557cf95f?w=600&h=200&fit=crop&auto=format",  # 법정
        "https://images.unsplash.com/photo-1521791136064-7986c2920216?w=600&h=200&fit=crop&auto=format",  # 책들
        "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=600&h=200&fit=crop&auto=format",  # 오피스
        "https://images.unsplash.com/photo-1516442719524-a603408c90cb?w=600&h=200&fit=crop&auto=format",  # 비즈니스
        "https://images.unsplash.com/photo-1560472354-b33ff0c44a43?w=600&h=200&fit=crop&auto=format",  # 서류
        "https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=600&h=200&fit=crop&auto=format",  # 저울(정의)
        "https://images.unsplash.com/photo-1589578228447-e1a4e481c6c8?w=600&h=200&fit=crop&auto=format",  # 법률서적
    ]
    
    # 옵션 2: SVG 이미지들 (항상 작동)
    gradient_images = [
        create_svg_gradient_image(width, height, "법률 뉴스레터"),
        create_svg_gradient_image2(width, height, "신뢰할 수 있는 법률 정보"),
    ]
    
    try:
        # 1단계: Unsplash 이미지 시도
        selected_image = random.choice(reliable_images)
        response = requests.head(selected_image, timeout=2)
        if response.status_code == 200:
            return selected_image
    except:
        pass
    
    try:
        # 2단계: Picsum 대체 이미지 시도
        picsum_id = random.randint(1, 100)  # 더 안정적인 범위
        picsum_url = f"https://picsum.photos/{width}/{height}?random={picsum_id}"
        response = requests.head(picsum_url, timeout=2)
        if response.status_code == 200:
            return picsum_url
    except:
        pass
    
    # 3단계: SVG 이미지 반환 (항상 작동)
    return random.choice(gradient_images)

def get_font_css(font_style='pretendard'):
    """선택된 폰트 스타일에 따른 CSS 반환"""
    
    if font_style == 'pretendard':
        return """
            /* Pretendard 웹폰트 */
            @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.8/dist/web/static/pretendard.css');
            
            body {
                font-family: "Pretendard Variable", Pretendard, -apple-system, BlinkMacSystemFont, system-ui, Roboto, "Helvetica Neue", "Segoe UI", "Apple SD Gothic Neo", "Noto Sans KR", "Malgun Gothic", sans-serif;
                font-weight: 400;
                -webkit-font-smoothing: antialiased;
                -moz-osx-font-smoothing: grayscale;
            }
        """
    elif font_style == 'system_sans':
        return """
            body {
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, "Noto Sans", sans-serif;
                font-weight: 400;
                -webkit-font-smoothing: antialiased;
                -moz-osx-font-smoothing: grayscale;
            }
        """
    else:
        return get_font_css('pretendard')

def validate_email(email):
    """이메일 주소 유효성 검사"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def simple_clean(text):
    """텍스트 정리 함수"""
    if not text:
        return ""
    text = text.replace('\u00a0', ' ')
    text = text.replace('\u2000', ' ')
    text = text.replace('\u2001', ' ')
    text = text.replace('\u2002', ' ')
    text = text.replace('\u2003', ' ')
    text = text.replace('\u2004', ' ')
    text = text.replace('\u2005', ' ')
    text = text.replace('\u2006', ' ')
    text = text.replace('\u2007', ' ')
    text = text.replace('\u2008', ' ')
    text = text.replace('\u2009', ' ')
    text = text.replace('\u200a', ' ')
    text = text.replace('\u200b', '')
    text = text.replace('\u3000', ' ')
    text = text.replace('\ufeff', '')
    text = re.sub(r'\s+', ' ', text)
    return text.strip()