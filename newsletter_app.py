#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
법률사무소 뉴스레터 발송 시스템
완전한 통합 버전
"""

import streamlit as st
import pandas as pd
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
import os
import json
import time
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import urlparse
import base64
from io import BytesIO

# 새로 추가된 모듈들 import
try:
    from news_crawler import NewsCollector
    from greeting_generator import GreetingGenerator
except ImportError:
    st.error("❌ news_crawler.py 또는 greeting_generator.py 파일이 없습니다. 해당 파일들을 같은 폴더에 저장해주세요.")
    st.stop()

# 페이지 설정
st.set_page_config(
    page_title="법률사무소 뉴스레터 발송 시스템",
    page_icon="📧",
    layout="wide"
)

# 데이터 저장 디렉토리 생성
DATA_DIR = Path("newsletter_data")
DATA_DIR.mkdir(exist_ok=True)

ADDRESS_BOOK_FILE = DATA_DIR / "address_book.csv"
SETTINGS_FILE = DATA_DIR / "settings.json"
NEWS_CACHE_FILE = DATA_DIR / "news_cache.json"

# === 데이터 관리 함수들 ===
def load_address_book():
    """주소록 로드"""
    if ADDRESS_BOOK_FILE.exists():
        try:
            df = pd.read_csv(ADDRESS_BOOK_FILE, encoding='utf-8')
            if '분류' not in df.columns:
                df['분류'] = '일반고객'
            if '메모' not in df.columns:
                df['메모'] = ''
            return df
        except:
            return pd.DataFrame(columns=['이름', '이메일', '분류', '메모'])
    return pd.DataFrame(columns=['이름', '이메일', '분류', '메모'])

def save_address_book(df):
    """주소록 저장"""
    try:
        df.to_csv(ADDRESS_BOOK_FILE, index=False, encoding='utf-8-sig')
        return True
    except Exception as e:
        st.error(f"주소록 저장 중 오류: {e}")
        return False

def load_persistent_settings():
    """설정 파일 로드"""
    if SETTINGS_FILE.exists():
        try:
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_persistent_settings(settings):
    """설정 파일 저장"""
    try:
        with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(settings, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        st.error(f"설정 저장 중 오류: {e}")
        return False

def load_news_cache():
    """뉴스 캐시 로드"""
    if NEWS_CACHE_FILE.exists():
        try:
            with open(NEWS_CACHE_FILE, 'r', encoding='utf-8') as f:
                cache = json.load(f)
                today = datetime.now().strftime('%Y-%m-%d')
                if cache.get('date') == today:
                    return cache.get('news', [])
        except:
            pass
    return []

def save_news_cache(news_list):
    """뉴스 캐시 저장"""
    try:
        cache_data = {
            'date': datetime.now().strftime('%Y-%m-%d'),
            'news': news_list,
            'timestamp': datetime.now().isoformat()
        }
        with open(NEWS_CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        st.error(f"뉴스 캐시 저장 중 오류: {e}")
        return False

# === 세션 상태 초기화 ===
if 'newsletter_data' not in st.session_state:
    st.session_state.newsletter_data = {
        'news_items': load_news_cache(),
        'email_settings': load_persistent_settings(),
        'address_book': load_address_book(),
        'auto_greeting': True,
        'custom_greeting': ""
    }

if 'news_collector' not in st.session_state:
    st.session_state.news_collector = NewsCollector()

if 'greeting_generator' not in st.session_state:
    st.session_state.greeting_generator = GreetingGenerator()

# === CSS 스타일링 ===
st.markdown("""
<style>
/* 기본 스타일 */
.main-header {
    text-align: center;
    padding: 2.5rem 0;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border-radius: 15px;
    margin-bottom: 2rem;
    box-shadow: 0 8px 32px rgba(102, 126, 234, 0.3);
}

.main-header h1 {
    font-size: 2.5rem;
    font-weight: 700;
    margin: 0;
    text-shadow: 0 2px 4px rgba(0,0,0,0.3);
}

/* 진행 단계 표시 */
.progress-container {
    background: white;
    border-radius: 15px;
    padding: 20px;
    margin: 20px 0;
    box-shadow: 0 4px 20px rgba(0,0,0,0.1);
    border: 1px solid #e9ecef;
}

.progress-steps {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
}

.step {
    display: flex;
    flex-direction: column;
    align-items: center;
    flex: 1;
    position: relative;
}

.step-number {
    width: 40px;
    height: 40px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: bold;
    margin-bottom: 8px;
    transition: all 0.3s ease;
}

.step-active {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
}

.step-completed {
    background: #28a745;
    color: white;
}

.step-pending {
    background: #e9ecef;
    color: #6c757d;
}

.step-title {
    font-size: 14px;
    font-weight: 600;
    text-align: center;
    color: #495057;
}

/* 섹션 카드 */
.section-card {
    background: white;
    border-radius: 15px;
    padding: 25px;
    margin: 20px 0;
    box-shadow: 0 4px 20px rgba(0,0,0,0.1);
    border: 1px solid #e9ecef;
    transition: all 0.3s ease;
}

.section-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 30px rgba(0,0,0,0.15);
}

.section-header {
    display: flex;
    align-items: center;
    margin-bottom: 20px;
    padding-bottom: 15px;
    border-bottom: 2px solid #f8f9fa;
}

.section-icon {
    font-size: 24px;
    margin-right: 12px;
}

.section-title {
    font-size: 20px;
    font-weight: 700;
    color: #2c3e50;
    margin: 0;
}

/* 상태 표시 */
.status-badge {
    display: inline-flex;
    align-items: center;
    padding: 6px 12px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 600;
    margin-left: 10px;
}

