import streamlit as st
import pandas as pd
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os
from datetime import datetime, timedelta
import json
import requests
from urllib.parse import urlparse, quote
import xml.etree.ElementTree as ET
import random
import re
import unicodedata
import hashlib
import base64
from dotenv import load_dotenv
load_dotenv()


try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    from zoneinfo import ZoneInfo  # Py>=3.9
except ImportError:
    ZoneInfo = None

# ==============================================
# 회사별 기본 설정 - 여기서 한 번만 수정하세요
# ==============================================

COMPANY_CONFIG = {
    # 회사 정보
    'company_name': '임앤리 법률사무소',
    'company_email': 'official.haedeun@gmail.com',
    'company_password': 'wsbn vanl ywza ochf',
    
    # 사무실 정보 (뉴스레터 하단에 표시)
    'office_info': {
        'address': '서울시 송파구 법원로92, 806호(문정동, 파트너스1)',
        'phone': '02-3477-9650',
        'website': 'https://www.limleelawfirm.com/',
        'business_hours': '평일 09:00-18:00'
    },
    
    # SMTP 설정
    'smtp_server': 'smtp.gmail.com',
    'smtp_port': 587,
    
    # 뉴스 수집 설정 (포괄적인 시사/사회/경제/법률 뉴스)
    'auto_collect_news': True,
    'default_news_sources': [
        # 네이버 뉴스 RSS (전 섹션)
        'https://news.naver.com/rss/section/100.xml',  # 정치
        'https://news.naver.com/rss/section/101.xml',  # 경제
        'https://news.naver.com/rss/section/102.xml',  # 사회
        'https://news.naver.com/rss/section/103.xml',  # 생활/문화
        
        # 다음 뉴스 RSS
        'https://news.daum.net/rss/politics',    # 정치
        'https://news.daum.net/rss/economic',    # 경제
        'https://news.daum.net/rss/society',     # 사회
        
        # Google News에서 한국 시사 뉴스 검색 (법률뿐만 아니라 전반적)
        'https://news.google.com/rss/search?q=한국+정책&hl=ko&gl=KR&ceid=KR:ko',
        'https://news.google.com/rss/search?q=경제+정책&hl=ko&gl=KR&ceid=KR:ko',
        'https://news.google.com/rss/search?q=사회+정책&hl=ko&gl=KR&ceid=KR:ko',
        'https://news.google.com/rss/search?q=법률+개정&hl=ko&gl=KR&ceid=KR:ko',
        'https://news.google.com/rss/search?q=규제+정책&hl=ko&gl=KR&ceid=KR:ko',
        'https://news.google.com/rss/search?q=부동산+시장&hl=ko&gl=KR&ceid=KR:ko',
        'https://news.google.com/rss/search?q=금융+정책&hl=ko&gl=KR&ceid=KR:ko',
        'https://news.google.com/rss/search?q=조세+세법&hl=ko&gl=KR&ceid=KR:ko',
    ],

    # 기본 메시지
    'default_subject_template': '[{company_name}] 법률 뉴스레터 - {date}',
    'default_greeting': '안녕하세요, 임앤리 법률사무소입니다. 최신 소식을 전해 드립니다.',
    'footer_message': '더 자세한 상담이 필요하시면 언제든 연락주세요.',

    # 자동화 설정
    'skip_email_setup': True,
    'skip_smtp_test': True,

    # OpenAI API 설정 (자동 설정으로 사용자가 신경쓸 필요 없음)
    'use_openai': True,
    'openai_api_key': os.getenv('OPENAI_API_KEY', ''),

    # 디자인 설정
    'newsletter_template': 'simple',
    'use_newsletter_images': True,
    'image_timeout': 3,
    'fallback_to_gradient': True,
}

# 기본 주소록 데이터 (샘플)
DEFAULT_ADDRESS_BOOK = [
    {'이름': '김철수', '이메일': 'test1@example.com'},
    {'이름': '이영희', '이메일': 'test2@example.com'},
    {'이름': '박민수', '이메일': 'test3@example.com'},
]

MESSAGE_BANK = {
    "seasons": {
        "spring": [
            "새봄의 기운처럼 좋은 소식이 가득하시길 바랍니다.",
            "따뜻한 봄바람과 함께 활력을 전합니다.",
        ],
        "summer": [
            "무더위에도 건강 잘 챙기시고 시원한 한 주 보내세요.",
            "뜨거운 여름, 시원한 소식과 함께 합니다.",
        ],
        "autumn": [
            "풍성한 가을처럼 보람 가득한 날 되세요.",
            "선선한 바람 속에 좋은 결실 이루시길 바랍니다.",
        ],
        "winter": [
            "따뜻하고 안전한 겨울 되세요.",
            "포근한 하루 보내시고 건강 유의하세요.",
        ],
    },
    "weekdays": {
        0: ["힘찬 월요일 되세요! 새로운 시작을 응원합니다."],
        1: ["화요일, 차근차근 목표에 다가가요."],
        2: ["수요일, 주중의 중심! 한 걸음만 더."],
        3: ["목요일, 마무리 준비에 딱 좋은 날입니다."],
        4: ["금요일, 한 주 잘 마무리하시고 편안한 주말 되세요."],
        5: ["토요일, 재충전과 쉼의 시간이 되길 바랍니다."],
        6: ["일요일, 내일을 위한 휴식 가득한 하루 보내세요."],
    },
    "special_dates": {
        "01-01": ["새해 복 많이 받으세요. 올 한 해도 더욱 더 든든히 함께하겠습니다."],
        "02-14": ["소중한 분들과 따뜻한 마음을 나누는 하루 되세요."],
        "03-01": ["뜻깊은 3·1절, 감사와 존경의 마음을 전합니다."],
        "05-05": ["가정의 달 5월, 사랑과 웃음이 가득하길 바랍니다."],
        "06-06": ["호국보훈의 달, 감사와 추모의 마음을 전합니다."],
        "10-09": ["한글날, 우리말의 아름다움을 함께 기립니다. 한 주도 파이팅!"],
        "12-25": ["메리 크리스마스! 따뜻하고 즐거운 연말 되세요."],
        "12-31": ["한 해 동안 감사했습니다. 새해에도 늘 건강과 행복이 함께하길!"],
    },
}

