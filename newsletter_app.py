import streamlit as st
import pandas as pd
from mailer import send_email
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
from datetime import datetime, date
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
from dotenv import load_dotenv
load_dotenv()  # .env 파일에서 환경변수 로드
import hashlib
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
    'company_email': 'lshlawfirm2@gmail.com',  # ← 수정됨
    'company_password': 'wsbn vanl ywza ochf',
    
    # 사무실 정보 (뉴스레터 하단에 표시)
    'office_info': {
        'address': '서울시 송파구 법원로92, 806호 (문정동, 파트너스1)',
        'phone': '02-3477-9650',
        'website': 'https://www.limleelawfirm.com/',
        'business_hours': '평일 09:00-18:00'
    },
    
    # SMTP 설정
    'smtp_server': 'smtp.gmail.com',
    'smtp_port': 587,
    
    # 뉴스 수집 설정
    'auto_collect_news': True,
    'default_news_sources': [
        'https://news.google.com/rss/search?q=법률+개정&hl=ko&gl=KR&ceid=KR:ko',
        'https://news.google.com/rss/search?q=법원+판결&hl=ko&gl=KR&ceid=KR:ko',
        'https://news.google.com/rss/search?q=변호사+법무&hl=ko&gl=KR&ceid=KR:ko',
        'https://news.google.com/rss/search?q=개인정보보호법&hl=ko&gl=KR&ceid=KR:ko',
        'https://news.google.com/rss/search?q=부동산+법률&hl=ko&gl=KR&ceid=KR:ko',
    ],
    
    # 기본 메시지
    'default_subject_template': '[{company_name}] 법률 뉴스레터 - {date}',
    'default_greeting': '안녕하세요, 임앤리 법률사무소입니다. 최신 소식을 전해 드립니다.',
    'footer_message': '더 자세한 상담이 필요하시면 언제든 연락주세요.',
    
    # 자동화 설정
    'skip_email_setup': True,
    'skip_smtp_test': True,
    
    # OpenAI API 설정 (보안을 위해 환경변수 사용)
    'use_openai': True,  # True로 설정하면 OpenAI API 사용
    'openai_api_key': os.getenv('OPENAI_API_KEY', ''),  # 환경변수에서 읽어옴
}

