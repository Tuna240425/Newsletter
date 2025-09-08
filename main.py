import streamlit as st
import pandas as pd
from datetime import datetime
from urllib.parse import quote

# 로컬 모듈 import
from config import COMPANY_CONFIG
from utils import pick_contextual_message, generate_ai_message
from news_collector import collect_latest_news
from newsletter_generator import create_html_newsletter
from email_handler import auto_configure_smtp, send_newsletter, test_smtp_connection
from address_book import (
    get_email_column_name, save_address_book, load_address_book, 
    validate_address_book, clean_address_book, add_contact, 
    import_address_book, export_address_book
)

# 페이지 설정
st.set_page_config(
    page_title=f"{COMPANY_CONFIG['company_name']} 뉴스레터 발송 시스템",
    page_icon="📧",
    layout="wide"
)

# CSS 스타일링 (개선된 버전)
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
.error-box {
    background-color: #f8d7da;
    border: 1px solid #f5c6cb;
    border-radius: 5px;
    padding: 15px;
    margin: 10px 0;
}
.info-box {
    background-color: #d1ecf1;
    border: 1px solid #bee5eb;
    border-radius: 5px;
    padding: 15px;
    margin: 10px 0;
}
</style>
""", unsafe_allow_html=True)

# 세션 상태 초기화
def initialize_session_state():
    """세션 상태 초기화 함수"""
    if 'newsletter_data' not in st.session_state:
        st.session_state.newsletter_data = {
            'news_items': [],
            'email_settings': {},
            'address_book': pd.DataFrame(columns=['이름', '이메일']),
            'auto_news_sources': COMPANY_CONFIG['default_news_sources'].copy(),
            'selected_news': [],
            'custom_message': ''
        }
        # 저장된 주소록 자동 로드
        saved_address_book = load_address_book()
        if not saved_address_book.empty:
            st.session_state.newsletter_data['address_book'] = saved_address_book

def main():
    """메인 함수"""
    # 세션 상태 초기화
    initialize_session_state()
    
    # 자동 SMTP 설정 로드
    st.session_state.newsletter_data['email_settings'] = auto_configure_smtp()
    
    # 메인 헤더
    st.markdown(f'<div class="main-header"><h1>📧 {COMPANY_CONFIG["company_name"]} 뉴스레터 발송 시스템</h1></div>', 
                unsafe_allow_html=True)
    
    # 메뉴 구성
    menu_options = ["🏠 홈", "📰 뉴스 수집", "📝 뉴스레터 작성", "👥 주소록 관리", "📤 발송하기"]
    
    if not COMPANY_CONFIG['skip_email_setup']:
        menu_options.insert(-1, "📧 이메일 설정")
    
    menu = st.sidebar.selectbox("메뉴 선택", menu_options)
    
    # 사이드바에 시스템 상태 표시
    show_sidebar_status()
    
    # OpenAI 설정 (사이드바)
    setup_ai_configuration()
    
    # 메뉴별 처리
    if menu == "🏠 홈":
        show_home()
    elif menu == "📰 뉴스 수집":
        show_news_collection()
    elif menu == "📝 뉴스레터 작성":
        show_newsletter_creation()
    elif menu == "👥 주소록 관리":
        show_address_book_management()
    elif menu == "📤 발송하기":
        show_newsletter_sending()
    elif menu == "📧 이메일 설정":
        show_email_setup()

def show_sidebar_status():
    """사이드바에 시스템 상태 표시"""
    st.sidebar.markdown("---")
    st.sidebar.subheader("📊 시스템 상태")
    
    # 뉴스 상태
    news_count = len(st.session_state.newsletter_data['news_items'])
    st.sidebar.metric("📰 수집된 뉴스", f"{news_count}개")
    
    # 주소록 상태
    address_count = len(st.session_state.newsletter_data['address_book'])
    st.sidebar.metric("👥 주소록", f"{address_count}명")
    
    # 이메일 설정 상태
    smtp_configured = bool(st.session_state.newsletter_data['email_settings'])
    st.sidebar.metric("📧 이메일 설정", "✅ 완료" if smtp_configured else "❌ 미완료")
    
    # 뉴스레터 작성 상태
    newsletter_ready = bool(st.session_state.newsletter_data.get('selected_news'))
    st.sidebar.metric("📝 뉴스레터", "✅ 작성됨" if newsletter_ready else "📝 미작성")

def setup_ai_configuration():
    """AI 설정 구성"""
    try:
        from openai import OpenAI
        OPENAI_AVAILABLE = True
    except ImportError:
        OPENAI_AVAILABLE = False
    
    st.sidebar.markdown("---")
    
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
        if COMPANY_CONFIG.get('use_openai'):
            st.sidebar.success("🤖 AI 메시지 생성 활성화됨")
        else:
            st.sidebar.info("🤖 AI 설정 완료 (비활성화)")
    elif not OPENAI_AVAILABLE:
        st.sidebar.info("🤖 AI 기능: openai 모듈 미설치\n(pip install openai로 설치 가능)")

def show_home():
    """홈 페이지"""
    st.header("환영합니다! 👋")
    
    # 자동 설정 상태 표시
    st.markdown('<div class="auto-news-box">✅ 이메일 설정이 자동으로 구성되었습니다!</div>', 
               unsafe_allow_html=True)
    
    # 시스템 소개
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.write(f"""
        **{COMPANY_CONFIG['company_name']} 뉴스레터 발송 시스템**
        
        이 시스템을 사용하여 손쉽게 뉴스레터를 작성하고 발송할 수 있습니다.
        
        **사용 방법:**
        1. **뉴스 수집**: 최신 법률 뉴스를 자동으로 수집하세요
        2. **주소록 관리**: 수신자 명단을 관리하세요  
        3. **뉴스레터 작성**: 수집된 뉴스로 뉴스레터를 작성하세요
        4. **발송하기**: 작성된 뉴스레터를 발송하세요
        
        **개선된 기능:**
        - 🎨 심플하고 전문적인 디자인
        - 🤖 AI 맞춤형 메시지 생성
        - 💾 주소록 자동 저장/불러오기
        - 📅 정확한 뉴스 날짜 표시
        - 🏢 사무실 정보 및 수신거부 안내
        - 📤 Pretendard 폰트 적용
        - 🔗 안정적인 뉴스 수집 (네이버, 다음 등)
        - 🖼️ 안정적인 이미지 표시 (SVG fallback)
        """)
    
    with col2:
        # 빠른 작업 버튼들
        st.subheader("🚀 빠른 작업")
        
        if st.button("📰 뉴스 수집 시작", use_container_width=True):
            st.session_state.menu_selection = "📰 뉴스 수집"
            st.rerun()
        
        if st.button("📝 뉴스레터 작성", use_container_width=True):
            st.session_state.menu_selection = "📝 뉴스레터 작성"
            st.rerun()
        
        if st.button("👥 주소록 관리", use_container_width=True):
            st.session_state.menu_selection = "👥 주소록 관리"
            st.rerun()
    
    # 통계 정보
    st.subheader("📊 현재 상태")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📰 뉴스 항목", len(st.session_state.newsletter_data['news_items']))
    with col2:
        st.metric("👥 주소록", len(st.session_state.newsletter_data['address_book']))
    with col3:
        smtp_configured = bool(st.session_state.newsletter_data['email_settings'])
        st.metric("📧 이메일", "✅" if smtp_configured else "❌")
    with col4:
        ai_status = "✅" if COMPANY_CONFIG.get('use_openai') else "🔒"
        st.metric("🤖 AI 메시지", ai_status)
    
    # 최근 활동 (선택사항)
    if 'send_history' in st.session_state and st.session_state.send_history:
        st.subheader("📋 최근 발송 이력")
        recent_sends = st.session_state.send_history[-3:]  # 최근 3개
        for send in reversed(recent_sends):
            with st.expander(f"{send['date']} - {send['subject']}"):
                st.write(f"수신자: {send['recipients']}명")
                st.write(f"상태: {send['status']}")

def show_news_collection():
    """뉴스 수집 페이지"""
    st.header("뉴스 자동 수집")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.subheader("📡 뉴스 소스 관리")
        
        # 뉴스 소스 표시 및 관리
        sources = st.session_state.newsletter_data['auto_news_sources']
        
        for i, source in enumerate(sources):
            col_a, col_b = st.columns([4, 1])
            with col_a:
                st.text(f"{i+1}. {source}")
            with col_b:
                if st.button("🗑️", key=f"source_delete_{i}", help="소스 삭제"):
                    st.session_state.newsletter_data['auto_news_sources'].pop(i)
                    st.rerun()
        
        # 새 소스 추가
        new_source = st.text_input("새로운 뉴스 소스 URL 추가")
        if st.button("➕ 소스 추가") and new_source:
            if new_source.startswith('http'):
                st.session_state.newsletter_data['auto_news_sources'].append(new_source)
                st.success("뉴스 소스가 추가되었습니다.")
                st.rerun()
            else:
                st.error("올바른 URL을 입력해주세요 (http:// 또는 https://로 시작)")
    
    with col2:
        st.subheader("뉴스 수집")
        
        if st.button("최신 뉴스 수집", type="primary"):
            with st.spinner("안정적인 소스에서 뉴스를 수집하는 중..."):
                collected_news = collect_latest_news(force_refresh=False)
                
                if collected_news:
                    st.session_state.newsletter_data['news_items'] = collected_news
                    st.success(f"{len(collected_news)}개의 뉴스를 수집했습니다!")
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
        
        # 검색 키워드 추가 섹션
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
        
        # 필터링 옵션
        col1, col2 = st.columns(2)
        with col1:
            filter_keyword = st.text_input("뉴스 제목 필터링 (키워드 입력)")
        with col2:
            source_filter = st.selectbox("소스 필터", 
                                       ["전체"] + list(set([item.get('source', '자동수집') 
                                                         for item in st.session_state.newsletter_data['news_items']])))
        
        # 필터링 적용
        filtered_news = st.session_state.newsletter_data['news_items']
        if filter_keyword:
            filtered_news = [item for item in filtered_news 
                           if filter_keyword.lower() in item['title'].lower()]
        if source_filter != "전체":
            filtered_news = [item for item in filtered_news 
                           if item.get('source', '자동수집') == source_filter]
        
        # 뉴스 표시
        for i, item in enumerate(filtered_news):
            with st.expander(f"{i+1}. {item['title']} ({item['date']})"):
                st.write(f"🔗 **URL**: {item['url']}")
                st.write(f"📅 **날짜**: {item['date']}")
                st.write(f"📰 **소스**: {item.get('source', '수동입력')}")
                if 'raw_date' in item:
                    st.write(f"🗓 **원본 날짜**: {item['raw_date']}")

def show_newsletter_creation():
    """뉴스레터 작성 페이지"""
    st.header("뉴스레터 작성")
    
    # 뉴스가 없는 경우 안내
    if not st.session_state.newsletter_data['news_items']:
        st.markdown('<div class="warning-box">먼저 \'뉴스 수집\' 메뉴에서 뉴스를 수집하세요.</div>', 
                   unsafe_allow_html=True)
        if st.button("📄 뉴스 수집하러 가기"):
            st.session_state.menu_selection = "📰 뉴스 수집"
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
        if st.button("🤖 AI 맞춤 메시지"):
            # AI 기능 가용성 확인
            if not check_ai_availability():
                return
            
            with st.spinner("AI가 메시지를 생성하는 중..."):
                ai_message = generate_ai_message()
                fallback_message = pick_contextual_message()
                
                if ai_message != fallback_message:
                    st.session_state.current_message = ai_message
                    st.success("✅ AI 메시지가 생성되었습니다!")
                    st.markdown(f'<div class="ai-message-box">🤖 AI가 생성한 메시지: {ai_message}</div>', 
                               unsafe_allow_html=True)
                    st.rerun()
                else:
                    st.error("❌ AI 메시지 생성에 실패했습니다. 기본 메시지를 사용합니다.")
                    st.session_state.current_message = fallback_message
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
    
    # 전체 선택/해제 버튼
    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ 전체 선택"):
            for i in range(len(st.session_state.newsletter_data['news_items'])):
                st.session_state[f"news_select_{i}"] = True
            st.rerun()
    with col2:
        if st.button("❌ 전체 해제"):
            for i in range(len(st.session_state.newsletter_data['news_items'])):
                st.session_state[f"news_select_{i}"] = False
            st.rerun()
    
    selected_indices = []
    for i, item in enumerate(st.session_state.newsletter_data['news_items']):
        default_selected = True if i < 5 else False  # 처음 5개는 기본 선택
        if st.checkbox(f"{item['title']} ({item['date']})", 
                      value=st.session_state.get(f"news_select_{i}", default_selected), 
                      key=f"news_select_{i}"):
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
        
        st.success("✅ 뉴스레터가 작성되었습니다. '발송하기' 메뉴에서 발송할 수 있습니다.")
    else:
        st.warning("발송할 뉴스를 선택해주세요.")

def check_ai_availability():
    """AI 기능 가용성 확인"""
    try:
        from openai import OpenAI
        OPENAI_AVAILABLE = True
    except ImportError:
        OPENAI_AVAILABLE = False
    
    if not OPENAI_AVAILABLE:
        st.markdown('<div class="error-box">❌ OpenAI 모듈이 설치되지 않았습니다.<br>설치 방법: pip install openai</div>', 
                   unsafe_allow_html=True)
        return False
    elif not COMPANY_CONFIG.get('use_openai'):
        st.markdown('<div class="warning-box">⚠️ AI 기능이 비활성화되어 있습니다.<br>상단 COMPANY_CONFIG에서 \'use_openai\': True로 설정하거나 사이드바에서 활성화하세요.</div>', 
                   unsafe_allow_html=True)
        return False
    elif not COMPANY_CONFIG.get('openai_api_key'):
        st.markdown('<div class="warning-box">⚠️ OpenAI API 키가 설정되지 않았습니다.<br>사이드바에서 API 키를 입력하거나 환경변수로 설정하세요.</div>', 
                   unsafe_allow_html=True)
        return False
    return True

def show_address_book_management():
    """주소록 관리 페이지"""
    st.header("주소록 관리")
    
    # 주소록 자동 저장/불러오기 안내
    col1, col2 = st.columns(2)
    with col1:
        st.info("💾 주소록은 자동으로 저장됩니다")
    with col2:
        if st.button("🔄 저장된 주소록 다시 불러오기"):
            saved_address_book = load_address_book()
            if not saved_address_book.empty:
                st.session_state.newsletter_data['address_book'] = saved_address_book
                st.success("저장된 주소록을 불러왔습니다!")
                st.rerun()
            else:
                st.warning("저장된 주소록이 없습니다.")
    
    # 파일 업로드
    uploaded_file = st.file_uploader("CSV 파일 업로드 (이름, 이메일 열 필요)", type=['csv'])
    
    if uploaded_file:
        result_df, message = import_address_book(uploaded_file)
        if result_df is not None:
            st.session_state.newsletter_data['address_book'] = result_df
            save_address_book(result_df)  # 자동 저장
            st.success(message)
            st.rerun()
        else:
            st.error(message)
    
    # 수동 입력
    with st.expander("➕ 수동으로 연락처 추가"):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("이름")
        with col2:
            email = st.text_input("이메일")
        
        if st.button("추가"):
            result_df, message = add_contact(
                st.session_state.newsletter_data['address_book'], name, email
            )
            st.session_state.newsletter_data['address_book'] = result_df
            save_address_book(result_df)  # 자동 저장
            
            if "성공적으로" in message:
                st.success(message)
                st.rerun()
            else:
                st.error(message)
    
    # 현재 주소록 표시
    if not st.session_state.newsletter_data['address_book'].empty:
        st.subheader(f"현재 주소록 ({len(st.session_state.newsletter_data['address_book'])}명)")
        
        # 주소록 편집 기능
        edited_df = st.data_editor(
            st.session_state.newsletter_data['address_book'],
            num_rows="dynamic",
            use_container_width=True,
            key="address_book_editor"
        )
        
        if not edited_df.equals(st.session_state.newsletter_data['address_book']):
            st.session_state.newsletter_data['address_book'] = edited_df
            save_address_book(edited_df)  # 자동 저장
            st.success("주소록 변경사항이 저장되었습니다!")
        
        # 다운로드 및 관리 버튼
        col1, col2, col3 = st.columns(3)
        
        with col1:
            csv_data, message = export_address_book(st.session_state.newsletter_data['address_book'])
            if csv_data:
                st.download_button(
                    label="📥 주소록 다운로드 (CSV)",
                    data=csv_data,
                    file_name=f"address_book_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )
        
        with col2:
            if st.button("🧹 주소록 정리"):
                cleaned_df = clean_address_book(st.session_state.newsletter_data['address_book'])
                st.session_state.newsletter_data['address_book'] = cleaned_df
                save_address_book(cleaned_df)
                st.success("주소록이 정리되었습니다 (중복 제거, 빈 값 정리)")
                st.rerun()
        
        with col3:
            if st.button("🗑️ 주소록 초기화", type="secondary"):
                if st.button("정말 삭제하시겠습니까?", type="secondary"):
                    st.session_state.newsletter_data['address_book'] = pd.DataFrame(columns=['이름', '이메일'])
                    save_address_book(st.session_state.newsletter_data['address_book'])
                    st.success("주소록이 초기화되었습니다.")
                    st.rerun()
        
        # 주소록 유효성 검사
        is_valid, validation_message = validate_address_book(st.session_state.newsletter_data['address_book'])
        if is_valid:
            st.success(f"✅ {validation_message}")
        else:
            st.error(f"❌ {validation_message}")
            
    else:
        st.info("아직 등록된 주소록이 없습니다. CSV 파일을 업로드하거나 수동으로 추가해보세요.")

def show_newsletter_sending():
    """뉴스레터 발송 페이지"""
    st.header("뉴스레터 발송")
    
    # 발송 전 체크리스트
    email_configured = bool(st.session_state.newsletter_data['email_settings'])
    has_news = bool(st.session_state.newsletter_data.get('selected_news', []))
    has_addresses = not st.session_state.newsletter_data['address_book'].empty
    
    st.subheader("📋 발송 준비 상태")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.write("📧 이메일 설정")
        if email_configured:
            st.success("✅ 자동 구성됨")
        else:
            st.error("❌ 설정 필요")
    
    with col2:
        st.write("📰 뉴스레터")
        if has_news:
            st.success(f"✅ {len(st.session_state.newsletter_data.get('selected_news', []))}개 뉴스")
        else:
            st.error("❌ 뉴스레터 미작성")
    
    with col3:
        st.write("👥 주소록")
        if has_addresses:
            # 이메일 컬럼 존재 여부 확인
            email_col = get_email_column_name(st.session_state.newsletter_data['address_book'])
            if email_col:
                st.success(f"✅ {len(st.session_state.newsletter_data['address_book'])}명")
            else:
                st.error("❌ 이메일 컬럼 없음")
                has_addresses = False
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
        address_book = st.session_state.newsletter_data['address_book']
        email_col = get_email_column_name(address_book)
        
        if email_col:
            all_emails = address_book[email_col].dropna().tolist()
            # 빈 문자열 제거
            all_emails = [email.strip() for email in all_emails if str(email).strip()]
            
            if all_emails:
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
                
                # 테스트 발송 기능
                with st.expander("🧪 테스트 발송 (선택사항)"):
                    test_email = st.text_input("테스트 이메일 주소")
                    if st.button("📧 테스트 발송") and test_email:
                        if subject:
                            with st.spinner("테스트 이메일을 발송 중입니다..."):
                                html_content = create_html_newsletter(
                                    st.session_state.newsletter_data.get('selected_news', []),
                                    st.session_state.newsletter_data.get('custom_message', '')
                                )
                                
                                sent_count, failed_emails = send_newsletter(
                                    [test_email],
                                    f"[테스트] {subject}",
                                    html_content,
                                    st.session_state.newsletter_data['email_settings']
                                )
                                
                                if sent_count > 0:
                                    st.success("✅ 테스트 이메일이 성공적으로 발송되었습니다!")
                                else:
                                    st.error(f"❌ 테스트 발송 실패: {failed_emails}")
                        else:
                            st.error("이메일 제목을 입력해주세요.")
                
                # 실제 발송 버튼
                st.write("---")
                if st.button("🚀 뉴스레터 발송", type="primary", use_container_width=True):
                    if subject:
                        # 발송 확인
                        confirm = st.checkbox(f"정말로 {len(selected_emails)}명에게 발송하시겠습니까?")
                        if confirm:
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
                            st.info("위의 체크박스를 선택하여 발송을 확인해주세요.")
                    else:
                        st.error("이메일 제목을 입력해주세요.")
            else:
                st.error("유효한 이메일 주소가 없습니다.")
        else:
            st.error("주소록에서 이메일 컬럼을 찾을 수 없습니다.")
    else:
        st.markdown('<div class="warning-box">발송하기 전에 모든 설정을 완료해주세요.</div>', 
                   unsafe_allow_html=True)
        
        # 부족한 설정으로 이동하는 버튼들
        if not has_news:
            if st.button("📝 뉴스레터 작성하러 가기"):
                st.session_state.menu_selection = "📝 뉴스레터 작성"
                st.rerun()
        
        if not has_addresses:
            if st.button("👥 주소록 관리하러 가기"):
                st.session_state.menu_selection = "👥 주소록 관리"
                st.rerun()

def show_email_setup():
    """이메일 설정 페이지"""
    st.header("이메일 설정")
    
    current_settings = st.session_state.newsletter_data.get('email_settings', {})
    
    with st.form("email_settings_form"):
        st.subheader("SMTP 설정")
        
        server = st.text_input("SMTP 서버", value=current_settings.get('server', ''))
        port = st.number_input("포트", value=current_settings.get('port', 587), min_value=1, max_value=65535)
        email = st.text_input("이메일 주소", value=current_settings.get('email', ''))
        password = st.text_input("비밀번호", type="password", value=current_settings.get('password', ''))
        sender_name = st.text_input("발신자 이름", value=current_settings.get('sender_name', ''))
        
        submitted = st.form_submit_button("설정 저장")
        
        if submitted:
            new_settings = {
                'server': server,
                'port': port,
                'email': email,
                'password': password,
                'sender_name': sender_name
            }
            
            # 연결 테스트
            success, message = test_smtp_connection(new_settings)
            
            if success:
                st.session_state.newsletter_data['email_settings'] = new_settings
                st.success("✅ 이메일 설정이 저장되었습니다!")
                st.success(message)
            else:
                st.error("❌ 이메일 설정 실패:")
                st.error(message)

if __name__ == "__main__":
    main()