def _get_kst_now():
    if ZoneInfo:
        return datetime.now(ZoneInfo("Asia/Seoul"))
    return datetime.now()

def _season_by_month(m: int) -> str:
    if 3 <= m <= 5: return "spring"
    if 6 <= m <= 8: return "summer"
    if 9 <= m <= 11: return "autumn"
    return "winter"

def pick_contextual_message(custom_bank: dict | None = None) -> str:
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
    """OpenAI API를 사용해서 맞춤형 메시지 생성"""
    if not COMPANY_CONFIG.get('use_openai') or not COMPANY_CONFIG.get('openai_api_key'):
        return pick_contextual_message()
    
    try:
        client = OpenAI(api_key=COMPANY_CONFIG['openai_api_key'])
        
        prompt = f"""
        {COMPANY_CONFIG['company_name']}의 {tone} 뉴스레터 인사말을 작성해주세요.
        
        조건:
        - 주제: {topic}
        - 톤: {tone}
        - 길이: 2문장
        - 한국어로 작성
        - 법률사무소 특성에 맞게
        - 오늘 날짜: {datetime.now().strftime('%Y년 %m월 %d일 %A')}
        - 큰따옴표 없이 작성
        
        예시 스타일: 새로운 한 주가 시작되었습니다. 언제나 여러분의 든든한 법률 파트너가 되겠습니다.
        """
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=150,
            temperature=0.7
        )
        
        ai_message = response.choices[0].message.content.strip()
        ai_message = ai_message.strip('"').strip("'")
        ai_message = ai_message.replace('"', '').replace('"', '').replace('"', '')
        
        return ai_message
        
    except Exception as e:
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
    """매우 안정적인 이미지 URL 반환 (자연 풍경 포함)"""
    
    # 옵션 1: 검증된 고정 이미지 URLs (비즈니스 + 자연 풍경 혼합)
    reliable_images = [
        # 비즈니스/법률 관련
        "https://images.unsplash.com/photo-1589829545856-d10d557cf95f?w=600&h=200&fit=crop&auto=format",  # 법정
        "https://images.unsplash.com/photo-1521791136064-7986c2920216?w=600&h=200&fit=crop&auto=format",  # 책들
        "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=600&h=200&fit=crop&auto=format",  # 오피스
        "https://images.unsplash.com/photo-1516442719524-a603408c90cb?w=600&h=200&fit=crop&auto=format",  # 비즈니스
        "https://images.unsplash.com/photo-1560472354-b33ff0c44a43?w=600&h=200&fit=crop&auto=format",  # 서류
        "https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=600&h=200&fit=crop&auto=format",  # 저울(정의)
        
        # 자연 풍경 (새로 추가)
        "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=600&h=200&fit=crop&auto=format",  # 산과 호수
        "https://images.unsplash.com/photo-1441974231531-c6227db76b6e?w=600&h=200&fit=crop&auto=format",  # 숲길
        "https://images.unsplash.com/photo-1469474968028-56623f02e42e?w=600&h=200&fit=crop&auto=format",  # 자연 풍경
        "https://images.unsplash.com/photo-1447752875215-b2761acb3c5d?w=600&h=200&fit=crop&auto=format",  # 들판
        "https://images.unsplash.com/photo-1540979388789-6cee28a1cdc9?w=600&h=200&fit=crop&auto=format",  # 해변
        "https://images.unsplash.com/photo-1418065460487-3e41a6c84dc5?w=600&h=200&fit=crop&auto=format",  # 산
        "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=600&h=200&fit=crop&auto=format",  # 호수
        "https://images.unsplash.com/photo-1439066615861-d1af74d74000?w=600&h=200&fit=crop&auto=format",  # 호수와 산
        "https://images.unsplash.com/photo-1501594907352-04cda38ebc29?w=600&h=200&fit=crop&auto=format",  # 바다
        "https://images.unsplash.com/photo-1426604966848-d7adac402bff?w=600&h=200&fit=crop&auto=format",  # 나무
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

def _extract_google_link_improved(link: str) -> str:
    """개선된 Google News 링크 추출 (에러 처리 강화)"""
    try:
        # Google News 리다이렉트가 아닌 경우 그대로 반환
        if "news.google.com" not in link:
            return link
            
        p = urlparse(link)
        if "news.google.com" in p.netloc:
            from urllib.parse import parse_qs
            qs = parse_qs(p.query)
            if "url" in qs and qs["url"]:
                decoded_url = qs["url"][0]
                # URL 유효성 검사
                try:
                    parsed_decoded = urlparse(decoded_url)
                    if parsed_decoded.scheme and parsed_decoded.netloc:
                        return decoded_url
                except:
                    pass
        
        # 추출 실패시 원본 반환 (차단되더라도 일단 포함)
        return link
    except Exception as e:
        print(f"링크 추출 오류: {e}")
        return link

def parse_rss_date(date_str):
    """RSS pubDate를 파싱해서 YYYY.MM.DD 형식으로 변환"""
    if not date_str:
        return datetime.now().strftime('%Y.%m.%d')
    
    try:
        from email.utils import parsedate_to_datetime
        dt = parsedate_to_datetime(date_str)
        return dt.strftime('%Y.%m.%d')
    except:
        try:
            dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            return dt.strftime('%Y.%m.%d')
        except:
            return datetime.now().strftime('%Y.%m.%d')

def fetch_naver_rss(url: str, timeout: float = 10.0):
    """네이버 뉴스 RSS 수집"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        r = requests.get(url, headers=headers, timeout=timeout)
        r.raise_for_status()
        r.encoding = "utf-8"
        root = ET.fromstring(r.text)
        items = []
        
        for it in root.findall(".//item"):
            title = (it.findtext("title") or "").strip()
            link = (it.findtext("link") or "").strip()
            pub_date = (it.findtext("pubDate") or "").strip()
            
            if not title or not link:
                continue
                
            # 제목에서 불필요한 태그 제거
            title = re.sub(r'<[^>]+>', '', title)
            title = re.sub(r'\[.*?\]', '', title).strip()
            
            formatted_date = parse_rss_date(pub_date)
            
            items.append({
                "title": title,
                "url": link,
                "date": formatted_date,
                "source": "Naver",
                "raw_date": pub_date
            })
        return items
    except Exception as e:
        return {"error": f"네이버 RSS 수집 실패: {e}"}

def fetch_daum_rss(url: str, timeout: float = 10.0):
    """다음 뉴스 RSS 수집"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        r = requests.get(url, headers=headers, timeout=timeout)
        r.raise_for_status()
        r.encoding = "utf-8"
        root = ET.fromstring(r.text)
        items = []
        
        for it in root.findall(".//item"):
            title = (it.findtext("title") or "").strip()
            link = (it.findtext("link") or "").strip()
            pub_date = (it.findtext("pubDate") or "").strip()
            
            if not title or not link:
                continue
                
            # 제목 정리
            title = re.sub(r'<[^>]+>', '', title)
            title = re.sub(r'\[.*?\]', '', title).strip()
            
            formatted_date = parse_rss_date(pub_date)
            
            items.append({
                "title": title,
                "url": link,
                "date": formatted_date,
                "source": "Daum",
                "raw_date": pub_date
            })
        return items
    except Exception as e:
        return {"error": f"다음 RSS 수집 실패: {e}"}

def fetch_google_rss(url: str, timeout: float = 10.0):
    """Google News RSS 수집"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        r = requests.get(url, headers=headers, timeout=timeout)
        r.raise_for_status()
        r.encoding = "utf-8"
        root = ET.fromstring(r.text)
        items = []
        
        for it in root.findall(".//item"):
            title = (it.findtext("title") or "").strip()
            link = _extract_google_link_improved((it.findtext("link") or "").strip())
            pub_date = (it.findtext("pubDate") or "").strip()
            
            if not title or not link:
                continue
                
            formatted_date = parse_rss_date(pub_date)
            
            items.append({
                "title": title,
                "url": link,
                "date": formatted_date,
                "source": "Google",
                "raw_date": pub_date
            })
        return items
    except Exception as e:
        return {"error": f"Google RSS 수집 실패: {e}"}

def fetch_mixed_rss(url: str, timeout: float = 10.0):
    """RSS 소스에 따라 적절한 수집 함수 선택"""
    try:
        if "naver.com" in url:
            return fetch_naver_rss(url, timeout)
        elif "daum.net" in url:
            return fetch_daum_rss(url, timeout)
        elif "google.com" in url:
            return fetch_google_rss(url, timeout)
        else:
            # 기타 RSS는 기본 방식 사용
            return fetch_google_rss(url, timeout)
    except Exception as e:
        return {"error": f"RSS 수집 실패: {e}"}

def create_news_cache_key(sources):
    """뉴스 소스 목록을 기반으로 캐시 키 생성"""
    sources_str = '|'.join(sorted(sources))
    return hashlib.md5(sources_str.encode()).hexdigest()

def collect_latest_news(limit: int = 10, fallback_on_fail: bool = True, force_refresh: bool = False):
    """개선된 뉴스 수집 함수 (한국 뉴스만 수집, 포괄적 필터링)"""
    sources = st.session_state.newsletter_data.get('auto_news_sources') or COMPANY_CONFIG['default_news_sources']
    
    # 캐시 확인
    cache_key = create_news_cache_key(sources)
    current_time = datetime.now()
    
    if not force_refresh and 'news_cache' in st.session_state:
        cache_data = st.session_state.news_cache
        if (cache_data.get('key') == cache_key and 
            cache_data.get('timestamp') and 
            (current_time - cache_data['timestamp']).total_seconds() < 1800):
            return cache_data['news']
    
    all_items = []
    titles_seen = set()
    urls_seen = set()
    errors = []
    successful_sources = 0

    # 외국 뉴스 필터링 키워드 (한국이 아닌 모든 외국 관련)
    exclude_keywords = [
        # 아시아 국가들
        '베트남', 'vietnam', '하노이', '호치민', 
        '중국', 'china', '베이징', '상하이', '시진핑',
        '일본', 'japan', '도쿄', '오사카', '기시다',
        '태국', 'thailand', '방콕',
        '필리핀', 'philippines', '마닐라',
        '말레이시아', 'malaysia', '쿠알라룸푸르',
        '싱가포르', 'singapore',
        '인도네시아', 'indonesia', '자카르타',
        '라오스', 'laos', '비엔티안',
        '캄보디아', 'cambodia', '프놈펜',
        '미얀마', 'myanmar', '양곤',
        '인도', 'india', '뉴델리', '뭄바이',
        
        # 미주 국가들
        '미국', 'usa', 'america', '워싱턴', '뉴욕', '트럼프', '바이든',
        '캐나다', 'canada', '오타와', '토론토',
        '멕시코', 'mexico', '멕시코시티',
        '브라질', 'brazil', '브라질리아', '상파울루',
        '아르헨티나', 'argentina', '부에노스아이레스',
        
        # 유럽 국가들
        '영국', 'uk', 'britain', '런던',
        '프랑스', 'france', '파리',
        '독일', 'germany', '베를린',
        '이탈리아', 'italy', '로마',
        '스페인', 'spain', '마드리드',
        '러시아', 'russia', '모스크바', '푸틴',
        '우크라이나', 'ukraine', '키예프', '젤렌스키',
        
        # 중동/아프리카
        '이스라엘', 'israel', '텔아비브',
        '사우디', 'saudi', '리야드',
        '이란', 'iran', '테헤란',
        '이집트', 'egypt', '카이로',
        
        # 국제기구 관련 (해외 소식)
        'nato', 'eu ', 'un ', 'g7', 'g20', 'imf', 'who',
        
        # 기타 외국 지명
        '해외', '국외', '외국인', '외국계'
    ]

    for i, src in enumerate(sources):
        try:
            res = fetch_mixed_rss(src, timeout=8.0)
            
            if isinstance(res, dict) and "error" in res:
                errors.append(f"소스 {i+1}: {res['error']}")
                continue
                
            successful_sources += 1
            valid_items = 0
            
            for item in res:
                # 제목과 URL 정리 및 검증
                title_clean = re.sub(r'\s+', ' ', item["title"].strip())
                url_clean = item["url"].strip()
                
                # 한국 뉴스 필터링 (외국 뉴스 제외 + 한국 관련성 확인)
                title_lower = title_clean.lower()
                
                # 1차: 외국 키워드가 포함된 뉴스는 제외
                if any(keyword in title_lower for keyword in exclude_keywords):
                    continue
                
                # 2차: 한국 관련성 확인 (한국 관련 키워드가 있거나, 한국 언론사 소스인 경우 통과)
                korean_keywords = [
                    '한국', '서울', '부산', '대구', '인천', '광주', '대전', '울산', '세종',
                    '경기', '강원', '충북', '충남', '전북', '전남', '경북', '경남', '제주',
                    '청와대', '국회', '정부', '국정원', '국세청', '검찰', '경찰',
                    '삼성', 'lg', 'sk', '현대', '롯데', '포스코', '네이버', '카카오',
                    '원화', '코스피', '코스닥', '한은', '금융위', '국토부', '복지부'
                ]
                
                is_korean_news = (
                    any(keyword in title_lower for keyword in korean_keywords) or
                    'naver.com' in url_clean or 'daum.net' in url_clean or
                    ('google.com' in url_clean and ('hl=ko' in url_clean or 'gl=KR' in url_clean))
                )
                
                # 한국 관련성이 없는 뉴스는 제외 (단, 법률/정책 일반 키워드는 예외)
                if not is_korean_news:
                    general_policy_keywords = ['법률', '정책', '규제', '법안', '개정', '시행']
                    if not any(keyword in title_lower for keyword in general_policy_keywords):
                        continue
                
                # 중복 검사
                if title_lower in titles_seen or url_clean in urls_seen:
                    continue
                
                # 최소 품질 검사
                if len(title_clean) < 5 or not url_clean.startswith('http'):
                    continue
                
                # 차단된 Google News 링크 필터링
                if "news.google.com" in url_clean and "/articles/" not in url_clean:
                    continue
                    
                titles_seen.add(title_lower)
                urls_seen.add(url_clean)
                all_items.append({
                    **item,
                    "title": title_clean
                })
                valid_items += 1
                
                if len(all_items) >= limit * 3:
                    break
                    
        except Exception as e:
            errors.append(f"소스 {i+1} 처리 중 오류: {str(e)}")
            continue
            
        if len(all_items) >= limit * 2:
            break

    # 날짜순 정렬
    try:
        all_items.sort(key=lambda x: datetime.strptime(x['date'], '%Y.%m.%d'), reverse=True)
    except:
        pass

    # 결과가 부족하면 샘플로 보충
    if len(all_items) < limit and fallback_on_fail:
        if successful_sources == 0:
            return get_sample_news()[:limit]
        elif len(all_items) < limit:
            sample = get_sample_news()
            need = limit - len(all_items)
            for item in sample[:need]:
                if item["title"].lower() not in titles_seen:
                    all_items.append(item)

    final_news = all_items[:limit]
    
    # 캐시 저장
    st.session_state.news_cache = {
        'key': cache_key,
        'timestamp': current_time,
        'news': final_news
    }

    return final_news

def get_sample_news():
    """다양한 시사/사회/경제/법률 샘플 뉴스 데이터 생성"""
    sample_news = [
        {
            'title': '정부, 부동산 규제 완화 정책 발표',
            'url': 'https://news.example.com/policy1',
            'date': datetime.now().strftime('%Y.%m.%d'),
            'source': '자동수집'
        },
        {
            'title': '개인정보보호법 개정안 국회 통과',
            'url': 'https://news.example.com/law1', 
            'date': (datetime.now() - timedelta(days=1)).strftime('%Y.%m.%d'),
            'source': '자동수집'
        },
        {
            'title': '최저임금 인상률 결정 앞두고 논란',
            'url': 'https://news.example.com/economy1',
            'date': (datetime.now() - timedelta(days=2)).strftime('%Y.%m.%d'),
            'source': '자동수집'
        },
        {
            'title': '근로기준법 개정으로 인한 기업 대응 방안',
            'url': 'https://news.example.com/law2',
            'date': (datetime.now() - timedelta(days=3)).strftime('%Y.%m.%d'),
            'source': '자동수집'
        },
        {
            'title': '금융위, 가상자산 규제 강화 방침',
            'url': 'https://news.example.com/finance1',
            'date': (datetime.now() - timedelta(days=4)).strftime('%Y.%m.%d'),
            'source': '자동수집'
        },
        {
            'title': '국세청, 세무조사 디지털화 추진',
            'url': 'https://news.example.com/tax1',
            'date': (datetime.now() - timedelta(days=5)).strftime('%Y.%m.%d'),
            'source': '자동수집'
        },
        {
            'title': '중소기업 지원 정책 확대 발표',
            'url': 'https://news.example.com/policy2',
            'date': (datetime.now() - timedelta(days=6)).strftime('%Y.%m.%d'),
            'source': '자동수집'
        },
        {
            'title': '환경부, 탄소중립 실현 로드맵 공개',
            'url': 'https://news.example.com/environment1',
            'date': (datetime.now() - timedelta(days=7)).strftime('%Y.%m.%d'),
            'source': '자동수집'
        },
        {
            'title': '디지털세법 시행령 발표',
            'url': 'https://news.example.com/law3',
            'date': (datetime.now() - timedelta(days=8)).strftime('%Y.%m.%d'),
            'source': '자동수집'
        },
        {
            'title': '코스피 상장기업 ESG 공시 의무화',
            'url': 'https://news.example.com/finance2',
            'date': (datetime.now() - timedelta(days=9)).strftime('%Y.%m.%d'),
            'source': '자동수집'
        }
    ]
    return sample_news

def save_address_book():
    """주소록을 파일로 저장"""
    if not st.session_state.newsletter_data['address_book'].empty:
        try:
            filename = "address_book_auto_save.csv"
            st.session_state.newsletter_data['address_book'].to_csv(filename, index=False, encoding='utf-8-sig')
            return True
        except:
            return False
    return False

def load_address_book():
    """저장된 주소록 파일 불러오기"""
    try:
        filename = "address_book_auto_save.csv"
        if os.path.exists(filename):
            df = pd.read_csv(filename, encoding='utf-8-sig')
            st.session_state.newsletter_data['address_book'] = df
            return True
    except:
        pass
    return False

def init_default_address_book():
    """기본 주소록 설정"""
    if st.session_state.newsletter_data['address_book'].empty:
        default_df = pd.DataFrame(DEFAULT_ADDRESS_BOOK)
        st.session_state.newsletter_data['address_book'] = default_df
        save_address_book()

def create_html_newsletter(news_items, custom_message=""):
    """이메일 클라이언트 호환성을 최대화한 HTML 뉴스레터 생성"""
    
    # 이미지 가져오기 (항상 성공)
    hero_image_url = None
    if COMPANY_CONFIG.get('use_newsletter_images', True):
        hero_image_url = get_reliable_image(600, 200)
    
    # 이미지 HTML 생성 (이메일 클라이언트 호환성 최대화)
    if hero_image_url:
        if hero_image_url.startswith('data:'):
            # SVG Data URL인 경우
            hero_html = f'''
            <div style="background: url('{hero_image_url}'); background-size: cover; background-position: center; height: 200px; display: block;">
                <table cellpadding="0" cellspacing="0" width="100%" height="200" style="background: url('{hero_image_url}'); background-size: cover; background-position: center;">
                    <tr>
                        <td align="center" valign="middle" style="color: white; text-align: center;">
                        </td>
                    </tr>
                </table>
            </div>
            '''
        else:
            # 외부 이미지 URL인 경우
            hero_html = f'''
            <div style="position: relative; height: 200px; background-image: linear-gradient(rgba(102, 126, 234, 0.7), rgba(118, 75, 162, 0.7)), url('{hero_image_url}'); background-size: cover; background-position: center;">
                <table cellpadding="0" cellspacing="0" width="100%" height="200">
                    <tr>
                        <td align="center" valign="middle" style="color: white; text-align: center;">
                            <h2 style="margin: 0; font-size: 28px; font-weight: bold; color: white; text-shadow: 2px 2px 4px rgba(0,0,0,0.5);">
                                법률 뉴스레터
                            </h2>
                            <p style="margin: 10px 0 0 0; font-size: 16px; color: white; text-shadow: 1px 1px 2px rgba(0,0,0,0.5);">
                                신뢰할 수 있는 법률 정보
                            </p>
                        </td>
                    </tr>
                </table>
            </div>
            '''
    else:
        # 이미지 없는 경우의 기본 헤더
        hero_html = '''
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); height: 200px;">
            <table cellpadding="0" cellspacing="0" width="100%" height="200">
                <tr>
                    <td align="center" valign="middle" style="color: white; text-align: center;">
                        <h2 style="margin: 0; font-size: 28px; font-weight: bold; color: white;">
                            법률 뉴스레터
                        </h2>
                        <p style="margin: 10px 0 0 0; font-size: 16px; color: white;">
                            신뢰할 수 있는 법률 정보
                        </p>
                    </td>
                </tr>
            </table>
        </div>
        '''
    
    # 사무실 정보
    office_info = COMPANY_CONFIG['office_info']
    today = datetime.now().strftime('%Y년 %m월 %d일')
    
    # 인사말과 커스텀 메시지를 자연스럽게 결합
    if custom_message:
        combined_greeting = f"""
        {COMPANY_CONFIG['default_greeting']}<br>
        {custom_message} 
        """
    else:
        combined_greeting = f"""
        {COMPANY_CONFIG['default_greeting']}<br>
        """
    
    # 뉴스 아이템 HTML 생성
    news_html = ""
    for i, item in enumerate(news_items, 1):
        news_html += f"""
        <tr>
            <td style="padding: 25px 0; border-bottom: 1px solid #eeeeee;">
                <table cellpadding="0" cellspacing="0" width="100%">
                    <tr>
                        <td style="width: 40px; vertical-align: top; padding-right: 15px;">
                            <div style="width: 30px; height: 30px; background-color: #333333; color: white; border-radius: 50%; text-align: center; line-height: 30px; font-weight: bold; font-size: 14px;">
                                {i}
                            </div>
                        </td>
                        <td style="vertical-align: top;">
                            <a href="{item['url']}" style="color: #000000; text-decoration: none; font-size: 18px; font-weight: 600; line-height: 1.4; display: block; margin-bottom: 8px;">
                                {item['title']}
                            </a>
                            <div style="font-size: 13px; color: #888888; margin-top: 8px;">
                                 {item['date']}
                            </div>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
        """
    
    html_template = f"""
    <!DOCTYPE html>
    <html lang="ko">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <meta http-equiv="X-UA-Compatible" content="IE=edge">
        <title>{COMPANY_CONFIG['company_name']} 뉴스레터</title>
        <!--[if mso]>
        <noscript>
            <xml>
                <o:OfficeDocumentSettings>
                    <o:PixelsPerInch>96</o:PixelsPerInch>
                </o:OfficeDocumentSettings>
            </xml>
        </noscript>
        <![endif]-->
    </head>
    <body style="margin: 0; padding: 0; background-color: #ffffff; font-family: Arial, sans-serif, '맑은 고딕', 'Malgun Gothic', '돋움', Dotum; color: #333333; line-height: 1.6;">
        <table cellpadding="0" cellspacing="0" width="100%" style="background-color: #ffffff;">
            <tr>
                <td align="center" style="padding: 40px 20px;">
                    <!-- 메인 컨테이너 -->
                    <table cellpadding="0" cellspacing="0" width="680" style="max-width: 680px; background-color: #ffffff; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
                        <!-- 헤더 이미지 -->
                        <tr>
                            <td style="padding: 0;">
                                {hero_html}
                            </td>
                        </tr>
                        
                        <!-- 메인 컨텐츠 -->
                        <tr>
                            <td style="padding: 40px 30px;">
                                <!-- 헤더 -->
                                <table cellpadding="0" cellspacing="0" width="100%">
                                    <tr>
                                        <td align="center" style="padding-bottom: 40px; border-bottom: 1px solid #e0e0e0;">
                                            <h1 style="margin: 0 0 8px 0; font-size: 42px; font-weight: 700; color: #000000; letter-spacing: -1px;">Newsletter</h1>
                                            <p style="margin: 0; font-size: 16px; color: #666666; font-weight: 400;">법률 정보 · {today}</p>
                                        </td>
                                    </tr>
                                </table>
                                
                                <!-- 인사말 -->
                                <table cellpadding="0" cellspacing="0" width="100%">
                                    <tr>
                                        <td style="padding: 30px 0 40px 0;">
                                            <p style="margin: 0; font-size: 16px; line-height: 1.8; color: #333333;">
                                                {combined_greeting}
                                            </p>
                                        </td>
                                    </tr>
                                </table>
                                
                                <!-- 뉴스 섹션 -->
                                <table cellpadding="0" cellspacing="0" width="100%">
                                    {news_html}
                                </table>
                            </td>
                        </tr>
                        
                        <!-- 푸터 -->
                        <tr>
                            <td style="background-color: #f8f9fa; padding: 30px; text-align: center;">
                                <!-- 사무실 정보 -->
                                <table cellpadding="0" cellspacing="0" width="100%" style="background-color: #ffffff; border-radius: 5px; border: 1px solid #e0e0e0; margin: 20px 0;">
                                    <tr>
                                        <td style="padding: 20px; text-align: left;">
                                            <h3 style="margin: 0 0 12px 0; font-size: 16px; font-weight: 600; color: #333333;">{COMPANY_CONFIG['company_name']}</h3>
                                            <p style="margin: 6px 0; font-size: 14px; color: #666666;">이메일: {COMPANY_CONFIG['company_email']}</p>
                                            <p style="margin: 6px 0; font-size: 14px; color: #666666;">전화: {office_info['phone']}</p>
                                            <p style="margin: 6px 0; font-size: 14px; color: #666666;">주소: {office_info['address']}</p>
                                            <p style="margin: 6px 0; font-size: 14px; color: #666666;">운영시간: {office_info['business_hours']}</p>
                                            {f"<p style='margin: 6px 0; font-size: 14px; color: #666666;'>웹사이트: {office_info['website']}</p>" if office_info.get('website') else ''}
                                        </td>
                                    </tr>
                                </table>
                                
                                <p style="margin: 15px 0; font-size: 13px; color: #888888; line-height: 1.6;">
                                    <strong>{COMPANY_CONFIG['footer_message']}</strong>
                                </p>
                                <p style="margin: 15px 0; font-size: 13px; color: #888888; line-height: 1.6;">
                                    본 뉴스레터는 법률 정보 제공을 목적으로 발송됩니다.
                                </p>
                                
                                <!-- 수신거부 -->
                                <table cellpadding="0" cellspacing="0" width="100%" style="margin-top: 20px; padding-top: 15px; border-top: 1px solid #e0e0e0;">
                                    <tr>
                                        <td style="text-align: center;">
                                            <p style="margin: 0; font-size: 13px; color: #888888;">
                                                뉴스레터 수신을 중단하시려면 
                                                <a href="mailto:{COMPANY_CONFIG['company_email']}?subject=수신거부신청" style="color: #333333; text-decoration: underline;">여기를 클릭</a>하여 신청해주세요.
                                            </p>
                                            <p style="margin: 15px 0 0 0; font-size: 11px; color: #aaa;">
                                                © 2025 {COMPANY_CONFIG['company_name']}. All rights reserved.
                                            </p>
                                        </td>
                                    </tr>
                                </table>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """
    return html_template

def validate_email(email):
    """이메일 주소 유효성 검사"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def auto_configure_smtp():
    """앱 시작시 자동으로 SMTP 설정을 로드"""
    auto_settings = {
        'server': COMPANY_CONFIG['smtp_server'],
        'port': COMPANY_CONFIG['smtp_port'],
        'email': COMPANY_CONFIG['company_email'],
        'password': COMPANY_CONFIG['company_password'],
        'sender_name': COMPANY_CONFIG['company_name']
    }
    st.session_state.newsletter_data['email_settings'] = auto_settings
    return auto_settings

def send_newsletter(recipients, subject, html_content, smtp_settings):
    """뉴스레터 발송"""
    import smtplib
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
    import re
    
    def simple_clean(text):
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
    
    try:
        clean_server = simple_clean(smtp_settings['server'])
        clean_email = simple_clean(smtp_settings['email']).replace(' ', '')
        clean_password = simple_clean(smtp_settings['password'])
        clean_sender_name = simple_clean(smtp_settings['sender_name'])
        
        server = smtplib.SMTP(clean_server, smtp_settings['port'])
        server.starttls()
        server.login(clean_email, clean_password)
        
        sent_count = 0
        failed_emails = []
        
        clean_subject = simple_clean(subject)
        clean_html = simple_clean(html_content)
        
        for recipient in recipients:
            try:
                clean_recipient = simple_clean(recipient).replace(' ', '')
                
                msg = MIMEMultipart('alternative')
                msg['From'] = f"{clean_sender_name} <{clean_email}>"
                msg['To'] = clean_recipient
                msg['Subject'] = clean_subject
                
                text_content = f"제목: {clean_subject}\n\n이 메일은 HTML 형식입니다."
                text_part = MIMEText(simple_clean(text_content), 'plain', 'utf-8')
                msg.attach(text_part)
                
                html_part = MIMEText(clean_html, 'html', 'utf-8')
                msg.attach(html_part)
                
                server.sendmail(clean_email, [clean_recipient], msg.as_string())
                sent_count += 1
                
            except Exception as e:
                failed_emails.append(f"{recipient}: {str(e)}")
        
        server.quit()
        return sent_count, failed_emails
    
    except Exception as e:
        return 0, [f"SMTP 연결 오류: {str(e)}"]

# 페이지 설정
st.set_page_config(
    page_title=f"{COMPANY_CONFIG['company_name']} 뉴스레터 시스템",
    page_icon="📧",
    layout="wide"
)

# 간소화된 CSS 스타일링
st.markdown("""
<style>
.main-header {
    text-align: center;
    padding: 2rem 0;
    background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
    color: white;
    border-radius: 10px;
    margin-bottom: 2rem;
}
.big-button {
    font-size: 1.2rem !important;
    padding: 1rem 2rem !important;
    margin: 0.5rem !important;
    border-radius: 10px !important;
    width: 100% !important;
}
.status-box {
    padding: 1rem;
    border-radius: 8px;
    margin: 1rem 0;
    text-align: center;
    font-weight: bold;
}
.success-status {
    background-color: #d4edda;
    color: #155724;
    border: 1px solid #c3e6cb;
}
.warning-status {
    background-color: #fff3cd;
    color: #856404;
    border: 1px solid #ffeaa7;
}
.info-status {
    background-color: #d1ecf1;
    color: #0c5460;
    border: 1px solid #bee5eb;
}
</style>
""", unsafe_allow_html=True)

# 세션 상태 초기화
if 'newsletter_data' not in st.session_state:
    st.session_state.newsletter_data = {
        'news_items': [],
        'email_settings': {},
        'address_book': pd.DataFrame(),
        'auto_news_sources': COMPANY_CONFIG['default_news_sources'].copy(),
        'selected_news': [],
        'custom_message': ''
    }
    # 저장된 주소록 자동 로드 or 기본 주소록 설정
    if not load_address_book():
        init_default_address_book()

# 메인 앱
def main():
    # 자동 SMTP 설정 로드
    auto_configure_smtp()
    
    st.markdown(f'<div class="main-header"><h1>📧 {COMPANY_CONFIG["company_name"]}<br>뉴스레터 시스템</h1></div>', 
                unsafe_allow_html=True)
    
    # 현재 상태 확인
    has_news = len(st.session_state.newsletter_data['news_items']) > 0
    has_addresses = len(st.session_state.newsletter_data['address_book']) > 0
    has_selected_news = len(st.session_state.newsletter_data.get('selected_news', [])) > 0
    
    # 상태 표시 (더 직관적으로)
    st.subheader("📊 현재 상태")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if has_news:
            st.markdown(f'<div class="status-box success-status">📰 뉴스 수집됨<br>({len(st.session_state.newsletter_data["news_items"])}개)</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="status-box warning-status">📰 뉴스 없음</div>', unsafe_allow_html=True)
    
    with col2:
        if has_addresses:
            st.markdown(f'<div class="status-box success-status">👥 주소록 준비됨<br>({len(st.session_state.newsletter_data["address_book"])}명)</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="status-box warning-status">👥 주소록 없음</div>', unsafe_allow_html=True)
    
    with col3:
        if has_selected_news:
            st.markdown(f'<div class="status-box success-status">📝 뉴스레터 작성됨<br>({len(st.session_state.newsletter_data["selected_news"])}개 뉴스)</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="status-box info-status">📝 뉴스레터 미작성</div>', unsafe_allow_html=True)
    
    st.write("---")
    
    # 메인 액션 버튼들 (단순하고 직관적)
    st.subheader("🎯 주요 작업")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📰 뉴스 자동 수집", key="collect_news_main", help="최신 뉴스를 자동으로 수집합니다"):
            with st.spinner("뉴스를 수집하는 중..."):
                collected_news = collect_latest_news(force_refresh=False)
                if collected_news:
                    st.session_state.newsletter_data['news_items'] = collected_news
                    st.success(f"✅ {len(collected_news)}개의 뉴스를 수집했습니다!")
                    st.rerun()
                else:
                    st.error("❌ 뉴스 수집에 실패했습니다. 잠시 후 다시 시도해주세요.")
    
    with col2:
        if st.button("📝 뉴스레터 작성", key="create_newsletter_main", help="수집된 뉴스로 뉴스레터를 작성합니다"):
            if not has_news:
                st.error("❌ 먼저 뉴스를 수집해주세요!")
            else:
                # 뉴스레터 작성 섹션으로 이동
                st.session_state.show_newsletter_creation = True
                st.rerun()
    
    # 뉴스레터 작성 섹션 (조건부 표시)
    if has_news and st.session_state.get('show_newsletter_creation', False):
        st.write("---")
        st.subheader("📝 뉴스레터 작성")
        
        # AI 메시지 생성 버튼 (단순화)
        col1, col2, col3 = st.columns(3)
        
        current_message = st.session_state.newsletter_data.get('custom_message', pick_contextual_message())
        
        with col1:
            if st.button("🎯 오늘의 인사말", help="오늘 날짜에 맞는 인사말을 생성합니다"):
                st.session_state.newsletter_data['custom_message'] = pick_contextual_message()
                st.rerun()
        
        with col2:
            if st.button("🤖 AI 인사말", help="AI가 맞춤형 인사말을 생성합니다"):
                if COMPANY_CONFIG.get('openai_api_key'):
                    with st.spinner("AI가 인사말을 생성 중..."):
                        ai_message = generate_ai_message()
                        st.session_state.newsletter_data['custom_message'] = ai_message
                        st.success("✅ AI 인사말이 생성되었습니다!")
                        st.rerun()
                else:
                    st.warning("⚠️ AI 기능을 사용하려면 OpenAI API 키가 필요합니다.")
        
        with col3:
            if st.button("🔄 다시 생성", help="인사말을 다시 생성합니다"):
                st.session_state.newsletter_data['custom_message'] = pick_contextual_message()
                st.rerun()
        
        # 인사말 편집
        custom_message = st.text_area(
            "인사말 편집", 
            value=current_message,
            height=100,
            help="생성된 인사말을 자유롭게 수정할 수 있습니다"
        )
        st.session_state.newsletter_data['custom_message'] = custom_message
        
        # 뉴스 선택 (간소화)
        st.write("**포함할 뉴스 선택:**")
        
        selected_indices = []
        news_items = st.session_state.newsletter_data['news_items']
        
        # 전체 선택/해제 버튼
        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button("전체 선택"):
                st.session_state.all_selected = True
                st.rerun()
        with col2:
            if st.button("전체 해제"):
                st.session_state.all_selected = False
                st.rerun()
        
        # 뉴스 체크박스
        all_selected = st.session_state.get('all_selected', True)
        for i, item in enumerate(news_items):
            if st.checkbox(f"{item['title']} ({item['date']})", value=all_selected, key=f"news_select_{i}"):
                selected_indices.append(i)
        
        selected_news = [news_items[i] for i in selected_indices]
        st.session_state.newsletter_data['selected_news'] = selected_news
        
        if selected_news:
            st.success(f"✅ {len(selected_news)}개 뉴스가 선택되었습니다")
            
            # 미리보기 및 발송 버튼
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("👀 미리보기", key="preview_main"):
                    html_content = create_html_newsletter(selected_news, custom_message)
                    st.components.v1.html(html_content, height=800, scrolling=True)
            
            with col2:
                if st.button("📤 뉴스레터 발송", key="send_main", type="primary"):
                    st.session_state.show_send_section = True
                    st.rerun()
    
    # 발송 섹션 (조건부 표시)
    if has_selected_news and st.session_state.get('show_send_section', False):
        st.write("---")
        st.subheader("📤 뉴스레터 발송")
        
        # 제목 입력
        subject = st.text_input(
            "이메일 제목", 
            value=f"[{COMPANY_CONFIG['company_name']}] 법률 뉴스레터 - {datetime.now().strftime('%Y년 %m월 %d일')}",
            help="발송될 이메일의 제목을 입력하세요"
        )
        
        # 수신자 관리 (간소화)
        st.write("**수신자 관리:**")
        
        all_emails = st.session_state.newsletter_data['address_book']['이메일'].tolist()
        all_names = st.session_state.newsletter_data['address_book']['이름'].tolist()
        
        # 수신자 목록 표시
        st.write(f"📧 총 {len(all_emails)}명의 수신자")
        
        with st.expander("수신자 목록 보기/편집"):
            # 간단한 수신자 편집
            for i, (name, email) in enumerate(zip(all_names, all_emails)):
                col1, col2, col3 = st.columns([2, 3, 1])
                with col1:
                    st.text(name)
                with col2:
                    st.text(email)
                with col3:
                    if st.button("❌", key=f"remove_{i}", help="삭제"):
                        st.session_state.newsletter_data['address_book'] = st.session_state.newsletter_data['address_book'].drop(index=i).reset_index(drop=True)
                        save_address_book()
                        st.rerun()
            
            # 새 수신자 추가
            st.write("**새 수신자 추가:**")
            new_col1, new_col2, new_col3 = st.columns([2, 3, 1])
            with new_col1:
                new_name = st.text_input("이름", key="new_name")
            with new_col2:
                new_email = st.text_input("이메일", key="new_email")
            with new_col3:
                if st.button("➕", key="add_new", help="추가"):
                    if new_name and new_email and validate_email(new_email):
                        new_contact = pd.DataFrame({'이름': [new_name], '이메일': [new_email]})
                        st.session_state.newsletter_data['address_book'] = pd.concat([
                            st.session_state.newsletter_data['address_book'], 
                            new_contact
                        ], ignore_index=True)
                        save_address_book()
                        st.success("✅ 새 수신자가 추가되었습니다!")
                        st.rerun()
                    else:
                        st.error("❌ 올바른 이름과 이메일을 입력하세요!")
        
        # 최종 발송 버튼
        if subject and all_emails:
            st.write("---")
            
            if st.button("🚀 최종 발송", key="final_send", type="primary", help=f"{len(all_emails)}명에게 뉴스레터를 발송합니다"):
                with st.spinner(f"뉴스레터를 {len(all_emails)}명에게 발송 중..."):
                    html_content = create_html_newsletter(
                        st.session_state.newsletter_data['selected_news'],
                        st.session_state.newsletter_data['custom_message']
                    )
                    
                    sent_count, failed_emails = send_newsletter(
                        all_emails,
                        subject,
                        html_content,
                        st.session_state.newsletter_data['email_settings']
                    )
                    
                    if sent_count > 0:
                        st.success(f"🎉 {sent_count}명에게 성공적으로 발송되었습니다!")
                        
                        # 발송 완료 후 초기화
                        st.session_state.show_newsletter_creation = False
                        st.session_state.show_send_section = False
                        
                        # 발송 기록 저장
                        if 'send_history' not in st.session_state:
                            st.session_state.send_history = []
                        
                        st.session_state.send_history.append({
                            'date': datetime.now().strftime('%Y-%m-%d %H:%M'),
                            'subject': subject,
                            'recipients': sent_count,
                            'status': 'success'
                        })
                        
                        st.balloons()
                    
                    if failed_emails:
                        st.error("❌ 일부 발송 실패:")
                        for error in failed_emails[:3]:  # 처음 3개만 표시
                            st.write(f"- {error}")
        else:
            if not subject:
                st.warning("⚠️ 이메일 제목을 입력해주세요")
            if not all_emails:
                st.warning("⚠️ 수신자가 없습니다")
    
    # 하단 도움말
    with st.expander("❓ 사용 도움말"):
        st.write("""
        **간단 사용법:**
        1. **뉴스 자동 수집** 버튼을 눌러 최신 뉴스를 가져옵니다
        2. **뉴스레터 작성** 버튼을 눌러 인사말을 생성하고 뉴스를 선택합니다
        3. **미리보기**로 확인한 후 **뉴스레터 발송** 버튼을 누릅니다
        4. 수신자를 확인하고 **최종 발송** 버튼을 누르면 완료됩니다
        
        **주요 특징:**
        - 모든 설정이 미리 완료되어 있어 바로 사용 가능
        - AI가 상황에 맞는 인사말을 자동 생성
        - 한국 뉴스만 자동 필터링하여 수집
        - 이메일 클라이언트에서 깨지지 않는 안정적인 디자인
        - 주소록 자동 저장 및 관리
        """)

if __name__ == "__main__":
    main()