MESSAGE_BANK = {
    "seasons": {
        "spring": [
            "새봄의 기운처럼 좋은 소식이 가득하시길 바랍니다. 🌱",
            "따뜻한 봄바람과 함께 활력을 전합니다. 🌸",
        ],
        "summer": [
            "무더위에도 건강 잘 챙기시고 시원한 한 주 보내세요. 🌊",
            "뜨거운 여름, 시원한 소식과 함께 합니다. ☀️",
        ],
        "autumn": [
            "풍성한 가을처럼 보람 가득한 날 되세요. 🍁",
            "선선한 바람 속에 좋은 결실 이루시길 바랍니다. 🍂",
        ],
        "winter": [
            "따뜻하고 안전한 겨울 되세요. ❄️",
            "포근한 하루 보내시고 건강 유의하세요. 🧣",
        ],
    },
    "weekdays": {
        0: ["힘찬 월요일 되세요! 새로운 시작을 응원합니다. 💪"],
        1: ["화요일, 차근차근 목표에 다가가요. ✨"],
        2: ["수요일, 주중의 중심! 한 걸음만 더. 🏃"],
        3: ["목요일, 마무리 준비에 딱 좋은 날입니다. 📌"],
        4: ["금요일, 한 주 잘 마무리하시고 편안한 주말 되세요. 🎉"],
        5: ["토요일, 재충전과 쉼의 시간이 되길 바랍니다. ☕"],
        6: ["일요일, 내일을 위한 휴식 가득한 하루 보내세요. 🌤️"],
    },
    "special_dates": {
        "01-01": ["새해 복 많이 받으세요. 올 한 해도 더욱 든든히 함께하겠습니다. 🎊"],
        "02-14": ["소중한 분들과 따뜻한 마음을 나누는 하루 되세요. 💝"],
        "03-01": ["뜻깊은 3·1절, 감사와 존경의 마음을 전합니다."],
        "05-05": ["가정의 달 5월, 사랑과 웃음이 가득하길 바랍니다. 👨‍👩‍👧‍👦"],
        "06-06": ["호국보훈의 달, 감사와 추모의 마음을 전합니다."],
        "10-09": ["한글날, 우리말의 아름다움을 함께 기립니다. 한 주도 파이팅!"],
        "12-25": ["메리 크리스마스! 따뜻하고 즐거운 연말 되세요. 🎄"],
        "12-31": ["한 해 동안 감사했습니다. 새해에도 늘 건강과 행복이 함께하길! 🎆"],
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
        candidates = ["늘 믿고 함께해주셔서 감사합니다. 좋은 하루 보내세요. 😊"]

    return random.choice(candidates)

def generate_ai_message(topic="법률", tone="친근한"):
    """OpenAI API를 사용해서 맞춤형 메시지 생성"""
    if not COMPANY_CONFIG.get('use_openai') or not COMPANY_CONFIG.get('openai_api_key'):
        return pick_contextual_message()
    
    try:
        openai.api_key = COMPANY_CONFIG['openai_api_key']
        
        prompt = f"""
        {COMPANY_CONFIG['company_name']}의 {tone} 뉴스레터 인사말을 작성해주세요.
        
        조건:
        - 주제: {topic}
        - 톤: {tone}
        - 길이: 3문장
        - 한국어로 작성
        - 법률사무소 특성에 맞게
        - 오늘 날짜: {datetime.now().strftime('%Y년 %m월 %d일 %A')}
        
        예시 스타일: "새로운 한 주가 시작되었습니다. 언제나 여러분의 든든한 법률 파트너가 되겠습니다."
        """
        
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=150,
            temperature=0.7
        )
        
        return response.choices[0].message.content.strip()
    except Exception as e:
        st.warning(f"AI 메시지 생성 실패: {e}")
        return pick_contextual_message()

def get_unsplash_image(query="law office", width=600, height=200):
    """Unsplash에서 랜덤 이미지 URL 가져오기"""
    try:
        # Unsplash API 없이도 사용할 수 있는 랜덤 이미지 URL
        unsplash_url = f"https://source.unsplash.com/{width}x{height}/?{query}"
        
        # 이미지가 유효한지 확인
        response = requests.head(unsplash_url, timeout=5)
        if response.status_code == 200:
            return unsplash_url
        else:
            # 기본 이미지 URL들
            default_images = [
                f"https://source.unsplash.com/{width}x{height}/?office",
                f"https://source.unsplash.com/{width}x{height}/?business",
                f"https://source.unsplash.com/{width}x{height}/?professional"
            ]
            return random.choice(default_images)
    except:
        # 완전히 실패하면 None 반환 (이미지 없이 진행)
        return None

def _extract_google_link(link: str) -> str:
    """Google News RSS가 중간 리다이렉트 링크를 줄 때 실제 기사 URL 추출"""
    try:
        p = urlparse(link)
        if "news.google.com" in p.netloc:
            from urllib.parse import parse_qs
            qs = parse_qs(p.query)
            if "url" in qs and qs["url"]:
                return qs["url"][0]
    except:
        pass
    return link

def parse_rss_date(date_str):
    """RSS pubDate를 파싱해서 YYYY.MM.DD 형식으로 변환"""
    if not date_str:
        return datetime.now().strftime('%Y.%m.%d')
    
    try:
        # RFC 2822 형식 파싱 시도 (예: "Tue, 19 Dec 2023 14:30:00 GMT")
        from email.utils import parsedate_to_datetime
        dt = parsedate_to_datetime(date_str)
        return dt.strftime('%Y.%m.%d')
    except:
        try:
            # ISO 8601 형식 시도
            dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            return dt.strftime('%Y.%m.%d')
        except:
            # 파싱 실패시 현재 날짜 반환
            return datetime.now().strftime('%Y.%m.%d')

def fetch_google_rss(url: str, timeout: float = 10.0):
    """단일 Google News RSS URL에서 기사 리스트 반환"""
    try:
        r = requests.get(url, timeout=timeout)
        r.raise_for_status()
        r.encoding = "utf-8"
        root = ET.fromstring(r.text)
        items = []
        
        for it in root.findall(".//item"):
            title = (it.findtext("title") or "").strip()
            link = _extract_google_link((it.findtext("link") or "").strip())
            pub_date = (it.findtext("pubDate") or "").strip()
            
            if not title or not link:
                continue
                
            # 날짜 파싱 개선
            formatted_date = parse_rss_date(pub_date)
            
            items.append({
                "title": title,
                "url": link,
                "date": formatted_date,
                "source": "Google",
                "raw_date": pub_date  # 디버깅용
            })
        return items
    except Exception as e:
        return {"error": f"RSS 수집 실패: {e}"}

def create_news_cache_key(sources):
    """뉴스 소스 목록을 기반으로 캐시 키 생성"""
    sources_str = '|'.join(sorted(sources))
    return hashlib.md5(sources_str.encode()).hexdigest()

def collect_latest_news(limit: int = 5, fallback_on_fail: bool = True, force_refresh: bool = False):
    """구글 뉴스 RSS 소스 목록에서 최신 뉴스 수집 (중복 방지 개선)"""
    sources = st.session_state.newsletter_data.get('auto_news_sources') or COMPANY_CONFIG['default_news_sources']
    
    # 캐시 키 생성
    cache_key = create_news_cache_key(sources)
    current_time = datetime.now()
    
    # 캐시 확인 (30분간 유효)
    if not force_refresh and 'news_cache' in st.session_state:
        cache_data = st.session_state.news_cache
        if (cache_data.get('key') == cache_key and 
            cache_data.get('timestamp') and 
            (current_time - cache_data['timestamp']).total_seconds() < 1800):  # 30분
            st.info("🔄 최근에 수집한 뉴스를 사용합니다. (강제 새로고침하려면 '강제 새로고침' 버튼을 사용하세요)")
            return cache_data['news']
    
    all_items = []
    titles_seen = set()
    urls_seen = set()
    errors = []

    for src in sources:
        res = fetch_google_rss(src)
        if isinstance(res, dict) and "error" in res:
            errors.append(res["error"])
            continue
            
        for item in res:
            # 제목과 URL 모두로 중복 확인
            title_clean = re.sub(r'\s+', ' ', item["title"].strip().lower())
            url_clean = item["url"].strip()
            
            if title_clean in titles_seen or url_clean in urls_seen:
                continue
                
            titles_seen.add(title_clean)
            urls_seen.add(url_clean)
            all_items.append(item)
            
            if len(all_items) >= limit * 2:  # 여유있게 수집
                break
                
        if len(all_items) >= limit * 2:
            break

    # 날짜순 정렬 (최신순)
    try:
        all_items.sort(key=lambda x: datetime.strptime(x['date'], '%Y.%m.%d'), reverse=True)
    except:
        pass  # 정렬 실패시 원래 순서 유지

    # 결과가 너무 적으면 샘플로 보충
    if len(all_items) < limit and fallback_on_fail:
        sample = get_sample_news()
        for it in sample:
            title_clean = re.sub(r'\s+', ' ', it["title"].strip().lower())
            if title_clean not in titles_seen:
                all_items.append(it)
                titles_seen.add(title_clean)
                if len(all_items) >= limit:
                    break

    final_news = all_items[:limit]
    
    # 캐시 저장
    st.session_state.news_cache = {
        'key': cache_key,
        'timestamp': current_time,
        'news': final_news
    }

    if errors:
        st.info("일부 RSS에서 오류가 있었습니다:\n- " + "\n- ".join(errors))

    return final_news

def get_sample_news():
    """샘플 법률 뉴스 데이터 생성"""
    sample_news = [
        {
            'title': '개인정보보호법 개정안 국회 통과',
            'url': 'https://news.example.com/law1',
            'date': datetime.now().strftime('%Y.%m.%d'),
            'source': '자동수집'
        },
        {
            'title': '새로운 상속세 면제 한도 확대',
            'url': 'https://news.example.com/law2', 
            'date': (datetime.now() - timedelta(days=1)).strftime('%Y.%m.%d'),
            'source': '자동수집'
        },
        {
            'title': '부동산 계약 관련 법률 개정 사항',
            'url': 'https://news.example.com/law3',
            'date': (datetime.now() - timedelta(days=2)).strftime('%Y.%m.%d'),
            'source': '자동수집'
        },
        {
            'title': '근로기준법 개정으로 인한 기업 대응 방안',
            'url': 'https://news.example.com/law4',
            'date': (datetime.now() - timedelta(days=3)).strftime('%Y.%m.%d'),
            'source': '자동수집'
        },
        {
            'title': '디지털세법 시행령 발표',
            'url': 'https://news.example.com/law5',
            'date': (datetime.now() - timedelta(days=4)).strftime('%Y.%m.%d'),
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

def create_html_newsletter(news_items, custom_message=""):
    """HTML 뉴스레터 생성 (이미지 및 사무실 정보 포함)"""
    
    # 랜덤 이미지 가져오기
    hero_image_url = get_unsplash_image("law office business", 600, 200)
    
    # 이미지 HTML (이미지가 없으면 그라디언트 배경 사용)
    if hero_image_url:
        hero_html = f'''
        <div class="hero-image" style="background-image: url('{hero_image_url}'); background-size: cover; background-position: center;">
            <div style="background: rgba(102, 126, 234, 0.8); padding: 20px; color: white; text-align: center;">
                <h2 style="margin: 0; font-size: 24px;">📧 법률 뉴스레터</h2>
            </div>
        </div>
        '''
    else:
        hero_html = '''
        <div class="hero-image" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); height: 200px; display: flex; align-items: center; justify-content: center; color: white; font-size: 24px; font-weight: bold;">
            📧 법률 뉴스레터
        </div>
        '''
    
    # 사무실 정보
    office_info = COMPANY_CONFIG['office_info']
    
    html_template = f"""
    <!DOCTYPE html>
    <html lang="ko">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{COMPANY_CONFIG['company_name']} 뉴스레터</title>
        <style>
            body {{
                font-family: 'Malgun Gothic', sans-serif;
                margin: 0;
                padding: 20px;
                background-color: #f5f5f5;
                line-height: 1.6;
            }}
            .container {{
                max-width: 600px;
                margin: 0 auto;
                background-color: white;
                border-radius: 10px;
                box-shadow: 0 4px 8px rgba(0,0,0,0.1);
                overflow: hidden;
            }}
            .header {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                text-align: center;
                padding: 30px 20px;
            }}
            .header h1 {{
                margin: 0;
                font-size: 24px;
                font-weight: bold;
            }}
            .header p {{
                margin: 10px 0 0 0;
                font-size: 16px;
                opacity: 0.9;
            }}
            .hero-image {{
                width: 100%;
                height: 200px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                display: flex;
                align-items: center;
                justify-content: center;
                color: white;
                font-size: 18px;
                font-weight: bold;
            }}
            .content {{
                padding: 30px;
            }}
            .greeting {{
                font-size: 16px;
                line-height: 1.6;
                color: #333;
                margin-bottom: 20px;
            }}
            .custom-message {{
                background-color: #f8f9fa;
                border-left: 4px solid #667eea;
                padding: 15px;
                margin: 20px 0;
                font-style: italic;
                border-radius: 0 5px 5px 0;
            }}
            .news-section {{
                margin-top: 30px;
            }}
            .news-item {{
                border-bottom: 1px solid #eee;
                padding: 15px 0;
                transition: background-color 0.3s;
            }}
            .news-item:hover {{
                background-color: #f8f9fa;
            }}
            .news-item:last-child {{
                border-bottom: none;
            }}
            .news-title {{
                color: #667eea;
                text-decoration: none;
                font-weight: bold;
                font-size: 16px;
                display: block;
                margin-bottom: 5px;
                line-height: 1.4;
            }}
            .news-title:hover {{
                color: #764ba2;
                text-decoration: underline;
            }}
            .news-date {{
                color: #888;
                font-size: 12px;
            }}
            .footer {{
                background-color: #f8f9fa;
                padding: 25px;
                text-align: center;
                color: #666;
                font-size: 13px;
                border-top: 1px solid #eee;
            }}
            .office-info {{
                background-color: #667eea;
                color: white;
                padding: 20px;
                text-align: center;
                font-size: 14px;
            }}
            .office-info h3 {{
                margin: 0 0 10px 0;
                font-size: 16px;
            }}
            .office-info p {{
                margin: 5px 0;
            }}
            .unsubscribe {{
                margin-top: 20px;
                padding-top: 15px;
                border-top: 1px solid #ddd;
                font-size: 11px;
                color: #999;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>신뢰할 수 있는</h1>
                <p>{COMPANY_CONFIG['company_name']}</p>
            </div>
            
            {hero_html}
            
            <div class="content">
                <div class="greeting">
                    {COMPANY_CONFIG['default_greeting']}<br>
                    항상 여러분과 함께하는 믿음직한 법률 파트너가 되겠습니다.
                </div>
                
                {f'<div class="custom-message">{custom_message}</div>' if custom_message else ''}
                
                <div class="news-section">
                    <h3 style="color: #333; border-bottom: 2px solid #667eea; padding-bottom: 10px; margin-bottom: 20px;">최신 법률 소식</h3>
                    {generate_news_items_html(news_items)}
                </div>
            </div>
            
            <div class="office-info">
                <h3>📍 {COMPANY_CONFIG['company_name']}</h3>
                <p>📧 {COMPANY_CONFIG['company_email']}</p>
                <p>📞 {office_info['phone']}</p>
                <p>🏢 {office_info['address']}</p>
                <p>🕒 {office_info['business_hours']}</p>
                {f"<p>🌐 {office_info['website']}</p>" if office_info.get('website') else ''}
            </div>
            
            <div class="footer">
                <p><strong>{COMPANY_CONFIG['footer_message']}</strong></p>
                <p>본 메일은 법률정보 제공을 위해 발송되었습니다.</p>
                
                <p style="margin-top: 15px;">© 2025 {COMPANY_CONFIG['company_name']}. All rights reserved.</p>
            </div>
        </div>
    </body>
    </html>
    """
    return html_template

def generate_news_items_html(news_items):
    """뉴스 아이템 HTML 생성"""
    html = ""
    for i, item in enumerate(news_items, 1):
        html += f"""
        <div class="news-item">
            <a href="{item['url']}" class="news-title">{i}. {item['title']}</a>
            <div class="news-date">📅 {item['date']} | 📰 {item.get('source', '자동수집')}</div>
        </div>
        """
    return html

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
    page_title=f"{COMPANY_CONFIG['company_name']} 뉴스레터 발송 시스템",
    page_icon="📧",
    layout="wide"
)

# CSS 스타일링
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
.auto-news-box {
    background-color: #e8f5e8;
    border: 1px solid #4caf50;
    border-radius: 5px;
    padding: 15px;
    margin: 10px 0;
}
.news-source-item {
    background-color: #f8f9fa;
    border: 1px solid #dee2e6;
    border-radius: 5px;
    padding: 10px;
    margin: 5px 0;
}
.success-box {
    background-color: #d4edda;
    border: 1px solid #c3e6cb;
    border-radius: 5px;
    padding: 15px;
    margin: 10px 0;
}
.warning-box {
    background-color: #fff3cd;
    border: 1px solid #ffeaa7;
    border-radius: 5px;
    padding: 15px;
    margin: 10px 0;
}
.ai-message-box {
    background-color: #e3f2fd;
    border: 1px solid #2196f3;
    border-radius: 5px;
    padding: 15px;
    margin: 10px 0;
}
</style>
""", unsafe_allow_html=True)

# 세션 상태 초기화
if 'newsletter_data' not in st.session_state:
    st.session_state.newsletter_data = {
        'news_items': [],
        'email_settings': {},
        'address_book': pd.DataFrame(),
        'auto_news_sources': COMPANY_CONFIG['default_news_sources'].copy()
    }
    # 저장된 주소록 자동 로드
    load_address_book()

# 메인 앱
def main():
    # 자동 SMTP 설정 로드
    auto_configure_smtp()
    
    st.markdown(f'<div class="main-header"><h1>📧 {COMPANY_CONFIG["company_name"]} 뉴스레터 발송 시스템</h1></div>', 
                unsafe_allow_html=True)
    
    # 메뉴 구성
    menu_options = ["🏠 홈", "📰 뉴스 수집", "📝 뉴스레터 작성", "👥 주소록 관리", "📤 발송하기"]
    
    if not COMPANY_CONFIG['skip_email_setup']:
        menu_options.insert(-1, "📧 이메일 설정")
    
    menu = st.sidebar.selectbox("메뉴 선택", menu_options)
    
    # OpenAI 설정 (사이드바) - OpenAI가 설치되어 있고, 상단에서 미리 설정하지 않은 경우만 표시
    if OPENAI_AVAILABLE and not COMPANY_CONFIG.get('openai_api_key'):
        with st.sidebar.expander("🤖 AI 설정 (선택사항)"):
            st.info("💡 상단 COMPANY_CONFIG에서 미리 설정하면 이 과정을 생략할 수 있습니다")
            use_ai = st.checkbox("OpenAI API 사용", value=COMPANY_CONFIG.get('use_openai', False))
            if use_ai:
                api_key = st.text_input("OpenAI API 키", type="password", 
                                       value=COMPANY_CONFIG.get('openai_api_key', ''))
                if api_key:
                    COMPANY_CONFIG['use_openai'] = True
                    COMPANY_CONFIG['openai_api_key'] = api_key
                    st.success("✅ AI 메시지 생성 활성화")
                else:
                    st.info("API 키를 입력하면 AI가 맞춤형 메시지를 생성합니다")
            else:
                COMPANY_CONFIG['use_openai'] = False
    elif OPENAI_AVAILABLE and COMPANY_CONFIG.get('openai_api_key'):
        # 상단에서 이미 설정된 경우
        if COMPANY_CONFIG.get('use_openai'):
            st.sidebar.success("🤖 AI 메시지 생성 활성화됨")
        else:
            st.sidebar.info("🤖 AI 설정 완료 (비활성화)")
    elif not OPENAI_AVAILABLE:
        st.sidebar.info("🤖 AI 기능: openai 모듈 미설치\n(pip install openai로 설치 가능)")
    
    
    if menu == "🏠 홈":
        st.header("환영합니다! 👋")
        
        # 자동 설정 상태 표시
        st.markdown('<div class="auto-news-box">✅ 이메일 설정이 자동으로 구성되었습니다!</div>', 
                   unsafe_allow_html=True)
        
        st.write(f"""
        **{COMPANY_CONFIG['company_name']} 뉴스레터 발송 시스템**
        
        이 시스템을 사용하여 손쉽게 뉴스레터를 작성하고 발송할 수 있습니다.
        
        **사용 방법:**
        1. **뉴스 수집**: 최신 법률 뉴스를 자동으로 수집하세요
        2. **주소록 관리**: 수신자 명단을 관리하세요  
        3. **뉴스레터 작성**: 수집된 뉴스로 뉴스레터를 작성하세요
        4. **발송하기**: 작성된 뉴스레터를 발송하세요
        
        **새로운 기능:**
        - 🎨 랜덤 이미지 자동 추가
        - 🤖 AI 맞춤형 메시지 생성
        - 💾 주소록 자동 저장/불러오기
        - 📅 정확한 뉴스 날짜 표시
        - 🏢 사무실 정보 및 수신거부 안내
        """)
        
        # 통계 정보
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("📰 뉴스 항목", len(st.session_state.newsletter_data['news_items']))
        with col2:
            st.metric("👥 주소록", len(st.session_state.newsletter_data['address_book']))
        with col3:
            smtp_configured = bool(st.session_state.newsletter_data['email_settings'])
            st.metric("📧 이메일", "✅" if smtp_configured else "❌")
        with col4:
            ai_status = "✅" if COMPANY_CONFIG.get('use_openai') else "📝"
            st.metric("🤖 AI 메시지", ai_status)
    
    elif menu == "📰 뉴스 수집":
        st.header("뉴스 자동 수집")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.subheader("📡 뉴스 소스 관리")
            
            # 뉴스 소스 표시
            for i, source in enumerate(st.session_state.newsletter_data['auto_news_sources']):
                col_a, col_b = st.columns([4, 1])
                with col_a:
                    st.text(f"{i+1}. {source}")
                with col_b:
                    if st.button("🗑️", key=f"source_delete_{i}"):
                        st.session_state.newsletter_data['auto_news_sources'].pop(i)
                        st.rerun()
            
            # 새 소스 추가
            new_source = st.text_input("새로운 뉴스 소스 URL 추가")
            if st.button("➕ 소스 추가") and new_source:
                st.session_state.newsletter_data['auto_news_sources'].append(new_source)
                st.rerun()
        
        with col2:
            st.subheader("구글 뉴스 수집")
            
            if st.button("최신 뉴스 수집", type="primary"):
                with st.spinner("구글에서 뉴스를 수집하는 중..."):
                    collected_news = collect_latest_news(force_refresh=False)
                    
                    if collected_news:
                        st.session_state.newsletter_data['news_items'] = collected_news
                        st.success(f"구글에서 {len(collected_news)}개의 뉴스를 수집했습니다!")
                        st.rerun()
                    else:
                        st.warning("수집된 뉴스가 없습니다. 네트워크 연결을 확인하세요.")
            
            if st.button("🔄 강제 새로고침"):
                with st.spinner("새로운 뉴스를 강제로 수집하는 중..."):
                    collected_news = collect_latest_news(force_refresh=True)
                    if collected_news:
                        st.session_state.newsletter_data['news_items'] = collected_news
                        st.success(f"새로 {len(collected_news)}개의 뉴스를 수집했습니다!")
                        st.rerun()
            
            st.write("---")
            
            if st.button("뉴스 목록 초기화"):
                st.session_state.newsletter_data['news_items'] = []
                if 'news_cache' in st.session_state:
                    del st.session_state.news_cache
                st.success("뉴스 목록이 초기화되었습니다.")
                st.rerun()
            
            # 구글 뉴스 검색 키워드 추가
            st.subheader("검색 키워드")
            new_keyword = st.text_input("새로운 검색 키워드")
            if st.button("키워드 추가") and new_keyword:
                encoded_keyword = quote(new_keyword)
                new_url = f"https://news.google.com/rss/search?q={encoded_keyword}&hl=ko&gl=KR&ceid=KR:ko"
                st.session_state.newsletter_data['auto_news_sources'].append(new_url)
                st.success(f"'{new_keyword}' 키워드가 추가되었습니다.")
                st.rerun()
        
        # 수집된 뉴스 미리보기
        if st.session_state.newsletter_data['news_items']:
            st.subheader("📋 수집된 뉴스 목록")
            for i, item in enumerate(st.session_state.newsletter_data['news_items']):
                with st.expander(f"{i+1}. {item['title']} ({item['date']})"):
                    st.write(f"🔗 **URL**: {item['url']}")
                    st.write(f"📅 **날짜**: {item['date']}")
                    st.write(f"📰 **소스**: {item.get('source', '수동입력')}")
                    if 'raw_date' in item:
                        st.write(f"🔍 **원본 날짜**: {item['raw_date']}")
    
    elif menu == "📝 뉴스레터 작성":
        st.header("뉴스레터 작성")
        
        # 뉴스가 없는 경우 안내
        if not st.session_state.newsletter_data['news_items']:
            st.warning("먼저 '뉴스 수집' 메뉴에서 뉴스를 수집하세요.")
            if st.button("📄 뉴스 수집하러 가기"):
                st.session_state.selected_menu = "📰 뉴스 수집"
                st.rerun()
            return
        
        # 메시지 생성 옵션
        st.subheader("✨ 맞춤형 메시지 생성")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🎯 시즌·요일 메시지"):
                st.session_state.current_message = pick_contextual_message()
                st.rerun()
        
        with col2:
            if st.button("🔄 랜덤 다시 뽑기"):
                st.session_state.current_message = pick_contextual_message()
                st.rerun()
        
        with col3:
            if COMPANY_CONFIG.get('use_openai') and st.button("🤖 AI 맞춤 메시지"):
                with st.spinner("AI가 메시지를 생성하는 중..."):
                    ai_message = generate_ai_message()
                    st.session_state.current_message = ai_message
                    st.markdown(f'<div class="ai-message-box">🤖 AI가 생성한 메시지: {ai_message}</div>', 
                               unsafe_allow_html=True)
                    st.rerun()
        
        # 기본 메시지 설정
        if "current_message" not in st.session_state:
            st.session_state.current_message = pick_contextual_message()
        
        custom_message = st.text_area(
            label="사용자 정의 메시지",
            value=st.session_state.current_message,
            height=100,
            help="버튼으로 추천 문구를 바꾼 뒤, 필요하면 직접 수정해서 사용하세요."
        )
        
        # 뉴스 선택
        st.subheader("📰 포함할 뉴스 선택")
        
        selected_indices = []
        for i, item in enumerate(st.session_state.newsletter_data['news_items']):
            if st.checkbox(f"{item['title']} ({item['date']})", value=True, key=f"news_select_{i}"):
                selected_indices.append(i)
        
        # 선택된 뉴스로 필터링
        selected_news = [st.session_state.newsletter_data['news_items'][i] for i in selected_indices]
        
        if selected_news:
            st.write(f"선택된 뉴스: {len(selected_news)}개")
            
            # 미리보기
            if st.button("👀 뉴스레터 미리보기"):
                html_content = create_html_newsletter(selected_news, custom_message)
                st.components.v1.html(html_content, height=800, scrolling=True)
            
            # 선택된 뉴스를 세션에 저장
            st.session_state.newsletter_data['selected_news'] = selected_news
            st.session_state.newsletter_data['custom_message'] = custom_message
    
    elif menu == "👥 주소록 관리":
        st.header("주소록 관리")
        
        # 주소록 자동 저장/불러오기 안내
        col1, col2 = st.columns(2)
        with col1:
            st.info("💾 주소록은 자동으로 저장됩니다")
        with col2:
            if st.button("🔄 저장된 주소록 다시 불러오기"):
                if load_address_book():
                    st.success("저장된 주소록을 불러왔습니다!")
                    st.rerun()
                else:
                    st.warning("저장된 주소록이 없습니다.")
        
        # 파일 업로드
        uploaded_file = st.file_uploader("CSV 파일 업로드 (이름, 이메일 열 필요)", type=['csv'])
        
        if uploaded_file:
            try:
                df = pd.read_csv(uploaded_file)
                st.session_state.newsletter_data['address_book'] = df
                save_address_book()  # 자동 저장
                st.success("주소록이 성공적으로 업로드되었습니다!")
                st.rerun()
            except Exception as e:
                st.error(f"파일 업로드 중 오류가 발생했습니다: {str(e)}")
        
        # 수동 입력
        with st.expander("➕ 수동으로 연락처 추가"):
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("이름")
            with col2:
                email = st.text_input("이메일")
            
            if st.button("추가"):
                if name and email and validate_email(email):
                    new_contact = pd.DataFrame({'이름': [name], '이메일': [email]})
                    if st.session_state.newsletter_data['address_book'].empty:
                        st.session_state.newsletter_data['address_book'] = new_contact
                    else:
                        st.session_state.newsletter_data['address_book'] = pd.concat([
                            st.session_state.newsletter_data['address_book'], 
                            new_contact
                        ], ignore_index=True)
                    save_address_book()  # 자동 저장
                    st.success("연락처가 추가되었습니다!")
                    st.rerun()
                else:
                    st.error("올바른 이름과 이메일을 입력해주세요.")
        
        # 현재 주소록 표시
        if not st.session_state.newsletter_data['address_book'].empty:
            st.subheader(f"현재 주소록 ({len(st.session_state.newsletter_data['address_book'])}명)")
            
            # 주소록 편집 기능
            edited_df = st.data_editor(
                st.session_state.newsletter_data['address_book'],
                num_rows="dynamic",
                use_container_width=True
            )
            
            if not edited_df.equals(st.session_state.newsletter_data['address_book']):
                st.session_state.newsletter_data['address_book'] = edited_df
                save_address_book()  # 자동 저장
                st.success("주소록 변경사항이 저장되었습니다!")
            
            # 다운로드 버튼
            csv = st.session_state.newsletter_data['address_book'].to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                label="📥 주소록 다운로드 (CSV)",
                data=csv,
                file_name=f"address_book_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
        else:
            st.info("아직 등록된 주소록이 없습니다. CSV 파일을 업로드하거나 수동으로 추가해보세요.")
    
    elif menu == "📤 발송하기":
        st.header("뉴스레터 발송")
        
        # 발송 전 체크리스트
        email_configured = bool(st.session_state.newsletter_data['email_settings'])
        has_news = bool(st.session_state.newsletter_data.get('selected_news', []))
        has_addresses = not st.session_state.newsletter_data['address_book'].empty
        
        st.subheader("📋 발송 준비 상태")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.write("📧 이메일 설정")
            st.success("✅ 자동 구성됨")
        
        with col2:
            st.write("📰 뉴스레터")
            if has_news:
                st.success(f"✅ {len(st.session_state.newsletter_data.get('selected_news', []))}개 뉴스")
            else:
                st.error("❌ 뉴스레터 미작성")
        
        with col3:
            st.write("👥 주소록")
            if has_addresses:
                st.success(f"✅ {len(st.session_state.newsletter_data['address_book'])}명")
            else:
                st.error("❌ 주소록 없음")
        
        if email_configured and has_news and has_addresses:
            st.markdown('<div class="success-box">모든 준비가 완료되었습니다! 🎉</div>', 
                       unsafe_allow_html=True)
            
            # 발송 설정
            subject = st.text_input(
                "이메일 제목", 
                value=f"[{COMPANY_CONFIG['company_name']}] 법률 뉴스레터 - {datetime.now().strftime('%Y년 %m월 %d일')}"
            )
            
            # 수신자 선택
            all_emails = st.session_state.newsletter_data['address_book']['이메일'].tolist()
            selected_emails = st.multiselect(
                "수신자 선택 (전체 선택하려면 비워두세요)",
                options=all_emails,
                default=all_emails
            )
            
            if not selected_emails:
                selected_emails = all_emails
            
            st.write(f"📧 발송 대상: {len(selected_emails)}명")
            
            # 발송 미리보기
            if st.button("👀 발송 전 최종 미리보기"):
                html_content = create_html_newsletter(
                    st.session_state.newsletter_data.get('selected_news', []),
                    st.session_state.newsletter_data.get('custom_message', '')
                )
                st.components.v1.html(html_content, height=800, scrolling=True)
            
            # 발송 버튼
            if st.button("🚀 뉴스레터 발송", type="primary"):
                if subject:
                    with st.spinner("뉴스레터를 발송 중입니다..."):
                        html_content = create_html_newsletter(
                            st.session_state.newsletter_data.get('selected_news', []),
                            st.session_state.newsletter_data.get('custom_message', '')
                        )
                        
                        sent_count, failed_emails = send_newsletter(
                            selected_emails,
                            subject,
                            html_content,
                            st.session_state.newsletter_data['email_settings']
                        )
                        
                        if sent_count > 0:
                            st.success(f"✅ {sent_count}명에게 성공적으로 발송되었습니다!")
                            
                            # 발송 기록 저장
                            if 'send_history' not in st.session_state:
                                st.session_state.send_history = []
                            
                            st.session_state.send_history.append({
                                'date': datetime.now().strftime('%Y-%m-%d %H:%M'),
                                'subject': subject,
                                'recipients': sent_count,
                                'status': 'success'
                            })
                        
                        if failed_emails:
                            st.error("❌ 발송 실패:")
                            for error in failed_emails:
                                st.write(f"- {error}")
                else:
                    st.error("이메일 제목을 입력해주세요.")
        else:
            st.markdown('<div class="warning-box">발송하기 전에 모든 설정을 완료해주세요.</div>', 
                       unsafe_allow_html=True)
            
            # 부족한 설정으로 이동하는 버튼들
            if not has_news:
                if st.button("📝 뉴스레터 작성하러 가기"):
                    st.rerun()
            
            if not has_addresses:
                if st.button("👥 주소록 관리하러 가기"):
                    st.rerun()

if __name__ == "__main__":
    main()