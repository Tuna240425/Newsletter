import streamlit as st
import pandas as pd
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os
from datetime import datetime
import json
import re

# 페이지 설정
st.set_page_config(
    page_title="법률사무소 뉴스레터 발송 시스템",
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
.newsletter-preview {
    border: 2px solid #e0e0e0;
    border-radius: 10px;
    padding: 20px;
    background-color: #f9f9f9;
    margin: 20px 0;
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
</style>
""", unsafe_allow_html=True)

# 세션 상태 초기화
if 'newsletter_data' not in st.session_state:
    st.session_state.newsletter_data = {
        'news_items': [],
        'email_settings': {},
        'address_book': pd.DataFrame()
    }

def load_settings():
    """설정 파일 로드"""
    if os.path.exists('email_settings.json'):
        with open('email_settings.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_settings(settings):
    """설정 파일 저장"""
    with open('email_settings.json', 'w', encoding='utf-8') as f:
        json.dump(settings, f, ensure_ascii=False, indent=2)

def validate_email(email):
    """이메일 주소 유효성 검사"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def create_html_newsletter(news_items, custom_message=""):
    """HTML 뉴스레터 생성"""
    html_template = f"""
    <!DOCTYPE html>
    <html lang="ko">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>법률행정 뉴스레터</title>
        <style>
            body {{
                font-family: 'Malgun Gothic', sans-serif;
                margin: 0;
                padding: 20px;
                background-color: #f5f5f5;
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
                height: 250px;
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
            }}
            .news-section {{
                margin-top: 30px;
            }}
            .news-item {{
                border-bottom: 1px solid #eee;
                padding: 15px 0;
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
            }}
            .news-title:hover {{
                color: #764ba2;
            }}
            .news-date {{
                color: #888;
                font-size: 12px;
            }}
            .footer {{
                background-color: #f8f9fa;
                padding: 20px;
                text-align: center;
                color: #666;
                font-size: 12px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>신뢰할 수 있는</h1>
                <p>법률행정 파트너</p>
            </div>
            
            <div class="hero-image">
                📧 법률 뉴스레터
            </div>
            
            <div class="content">
                <div class="greeting">
                    안녕하세요, 귀하의 법률사무소 소식을 전해 드립니다.<br>
                    항상 여러분과 함께하는 믿음직한 법률 파트너가 되겠습니다.
                </div>
                
                {f'<div class="custom-message">{custom_message}</div>' if custom_message else ''}
                
                <div class="news-section">
                    <h3 style="color: #333; border-bottom: 2px solid #667eea; padding-bottom: 10px;">최신 법률 소식</h3>
                    
                    {generate_news_items_html(news_items)}
                </div>
            </div>
            
            <div class="footer">
                <p>본 메일은 법률정보 제공을 위해 발송되었습니다.</p>
                <p>더 자세한 상담이 필요하시면 언제든 연락주세요.</p>
                <p>© 2024 법률사무소. All rights reserved.</p>
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
            <div class="news-date">{item['date']}</div>
        </div>
        """
    return html

def send_newsletter(recipients, subject, html_content, smtp_settings):
    """뉴스레터 발송"""
    try:
        server = smtplib.SMTP(smtp_settings['server'], smtp_settings['port'])
        server.starttls()
        server.login(smtp_settings['email'], smtp_settings['password'])
        
        sent_count = 0
        failed_emails = []
        
        for recipient in recipients:
            try:
                msg = MIMEMultipart('alternative')
                msg['From'] = smtp_settings['email']
                msg['To'] = recipient
                msg['Subject'] = subject
                
                html_part = MIMEText(html_content, 'html', 'utf-8')
                msg.attach(html_part)
                
                server.send_message(msg)
                sent_count += 1
            except Exception as e:
                failed_emails.append(f"{recipient}: {str(e)}")
        
        server.quit()
        return sent_count, failed_emails
    
    except Exception as e:
        return 0, [f"SMTP 연결 오류: {str(e)}"]

# 메인 앱
def main():
    st.markdown('<div class="main-header"><h1>📧 법률사무소 뉴스레터 발송 시스템</h1></div>', 
                unsafe_allow_html=True)
    
    # 사이드바 메뉴
    menu = st.sidebar.selectbox(
        "메뉴 선택",
        ["🏠 홈", "📝 뉴스레터 작성", "📧 이메일 설정", "👥 주소록 관리", "📤 발송하기"]
    )
    
    if menu == "🏠 홈":
        st.header("환영합니다! 👋")
        st.write("""
        이 시스템을 사용하여 손쉽게 뉴스레터를 작성하고 발송할 수 있습니다.
        
        **사용 방법:**
        1. **이메일 설정**: SMTP 설정을 입력하세요
        2. **주소록 관리**: 수신자 명단을 관리하세요
        3. **뉴스레터 작성**: 뉴스 항목을 추가하고 내용을 작성하세요
        4. **발송하기**: 작성된 뉴스레터를 발송하세요
        """)
        
        # 통계 정보
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("📰 뉴스 항목", len(st.session_state.newsletter_data['news_items']))
        with col2:
            st.metric("👥 주소록", len(st.session_state.newsletter_data['address_book']))
        with col3:
            smtp_configured = bool(st.session_state.newsletter_data['email_settings'])
            st.metric("📧 이메일 설정", "✅" if smtp_configured else "❌")
    
    elif menu == "📝 뉴스레터 작성":
        st.header("뉴스레터 작성")
        
        # 사용자 정의 메시지
        custom_message = st.text_area(
            "사용자 정의 메시지 (선택사항)",
            placeholder="고객에게 전달하고 싶은 특별한 메시지를 입력하세요...",
            height=100
        )
        
        st.subheader("뉴스 항목 추가")
        
        col1, col2 = st.columns([3, 1])
        with col1:
            news_title = st.text_input("뉴스 제목")
            news_url = st.text_input("뉴스 URL")
        with col2:
            news_date = st.date_input("날짜", datetime.now())
            if st.button("➕ 추가"):
                if news_title and news_url:
                    new_item = {
                        'title': news_title,
                        'url': news_url,
                        'date': news_date.strftime('%Y.%m.%d')
                    }
                    st.session_state.newsletter_data['news_items'].append(new_item)
                    st.success("뉴스 항목이 추가되었습니다!")
                    st.rerun()
                else:
                    st.error("제목과 URL을 모두 입력해주세요.")
        
        # 현재 뉴스 목록
        if st.session_state.newsletter_data['news_items']:
            st.subheader("현재 뉴스 목록")
            for i, item in enumerate(st.session_state.newsletter_data['news_items']):
                col1, col2, col3 = st.columns([0.5, 3, 0.5])
                with col1:
                    st.write(f"{i+1}.")
                with col2:
                    st.write(f"**{item['title']}** ({item['date']})")
                    st.write(f"🔗 {item['url']}")
                with col3:
                    if st.button("🗑️", key=f"delete_{i}"):
                        st.session_state.newsletter_data['news_items'].pop(i)
                        st.rerun()
        
        # 미리보기
        if st.session_state.newsletter_data['news_items']:
            if st.button("👀 미리보기"):
                html_content = create_html_newsletter(
                    st.session_state.newsletter_data['news_items'],
                    custom_message
                )
                st.markdown('<div class="newsletter-preview">', unsafe_allow_html=True)
                st.components.v1.html(html_content, height=800, scrolling=True)
                st.markdown('</div>', unsafe_allow_html=True)
    
    elif menu == "📧 이메일 설정":
        st.header("이메일 SMTP 설정")
        
        # 기존 설정 로드
        saved_settings = load_settings()
        
        with st.form("smtp_settings"):
            st.subheader("SMTP 서버 정보")
            
            smtp_server = st.text_input(
                "SMTP 서버", 
                value=saved_settings.get('server', 'smtp.gmail.com'),
                placeholder="예: smtp.gmail.com"
            )
            smtp_port = st.number_input(
                "포트", 
                value=saved_settings.get('port', 587),
                min_value=1, max_value=65535
            )
            
            sender_email = st.text_input(
                "발신자 이메일", 
                value=saved_settings.get('email', ''),
                placeholder="your-email@gmail.com"
            )
            sender_password = st.text_input(
                "비밀번호 (앱 비밀번호)", 
                type="password",
                placeholder="Gmail의 경우 앱 비밀번호를 사용하세요"
            )
            
            if st.form_submit_button("💾 설정 저장"):
                if all([smtp_server, smtp_port, sender_email, sender_password]):
                    settings = {
                        'server': smtp_server,
                        'port': int(smtp_port),
                        'email': sender_email,
                        'password': sender_password
                    }
                    
                    # 설정 테스트
                    try:
                        server = smtplib.SMTP(smtp_server, int(smtp_port))
                        server.starttls()
                        server.login(sender_email, sender_password)
                        server.quit()
                        
                        st.session_state.newsletter_data['email_settings'] = settings
                        save_settings(settings)
                        st.success("✅ SMTP 설정이 성공적으로 저장되었습니다!")
                        
                    except Exception as e:
                        st.error(f"❌ SMTP 연결 테스트 실패: {str(e)}")
                else:
                    st.error("모든 필드를 입력해주세요.")
        
        # Gmail 설정 안내
        with st.expander("📖 Gmail 설정 방법"):
            st.write("""
            **Gmail 사용 시 설정 방법:**
            
            1. Google 계정의 2단계 인증을 활성화하세요
            2. Google 계정 > 보안 > 앱 비밀번호로 이동
            3. '메일' 앱용 비밀번호를 생성하세요
            4. 생성된 16자리 비밀번호를 위의 '비밀번호' 필드에 입력하세요
            
            **설정값:**
            - SMTP 서버: smtp.gmail.com
            - 포트: 587
            - 이메일: 본인의 Gmail 주소
            - 비밀번호: 생성한 앱 비밀번호
            """)
    
    elif menu == "👥 주소록 관리":
        st.header("주소록 관리")
        
        # 파일 업로드
        uploaded_file = st.file_uploader(
            "CSV 파일 업로드 (이름, 이메일 열 필요)",
            type=['csv']
        )
        
        if uploaded_file:
            try:
                df = pd.read_csv(uploaded_file)
                st.session_state.newsletter_data['address_book'] = df
                st.success("주소록이 성공적으로 업로드되었습니다!")
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
                    st.success("연락처가 추가되었습니다!")
                    st.rerun()
                else:
                    st.error("올바른 이름과 이메일을 입력해주세요.")
        
        # 현재 주소록 표시
        if not st.session_state.newsletter_data['address_book'].empty:
            st.subheader(f"현재 주소록 ({len(st.session_state.newsletter_data['address_book'])}명)")
            st.dataframe(st.session_state.newsletter_data['address_book'])
            
            # 다운로드 버튼
            csv = st.session_state.newsletter_data['address_book'].to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                label="📥 주소록 다운로드 (CSV)",
                data=csv,
                file_name=f"address_book_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
        
        # 샘플 CSV 다운로드
        with st.expander("📋 샘플 CSV 형식"):
            sample_df = pd.DataFrame({
                '이름': ['홍길동', '김영희', '이철수'],
                '이메일': ['hong@example.com', 'kim@example.com', 'lee@example.com']
            })
            st.write("다음과 같은 형식의 CSV 파일을 업로드하세요:")
            st.dataframe(sample_df)
            
            sample_csv = sample_df.to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                label="📥 샘플 CSV 다운로드",
                data=sample_csv,
                file_name="sample_address_book.csv",
                mime="text/csv"
            )
    
    elif menu == "📤 발송하기":
        st.header("뉴스레터 발송")
        
        # 발송 전 체크리스트
        email_configured = bool(st.session_state.newsletter_data['email_settings'])
        has_news = bool(st.session_state.newsletter_data['news_items'])
        has_addresses = not st.session_state.newsletter_data['address_book'].empty
        
        st.subheader("📋 발송 준비 상태")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.write("📧 이메일 설정")
            if email_configured:
                st.success("✅ 완료")
            else:
                st.error("❌ 미완료")
        
        with col2:
            st.write("📰 뉴스 항목")
            if has_news:
                st.success(f"✅ {len(st.session_state.newsletter_data['news_items'])}개")
            else:
                st.error("❌ 없음")
        
        with col3:
            st.write("👥 주소록")
            if has_addresses:
                st.success(f"✅ {len(st.session_state.newsletter_data['address_book'])}명")
            else:
                st.error("❌ 없음")
        
        if email_configured and has_news and has_addresses:
            st.markdown('<div class="success-box">모든 준비가 완료되었습니다! 🎉</div>', 
                       unsafe_allow_html=True)
            
            # 발송 설정
            subject = st.text_input(
                "이메일 제목", 
                value=f"[법률사무소] 법률 뉴스레터 - {datetime.now().strftime('%Y년 %m월 %d일')}"
            )
            
            custom_message = st.text_area(
                "사용자 정의 메시지 (선택사항)",
                placeholder="고객에게 전달하고 싶은 특별한 메시지를 입력하세요...",
                height=100
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
            
            # 발송 버튼
            if st.button("🚀 뉴스레터 발송", type="primary"):
                if subject:
                    with st.spinner("뉴스레터를 발송 중입니다..."):
                        html_content = create_html_newsletter(
                            st.session_state.newsletter_data['news_items'],
                            custom_message
                        )
                        
                        sent_count, failed_emails = send_newsletter(
                            selected_emails,
                            subject,
                            html_content,
                            st.session_state.newsletter_data['email_settings']
                        )
                        
                        if sent_count > 0:
                            st.success(f"✅ {sent_count}명에게 성공적으로 발송되었습니다!")
                        
                        if failed_emails:
                            st.error("❌ 발송 실패:")
                            for error in failed_emails:
                                st.write(f"- {error}")
                else:
                    st.error("이메일 제목을 입력해주세요.")
        else:
            st.markdown('<div class="warning-box">발송하기 전에 모든 설정을 완료해주세요.</div>', 
                       unsafe_allow_html=True)
            missing_items = []
            if not email_configured:
                missing_items.append("📧 이메일 설정")
            if not has_news:
                missing_items.append("📰 뉴스 항목 추가")
            if not has_addresses:
                missing_items.append("👥 주소록 등록")
            
            st.write("**미완료 항목:**")
            for item in missing_items:
                st.write(f"- {item}")

if __name__ == "__main__":
    main()