.status-ready {
    background: #d4edda;
    color: #155724;
}

.status-warning {
    background: #fff3cd;
    color: #856404;
}

.status-error {
    background: #f8d7da;
    color: #721c24;
}

/* 뉴스 아이템 카드 */
.news-item-card {
    border: 1px solid #e9ecef;
    border-radius: 12px;
    padding: 20px;
    margin: 15px 0;
    background: linear-gradient(145deg, #ffffff 0%, #f8f9fa 100%);
    transition: all 0.3s ease;
    position: relative;
}

.news-item-card:hover {
    transform: translateY(-3px);
    box-shadow: 0 8px 25px rgba(0,0,0,0.15);
    border-color: #667eea;
}

.category-tag {
    display: inline-block;
    padding: 4px 12px;
    border-radius: 15px;
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

.category-society { background-color: #e3f2fd; color: #1976d2; }
.category-economy { background-color: #f3e5f5; color: #7b1fa2; }
.category-culture { background-color: #e8f5e8; color: #388e3c; }

/* 통계 카드 */
.stat-card {
    background: white;
    border-radius: 12px;
    padding: 20px;
    text-align: center;
    box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    border: 1px solid #e9ecef;
    transition: all 0.3s ease;
}

.stat-card:hover {
    transform: translateY(-3px);
    box-shadow: 0 8px 25px rgba(0,0,0,0.15);
}

.stat-icon {
    font-size: 32px;
    margin-bottom: 10px;
}

.stat-number {
    font-size: 24px;
    font-weight: 700;
    color: #2c3e50;
    margin: 5px 0;
}

.stat-label {
    font-size: 14px;
    color: #6c757d;
    font-weight: 500;
}

/* 알림 박스 */
.alert {
    padding: 15px 20px;
    border-radius: 10px;
    margin: 15px 0;
    border-left: 4px solid;
    font-weight: 500;
}

.alert-success {
    background-color: #d4edda;
    border-color: #28a745;
    color: #155724;
}

.alert-warning {
    background-color: #fff3cd;
    border-color: #ffc107;
    color: #856404;
}

.alert-error {
    background-color: #f8d7da;
    border-color: #dc3545;
    color: #721c24;
}

.alert-info {
    background-color: #d1ecf1;
    border-color: #17a2b8;
    color: #0c5460;
}

/* 모바일 반응형 */
@media (max-width: 768px) {
    .progress-steps {
        flex-direction: column;
        gap: 15px;
    }
    
    .step {
        flex-direction: row;
        justify-content: flex-start;
        width: 100%;
    }
    
    .step-title {
        margin-left: 15px;
        text-align: left;
    }
    
    .section-card {
        padding: 20px 15px;
    }
}

/* 애니메이션 */
@keyframes fadeInUp {
    from {
        opacity: 0;
        transform: translateY(20px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

.fade-in-up {
    animation: fadeInUp 0.6s ease-out;
}
</style>
""", unsafe_allow_html=True)

# === 유틸리티 함수들 ===
def validate_email(email):
    """이메일 주소 유효성 검사"""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def display_progress_steps(current_step="home"):
    """진행 단계 표시 (간단한 버전)"""
    steps = [
        {"id": "settings", "title": "📧 이메일 설정"},
        {"id": "addresses", "title": "👥 주소록 관리"}, 
        {"id": "content", "title": "📝 뉴스레터 작성"},
        {"id": "preview", "title": "👀 미리보기"},
        {"id": "send", "title": "🚀 발송"}
    ]
    
    # 현재 상태 체크
    email_configured = bool(st.session_state.newsletter_data['email_settings'])
    has_addresses = not st.session_state.newsletter_data['address_book'].empty
    has_content = bool(st.session_state.newsletter_data['news_items'])
    
    step_status = {
        "settings": "✅" if email_configured else "⏳",
        "addresses": "✅" if has_addresses else "⏳", 
        "content": "✅" if has_content else "⏳",
        "preview": "✅" if (email_configured and has_addresses and has_content) else "⏳",
        "send": "✅" if (email_configured and has_addresses and has_content) else "⏳"
    }
    
    # 현재 단계 활성화
    if current_step in step_status:
        step_status[current_step] = "🔄"
    
    # 간단한 텍스트로 표시
    st.markdown("### 📋 진행 단계")
    
    cols = st.columns(5)
    for i, step in enumerate(steps):
        with cols[i]:
            status = step_status[step["id"]]
            st.markdown(f"**{status} {step['title']}**")

def show_alert(message, alert_type="info"):
    """알림 메시지 표시"""
    st.markdown(f"""
    <div class="alert alert-{alert_type}">
        {message}
    </div>
    """, unsafe_allow_html=True)

def display_status_summary():
    """전체 상태 요약 표시"""
    email_configured = bool(st.session_state.newsletter_data['email_settings'])
    has_addresses = not st.session_state.newsletter_data['address_book'].empty
    has_content = bool(st.session_state.newsletter_data['news_items'])
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        status = "✅ 완료" if email_configured else "❌ 미완료"
        color = "#28a745" if email_configured else "#dc3545"
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-icon">📧</div>
            <div class="stat-label">이메일 설정</div>
            <div class="stat-number" style="color: {color};">{status}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        count = len(st.session_state.newsletter_data['address_book'])
        color = "#28a745" if count > 0 else "#dc3545"
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-icon">👥</div>
            <div class="stat-label">주소록</div>
            <div class="stat-number" style="color: {color};">{count}명</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        count = len(st.session_state.newsletter_data['news_items'])
        color = "#28a745" if count > 0 else "#dc3545"
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-icon">📰</div>
            <div class="stat-label">뉴스 항목</div>
            <div class="stat-number" style="color: {color};">{count}개</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        ready = email_configured and has_addresses and has_content
        status = "준비완료" if ready else "준비중"
        color = "#28a745" if ready else "#ffc107"
        icon = "🚀" if ready else "⏳"
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-icon">{icon}</div>
            <div class="stat-label">발송 준비</div>
            <div class="stat-number" style="color: {color};">{status}</div>
        </div>
        """, unsafe_allow_html=True)

# === 뉴스레터 생성 함수들 ===
def create_html_newsletter(news_items, greeting_content=""):
    """HTML 뉴스레터 생성"""
    category_names = {
        'society': '사회',
        'economy': '경제',
        'culture': '문화'
    }
    
    html_template = f"""
    <!DOCTYPE html>
    <html lang="ko">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>법률행정 뉴스레터</title>
        <style>
            body {{
                font-family: 'Malgun Gothic', -apple-system, BlinkMacSystemFont, sans-serif;
                margin: 0;
                padding: 20px;
                background-color: #f8f9fa;
                line-height: 1.6;
            }}
            .container {{
                max-width: 600px;
                margin: 0 auto;
                background-color: white;
                border-radius: 12px;
                box-shadow: 0 4px 20px rgba(0,0,0,0.1);
                overflow: hidden;
            }}
            .header {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                text-align: center;
                padding: 40px 30px;
            }}
            .header h1 {{
                margin: 0 0 10px 0;
                font-size: 28px;
                font-weight: 700;
                letter-spacing: -0.5px;
            }}
            .header p {{
                margin: 0;
                font-size: 18px;
                opacity: 0.95;
                font-weight: 300;
            }}
            .greeting-section {{
                padding: 0;
                background-color: white;
            }}
            .content {{
                padding: 30px;
            }}
            .default-greeting {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 25px;
                border-radius: 10px;
                margin: 20px 0;
                text-align: center;
            }}
            .default-greeting h3 {{
                margin: 0 0 15px 0;
                font-size: 18px;
                font-weight: 600;
            }}
            .default-greeting p {{
                margin: 0;
                font-size: 16px;
                line-height: 1.6;
                opacity: 0.95;
            }}
            .news-section {{
                margin-top: 30px;
            }}
            .section-title {{
                color: #2c3e50;
                font-size: 22px;
                font-weight: 700;
                border-bottom: 3px solid #667eea;
                padding-bottom: 10px;
                margin-bottom: 25px;
                display: flex;
                align-items: center;
            }}
            .section-title::before {{
                content: "📰";
                margin-right: 10px;
                font-size: 24px;
            }}
            .news-item {{
                border: 1px solid #e9ecef;
                border-radius: 12px;
                padding: 20px;
                margin-bottom: 16px;
                background: linear-gradient(145deg, #ffffff 0%, #f8f9fa 100%);
                transition: all 0.3s ease;
                position: relative;
            }}
            .news-item:hover {{
                transform: translateY(-2px);
                box-shadow: 0 8px 25px rgba(0,0,0,0.1);
            }}
            .news-category {{
                display: inline-block;
                padding: 4px 12px;
                border-radius: 20px;
                font-size: 12px;
                font-weight: 600;
                margin-bottom: 8px;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }}
            .category-society {{
                background-color: #e3f2fd;
                color: #1976d2;
            }}
            .category-economy {{
                background-color: #f3e5f5;
                color: #7b1fa2;
            }}
            .category-culture {{
                background-color: #e8f5e8;
                color: #388e3c;
            }}
            .news-number {{
                position: absolute;
                top: -8px;
                left: 20px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                width: 28px;
                height: 28px;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                font-weight: 700;
                font-size: 14px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.2);
            }}
            .news-title {{
                color: #2c3e50;
                text-decoration: none;
                font-weight: 600;
                font-size: 16px;
                display: block;
                margin: 8px 0 8px 0;
                line-height: 1.4;
                transition: color 0.3s ease;
            }}
            .news-title:hover {{
                color: #667eea;
                text-decoration: none;
            }}
            .news-date {{
                color: #6c757d;
                font-size: 13px;
                font-weight: 500;
                display: flex;
                align-items: center;
            }}
            .news-date::before {{
                content: "📅";
                margin-right: 6px;
            }}
            .footer {{
                background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
                padding: 30px;
                text-align: center;
                color: #6c757d;
                border-top: 1px solid #dee2e6;
            }}
            .footer p {{
                margin: 8px 0;
                font-size: 14px;
            }}
            .footer .company-name {{
                font-weight: 700;
                color: #495057;
                font-size: 16px;
            }}
            .divider {{
                height: 2px;
                background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
                margin: 30px 0;
                border-radius: 1px;
            }}
            @media (max-width: 600px) {{
                .container {{ margin: 10px; }}
                .header, .content {{ padding: 20px; }}
                .news-item {{ padding: 15px; }}
                .header h1 {{ font-size: 24px; }}
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>신뢰할 수 있는</h1>
                <p>법률행정 파트너</p>
            </div>
            
            <div class="greeting-section">
                {greeting_content if greeting_content else generate_default_greeting()}
            </div>
            
            <div class="content">
                <div class="divider"></div>
                
                <div class="news-section">
                    <h3 class="section-title">주간 법률 및 사회 동향</h3>
                    {generate_news_items_html(news_items)}
                </div>
            </div>
            
            <div class="footer">
                <p class="company-name">법률사무소</p>
                <p>📧 본 메일은 법률정보 제공을 위해 발송되었습니다.</p>
                <p>📞 더 자세한 상담이 필요하시면 언제든 연락주세요.</p>
                <p>© 2024 법률사무소. All rights reserved.</p>
            </div>
        </div>
    </body>
    </html>
    """
    return html_template

def generate_default_greeting():
    """기본 인사말 생성"""
    now = datetime.now()
    date_str = now.strftime("%Y년 %m월 %d일")
    
    return f"""
    <div class="default-greeting">
        <h3>{date_str}</h3>
        <p>안녕하세요. 귀하의 법률사무소에서 정성껏 준비한 주간 소식을 전해드립니다.<br>
        항상 여러분과 함께하는 믿음직한 법률 파트너가 되겠습니다.</p>
    </div>
    """

def generate_news_items_html(news_items):
    """뉴스 아이템 HTML 생성"""
    if not news_items:
        return '<p style="text-align: center; color: #6c757d; font-style: italic;">등록된 뉴스가 없습니다.</p>'
    
    category_names = {
        'society': '사회',
        'economy': '경제',
        'culture': '문화'
    }
    
    html = ""
    for i, item in enumerate(news_items, 1):
        category = item.get('category', 'society')
        category_korean = category_names.get(category, '사회')
        
        html += f"""
        <div class="news-item">
            <div class="news-number">{i}</div>
            <div class="news-category category-{category}">{category_korean}</div>
            <a href="{item['url']}" class="news-title" target="_blank">{item['title']}</a>
            <div class="news-date">{item['date']}</div>
        </div>
        """
    return html

# === 발송 함수들 ===
def send_newsletter_with_progress(recipients, subject, html_content, smtp_settings, progress_callback=None):
    """진행 상황을 표시하는 뉴스레터 발송 함수"""
    total_recipients = len(recipients)
    sent_count = 0
    failed_emails = []
    
    try:
        if progress_callback:
            progress_callback(0, f"📡 SMTP 서버에 연결 중... ({smtp_settings['server']})")
        
        server = smtplib.SMTP(smtp_settings['server'], smtp_settings['port'])
        server.starttls()
        server.login(smtp_settings['email'], smtp_settings['password'])
        
        if progress_callback:
            progress_callback(5, f"✅ SMTP 서버 연결 완료")
        
        for i, recipient in enumerate(recipients):
            try:
                progress = 5 + int((i / total_recipients) * 90)
                
                if progress_callback:
                    progress_callback(progress, f"📧 발송 중... ({i+1}/{total_recipients}) {recipient}")
                
                msg = MIMEMultipart('alternative')
                msg['From'] = smtp_settings['email']
                msg['To'] = recipient
                msg['Subject'] = subject
                
                html_part = MIMEText(html_content, 'html', 'utf-8')
                msg.attach(html_part)
                
                server.send_message(msg)
                sent_count += 1
                
                if i > 0 and i % 50 == 0:
                    if progress_callback:
                        progress_callback(progress, f"⏳ 서버 부하 방지를 위해 잠시 대기 중... ({i+1}/{total_recipients})")
                    time.sleep(10)
                else:
                    time.sleep(0.5)
                
            except Exception as e:
                failed_emails.append(f"{recipient}: {str(e)}")
                if progress_callback:
                    progress_callback(progress, f"❌ 실패: {recipient} - {str(e)[:50]}...")
        
        if progress_callback:
            progress_callback(95, "🔄 SMTP 연결 종료 중...")
        
        server.quit()
        
        if progress_callback:
            progress_callback(100, f"✅ 발송 완료! 성공: {sent_count}명, 실패: {len(failed_emails)}명")
        
        return sent_count, failed_emails
    
    except Exception as e:
        if progress_callback:
            progress_callback(0, f"❌ SMTP 연결 오류: {str(e)}")
        return 0, [f"SMTP 연결 오류: {str(e)}"]

def display_newsletter_editor():
    """뉴스레터 편집기 (발송 전 최종 편집)"""
    st.markdown("""
    <div class="section-card">
        <div class="section-header">
            <span class="section-icon">📝</span>
            <h3 class="section-title">발송 전 최종 편집</h3>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # 제목 편집
    st.subheader("📧 이메일 제목")
    current_subject = st.session_state.get('email_subject', f"[법률사무소] 법률 뉴스레터 - {datetime.now().strftime('%Y년 %m월 %d일')}")
    edited_subject = st.text_input(
        "이메일 제목을 확인하고 수정하세요",
        value=current_subject,
        key="final_subject_edit"
    )
    st.session_state['email_subject'] = edited_subject
    
    # 인사말 편집
    st.subheader("🎉 인사말")
    if st.session_state.newsletter_data.get('auto_greeting', True):
        custom_message = st.text_area(
            "자동 생성된 인사말에 추가할 메시지",
            value=st.session_state.newsletter_data.get('custom_greeting', ''),
            height=100,
            key="final_greeting_edit"
        )
        st.session_state.newsletter_data['custom_greeting'] = custom_message
        
        if st.button("🔄 인사말 미리보기 새로고침"):
            greeting_html = st.session_state.greeting_generator.generate_complete_greeting(
                custom_message=custom_message,
                include_image=True
            )
            st.components.v1.html(greeting_html, height=350)
    else:
        custom_greeting = st.text_area(
            "사용자 정의 인사말",
            value=st.session_state.newsletter_data.get('custom_greeting', ''),
            height=120,
            key="final_custom_greeting_edit"
        )
        st.session_state.newsletter_data['custom_greeting'] = custom_greeting
    
    # 뉴스 항목 편집
    st.subheader("📰 뉴스 항목 최종 확인")
    
    if st.session_state.newsletter_data['news_items']:
        for i, item in enumerate(st.session_state.newsletter_data['news_items']):
            with st.expander(f"{i+1}. {item['title'][:50]}...", expanded=False):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    new_title = st.text_input(
                        "제목", 
                        value=item['title'],
                        key=f"edit_title_{i}"
                    )
                    
                    new_url = st.text_input(
                        "URL",
                        value=item['url'],
                        key=f"edit_url_{i}"
                    )
                    
                    if new_title != item['title'] or new_url != item['url']:
                        st.session_state.newsletter_data['news_items'][i]['title'] = new_title
                        st.session_state.newsletter_data['news_items'][i]['url'] = new_url
                
                with col2:
                    category_korean = {"society": "사회", "economy": "경제", "culture": "문화"}
                    st.write(f"**카테고리:** {category_korean.get(item.get('category', 'society'), '사회')}")
                    st.write(f"**날짜:** {item['date']}")
                    
                    if st.button("🗑️ 삭제", key=f"delete_final_{i}"):
                        st.session_state.newsletter_data['news_items'].pop(i)
                        st.rerun()
    
    # 수신자 선택
    st.subheader("👥 수신자 선택")
    
    if not st.session_state.newsletter_data['address_book'].empty:
        df = st.session_state.newsletter_data['address_book']
        
        col1, col2 = st.columns(2)
        
        with col1:
            categories = df['분류'].unique() if '분류' in df.columns else ['전체']
            selected_categories = st.multiselect(
                "발송할 고객 분류 선택",
                categories,
                default=categories,
                key="final_categories"
            )
        
        with col2:
            if st.button("🎯 전체 선택"):
                st.session_state['final_categories'] = list(categories)
                st.experimental_rerun()
        
        if selected_categories:
            filtered_df = df[df['분류'].isin(selected_categories)] if '분류' in df.columns else df
            
            st.write(f"📊 **선택된 수신자: {len(filtered_df)}명**")
            
            preview_df = filtered_df[['이름', '이메일', '분류']].head(10)
            st.dataframe(preview_df, use_container_width=True)
            
            if len(filtered_df) > 10:
                st.info(f"+ 추가 {len(filtered_df) - 10}명이 더 있습니다.")
            
            return filtered_df['이메일'].tolist(), edited_subject
        else:
            st.warning("발송할 고객 분류를 선택해주세요.")
            return [], edited_subject
    else:
        st.error("등록된 주소록이 없습니다.")
        return [], edited_subject

# === 메인 애플리케이션 ===
def main():
    """메인 함수"""
    
    # 사이드바 메뉴
    menu = st.sidebar.selectbox(
        "메뉴 선택",
        ["🏠 홈", "📝 뉴스레터 작성", "📧 이메일 설정", "👥 주소록 관리", "📤 발송하기"]
    )
    
    # 홈 메뉴
    if menu == "🏠 홈":
        st.markdown('<div class="main-header"><h1>📧 법률사무소 뉴스레터 발송 시스템</h1><p>간편하고 전문적인 뉴스레터 관리 솔루션</p></div>', 
                    unsafe_allow_html=True)
        
        display_progress_steps("home")
        
        st.markdown("""
        <div class="section-card">
            <div class="section-header">
                <span class="section-icon">📊</span>
                <h3 class="section-title">현재 상태</h3>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        display_status_summary()
        
        email_configured = bool(st.session_state.newsletter_data['email_settings'])
        has_addresses = not st.session_state.newsletter_data['address_book'].empty
        has_content = bool(st.session_state.newsletter_data['news_items'])
        
        if not email_configured:
            show_alert("🔧 먼저 이메일 설정을 완료해주세요. 사이드바에서 '📧 이메일 설정' 메뉴를 클릭하세요.", "warning")
        elif not has_addresses:
            show_alert("📋 이제 고객 주소록을 등록해주세요.", "info")
        elif not has_content:
            show_alert("📝 이제 뉴스레터 내용을 작성해주세요.", "info")
        else:
            show_alert("🎉 모든 준비가 완료되었습니다! 이제 뉴스레터를 발송할 수 있습니다.", "success")
    
    # 이메일 설정 메뉴
    elif menu == "📧 이메일 설정":
        st.markdown('<div class="main-header"><h1>📧 이메일 설정</h1><p>안전하고 안정적인 이메일 발송을 위한 SMTP 설정</p></div>', 
                    unsafe_allow_html=True)
        
        display_progress_steps("settings")
        
        saved_settings = load_persistent_settings()
        is_configured = bool(saved_settings)
        
        if is_configured:
            show_alert(f"✅ 이메일 설정이 완료되었습니다. (발신자: {saved_settings.get('email', '설정됨')})", "success")
        else:
            show_alert("⚙️ 이메일 설정을 완료해주세요. Gmail 사용을 권장합니다.", "info")
        
        with st.form("gmail_settings"):
            col1, col2 = st.columns(2)
            
            with col1:
                gmail_address = st.text_input(
                    "Gmail 주소",
                    value=saved_settings.get('email', ''),
                    placeholder="your-email@gmail.com"
                )
            
            with col2:
                app_password = st.text_input(
                    "앱 비밀번호 (16자리)",
                    type="password",
                    placeholder="abcd efgh ijkl mnop"
                )
            
            st.info("✅ SMTP 서버와 포트는 자동으로 설정됩니다 (smtp.gmail.com:587)")
            
            if st.form_submit_button("💾 Gmail 설정 저장 및 테스트", type="primary", use_container_width=True):
                if gmail_address and app_password:
                    if validate_email(gmail_address) and gmail_address.endswith('@gmail.com'):
                        settings = {
                            'server': 'smtp.gmail.com',
                            'port': 587,
                            'email': gmail_address,
                            'password': app_password
                        }
                        
                        with st.spinner("Gmail 연결을 테스트하고 있습니다..."):
                            try:
                                server = smtplib.SMTP('smtp.gmail.com', 587)
                                server.starttls()
                                server.login(gmail_address, app_password)
                                server.quit()
                                
                                st.session_state.newsletter_data['email_settings'] = settings
                                save_persistent_settings(settings)
                                show_alert("🎉 Gmail 설정이 성공적으로 완료되었습니다!", "success")
                                
                            except Exception as e:
                                show_alert(f"❌ Gmail 연결 테스트 실패: {str(e)}", "error")
                    else:
                        show_alert("올바른 Gmail 주소를 입력해주세요.", "error")
                else:
                    show_alert("Gmail 주소와 앱 비밀번호를 모두 입력해주세요.", "error")
    
    # 주소록 관리 메뉴
    elif menu == "👥 주소록 관리":
        st.markdown('<div class="main-header"><h1>👥 주소록 관리</h1><p>고객 정보를 체계적으로 관리하세요</p></div>', 
                    unsafe_allow_html=True)
        
        display_progress_steps("addresses")
        
        uploaded_file = st.file_uploader(
            "CSV 파일 업로드 (이름, 이메일, 분류, 메모 열 포함)",
            type=['csv']
        )
        
        if uploaded_file:
            try:
                df = pd.read_csv(uploaded_file, encoding='utf-8')
                
                required_columns = ['이름', '이메일']
                missing_columns = [col for col in required_columns if col not in df.columns]
                
                if missing_columns:
                    st.error(f"필수 컬럼이 누락되었습니다: {', '.join(missing_columns)}")
                else:
                    if '분류' not in df.columns:
                        df['분류'] = '일반고객'
                    if '메모' not in df.columns:
                        df['메모'] = ''
                    
                    st.session_state.newsletter_data['address_book'] = df
                    save_address_book(df)
                    st.success(f"주소록이 성공적으로 업로드되었습니다! ({len(df)}명)")
            except Exception as e:
                st.error(f"파일 업로드 중 오류가 발생했습니다: {str(e)}")
        
        with st.expander("➕ 수동으로 연락처 추가"):
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("이름*", key="add_name")
                email = st.text_input("이메일*", key="add_email")
            with col2:
                category = st.selectbox("분류", 
                                      ["일반고객", "VIP고객", "기업고객", "개인고객", "잠재고객"], 
                                      key="add_category")
                memo = st.text_input("메모", key="add_memo")
            
            if st.button("➕ 연락처 추가"):
                if name and email and validate_email(email):
                    new_contact = pd.DataFrame({
                        '이름': [name], 
                        '이메일': [email],
                        '분류': [category],
                        '메모': [memo]
                    })
                    
                    if st.session_state.newsletter_data['address_book'].empty:
                        st.session_state.newsletter_data['address_book'] = new_contact
                    else:
                        st.session_state.newsletter_data['address_book'] = pd.concat([
                            st.session_state.newsletter_data['address_book'], 
                            new_contact
                        ], ignore_index=True)
                    
                    save_address_book(st.session_state.newsletter_data['address_book'])
                    st.success(f"'{name}' 연락처가 추가되었습니다!")
                    st.experimental_rerun()
                else:
                    st.error("올바른 이름과 이메일을 입력해주세요.")
        
        if not st.session_state.newsletter_data['address_book'].empty:
            st.subheader("📋 현재 주소록")
            st.dataframe(st.session_state.newsletter_data['address_book'], use_container_width=True)
            
            csv = st.session_state.newsletter_data['address_book'].to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                label="📥 주소록 다운로드 (CSV)",
                data=csv,
                file_name=f"address_book_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
    
    # 뉴스레터 작성 메뉴
    elif menu == "📝 뉴스레터 작성":
        st.markdown('<div class="main-header"><h1>📝 뉴스레터 작성</h1><p>따뜻한 감성의 법률 뉴스레터를 만들어보세요</p></div>', 
                    unsafe_allow_html=True)
        
        display_progress_steps("content")
        
        auto_greeting = st.checkbox(
            "자동 인사말 생성", 
            value=st.session_state.newsletter_data.get('auto_greeting', True)
        )
        st.session_state.newsletter_data['auto_greeting'] = auto_greeting
        
        custom_greeting = st.text_area(
            "사용자 정의 메시지",
            value=st.session_state.newsletter_data.get('custom_greeting', ''),
            placeholder="고객에게 전달하고 싶은 메시지를 입력하세요...",
            height=100
        )
        st.session_state.newsletter_data['custom_greeting'] = custom_greeting
        
        st.subheader("📰 뉴스 수집")
        
        col1, col2 = st.columns([2, 1])
        with col1:
            news_count = st.selectbox("수집할 뉴스 개수", [3, 5, 7, 10], index=1)
        with col2:
            if st.button("🔄 자동 뉴스 수집", type="primary"):
                with st.spinner("최신 뉴스를 수집하고 있습니다..."):
                    try:
                        collected_news = st.session_state.news_collector.collect_weekly_news(news_count)
                        st.session_state.newsletter_data['news_items'] = collected_news
                        save_news_cache(collected_news)
                        st.success(f"✅ {len(collected_news)}개의 뉴스를 수집했습니다!")
                        st.experimental_rerun()
                    except Exception as e:
                        st.error(f"뉴스 수집 중 오류가 발생했습니다: {e}")
        
        with st.expander("➕ 수동으로 뉴스 추가"):
            col1, col2 = st.columns([3, 1])
            with col1:
                news_title = st.text_input("뉴스 제목")
                news_url = st.text_input("뉴스 URL")
            with col2:
                news_category = st.selectbox("카테고리", ["society", "economy", "culture"], 
                                           format_func=lambda x: {"society": "사회", "economy": "경제", "culture": "문화"}[x])
                news_date = st.date_input("날짜", datetime.now())
                
            if st.button("➕ 뉴스 추가"):
                if news_title and news_url:
                    new_item = {
                        'title': news_title,
                        'url': news_url,
                        'date': news_date.strftime('%Y.%m.%d'),
                        'category': news_category
                    }
                    st.session_state.newsletter_data['news_items'].append(new_item)
                    st.success("뉴스 항목이 추가되었습니다!")
                    st.experimental_rerun()
                else:
                    st.error("제목과 URL을 모두 입력해주세요.")
        
        if st.session_state.newsletter_data['news_items']:
            st.subheader(f"📋 현재 뉴스 목록 ({len(st.session_state.newsletter_data['news_items'])}개)")
            
            for i, item in enumerate(st.session_state.newsletter_data['news_items']):
                category_korean = {"society": "사회", "economy": "경제", "culture": "문화"}
                
                col1, col2 = st.columns([5, 1])
                with col1:
                    st.write(f"**{i+1}. {item['title']}** ({category_korean.get(item.get('category', 'society'), '사회')} | {item['date']})")
                    st.write(f"🔗 {item['url']}")
                with col2:
                    if st.button("🗑️", key=f"delete_{i}"):
                        st.session_state.newsletter_data['news_items'].pop(i)
                        st.experimental_rerun()
        
        if st.session_state.newsletter_data['news_items']:
            if st.button("👀 전체 뉴스레터 미리보기", type="secondary"):
                if auto_greeting:
                    greeting_content = st.session_state.greeting_generator.generate_complete_greeting(
                        custom_message=custom_greeting,
                        include_image=True
                    )
                else:
                    greeting_content = f'<div style="padding: 20px; background-color: #f8f9fa; border-radius: 8px;">{custom_greeting}</div>' if custom_greeting else ""
                
                html_content = create_html_newsletter(
                    st.session_state.newsletter_data['news_items'],
                    greeting_content
                )
                
                st.components.v1.html(html_content, height=800, scrolling=True)
    
    # 발송하기 메뉴
    elif menu == "📤 발송하기":
        st.markdown('<div class="main-header"><h1>🚀 뉴스레터 발송</h1><p>단계별로 안전하게 발송하세요</p></div>', 
                    unsafe_allow_html=True)
        
        display_progress_steps("send")
        
        email_configured = bool(st.session_state.newsletter_data['email_settings'])
        has_news = bool(st.session_state.newsletter_data['news_items'])
        has_addresses = not st.session_state.newsletter_data['address_book'].empty
        
        all_ready = email_configured and has_news and has_addresses
        
        if not all_ready:
            st.error("❌ 발송하기 전에 모든 설정을 완료해주세요.")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if email_configured:
                    st.success("✅ 이메일 설정 완료")
                else:
                    st.error("❌ 이메일 설정 필요")
            
            with col2:
                if has_addresses:
                    st.success(f"✅ 주소록 준비 완료 ({len(st.session_state.newsletter_data['address_book'])}명)")
                else:
                    st.error("❌ 주소록 등록 필요")
            
            with col3:
                if has_news:
                    st.success(f"✅ 뉴스레터 준비 완료 ({len(st.session_state.newsletter_data['news_items'])}개)")
                else:
                    st.error("❌ 뉴스레터 작성 필요")
        
        else:
            show_alert("🎉 모든 준비가 완료되었습니다! 발송을 진행할 수 있습니다.", "success")
            
            tab1, tab2 = st.tabs(["📝 내용 편집", "👀 미리보기"])
            
            with tab1:
                recipient_emails, final_subject = display_newsletter_editor()
            
            with tab2:
                st.markdown("### 📱 실제 발송될 뉴스레터 미리보기")
                
                if st.button("🔄 미리보기 새로고침", key="refresh_preview"):
                    if st.session_state.newsletter_data.get('auto_greeting', True):
                        greeting_content = st.session_state.greeting_generator.generate_complete_greeting(
                            custom_message=st.session_state.newsletter_data.get('custom_greeting', ''),
                            include_image=True
                        )
                    else:
                        greeting_content = f'<div style="padding: 20px; background-color: #f8f9fa; border-radius: 8px;">{st.session_state.newsletter_data.get("custom_greeting", "")}</div>'
                    
                    html_content = create_html_newsletter(
                        st.session_state.newsletter_data['news_items'],
                        greeting_content
                    )
                    
                    st.components.v1.html(html_content, height=800, scrolling=True)
            
            # 발송 실행
            if 'recipient_emails' in locals() and recipient_emails and 'final_subject' in locals() and final_subject:
                st.markdown("### 🚀 최종 발송")
                
                st.markdown(f"""
                **🔍 발송 전 최종 확인:**
                - **제목:** {final_subject}
                - **수신자:** {len(recipient_emails)}명
                - **뉴스 항목:** {len(st.session_state.newsletter_data['news_items'])}개
                """)
                
                col1, col2 = st.columns([1, 1])
                
                with col1:
                    if st.button("🚀 지금 발송하기", type="primary", key="execute_send", use_container_width=True):
                        if st.checkbox("위 내용을 확인했으며 발송을 진행합니다", key="confirm_send"):
                            
                            send_start_time = datetime.now()
                            
                            st.markdown("### 📊 발송 진행 상황")
                            
                            progress_bar = st.progress(0)
                            status_container = st.empty()
                            log_container = st.empty()
                            
                            if 'current_send_log' not in st.session_state:
                                st.session_state.current_send_log = []
                            
                            st.session_state.current_send_log = []
                            
                            def update_send_progress(progress, message):
                                progress_bar.progress(progress)
                                status_container.info(f"🔄 {message}")
                                
                                timestamp = datetime.now().strftime('%H:%M:%S')
                                st.session_state.current_send_log.append(f"[{timestamp}] {message}")
                                
                                recent_logs = st.session_state.current_send_log[-5:]
                                log_text = "\n".join(recent_logs)
                                
                                with log_container.container():
                                    st.text_area(
                                        "실시간 발송 로그", 
                                        value=log_text, 
                                        height=120, 
                                        key=f"send_log_{len(st.session_state.current_send_log)}"
                                    )
                            
                            try:
                                update_send_progress(1, "📝 뉴스레터 내용을 생성하고 있습니다...")
                                
                                if st.session_state.newsletter_data.get('auto_greeting', True):
                                    greeting_content = st.session_state.greeting_generator.generate_complete_greeting(
                                        custom_message=st.session_state.newsletter_data.get('custom_greeting', ''),
                                        include_image=True
                                    )
                                else:
                                    greeting_content = f'<div style="padding: 20px; background-color: #f8f9fa; border-radius: 8px;">{st.session_state.newsletter_data.get("custom_greeting", "")}</div>'
                                
                                html_content = create_html_newsletter(
                                    st.session_state.newsletter_data['news_items'],
                                    greeting_content
                                )
                                
                                update_send_progress(3, "✅ 뉴스레터 내용 생성 완료")
                                
                                update_send_progress(5, f"📧 {len(recipient_emails)}명에게 발송을 시작합니다...")
                                
                                sent_count, failed_emails = send_newsletter_with_progress(
                                    recipient_emails,
                                    final_subject,
                                    html_content,
                                    st.session_state.newsletter_data['email_settings'],
                                    progress_callback=update_send_progress
                                )
                                
                                progress_bar.progress(100)
                                status_container.success("🎉 뉴스레터 발송이 완료되었습니다!")
                                
                                st.markdown("### 📊 발송 결과")
                                
                                if sent_count > 0:
                                    st.success(f"✅ 성공! {sent_count}명에게 뉴스레터가 발송되었습니다.")
                                    
                                    success_rate = (sent_count / len(recipient_emails)) * 100
                                    st.metric(
                                        label="발송 성공률",
                                        value=f"{success_rate:.1f}%",
                                        delta=f"{sent_count}/{len(recipient_emails)}"
                                    )
                                
                                if failed_emails:
                                    st.error(f"⚠️ {len(failed_emails)}건의 발송이 실패했습니다.")
                                    
                                    with st.expander("🔍 실패한 발송 상세 보기"):
                                        for i, error in enumerate(failed_emails[:10]):
                                            st.write(f"{i+1}. {error}")
                                        
                                        if len(failed_emails) > 10:
                                            st.write(f"... 외 {len(failed_emails)-10}건 더")
                                
                                if st.button("🏠 홈으로 돌아가기", key="go_home"):
                                    st.experimental_rerun()
                                    
                            except Exception as e:
                                progress_bar.progress(0)
                                status_container.error(f"❌ 발송 중 오류가 발생했습니다: {str(e)}")
                                st.error(f"오류 내용: {str(e)}")
                        
                        else:
                            show_alert("발송을 진행하려면 확인 체크박스를 선택해주세요.", "warning")
                
                with col2:
                    if st.button("📧 테스트 발송", key="test_send", use_container_width=True):
                        if st.session_state.newsletter_data['email_settings']:
                            test_email = st.session_state.newsletter_data['email_settings']['email']
                            
                            with st.spinner("테스트 발송 중..."):
                                try:
                                    if st.session_state.newsletter_data.get('auto_greeting', True):
                                        greeting_content = st.session_state.greeting_generator.generate_complete_greeting(
                                            custom_message="이것은 테스트 발송입니다.",
                                            include_image=True
                                        )
                                    else:
                                        greeting_content = f'<div style="padding: 20px; background-color: #f8f9fa; border-radius: 8px;">테스트 발송: {st.session_state.newsletter_data.get("custom_greeting", "")}</div>'
                                    
                                    html_content = create_html_newsletter(
                                        st.session_state.newsletter_data['news_items'],
                                        greeting_content
                                    )
                                    
                                    test_subject = f"[테스트] {final_subject}"
                                    sent_count, failed_emails = send_newsletter_with_progress(
                                        [test_email],
                                        test_subject,
                                        html_content,
                                        st.session_state.newsletter_data['email_settings']
                                    )
                                    
                                    if sent_count > 0:
                                        st.success(f"✅ 테스트 메일이 {test_email}로 발송되었습니다!")
                                    else:
                                        st.error("❌ 테스트 발송에 실패했습니다.")
                                        if failed_emails:
                                            st.error(f"오류: {failed_emails[0]}")
                                            
                                except Exception as e:
                                    st.error(f"❌ 테스트 발송 중 오류: {str(e)}")
                        else:
                            st.error("이메일 설정을 먼저 완료해주세요.")

if __name__ == "__main__":
    main()