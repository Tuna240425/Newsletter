import os

# ==============================================
# 회사별 기본 설정 - 여기서 한 번만 수정하세요
# ==============================================

COMPANY_CONFIG = {
    # 회사 정보
    'company_name': '임앤리 법률사무소',
    'company_email': 'lshlawfirm2@gmail.com',
    'company_password': 'wsbn vanl ywza ochf',
    
    # 사무실 정보 (뉴스레터 하단에 표시)
    'office_info': {
        'address': '서울시 강남구 테헤란로 123, ABC빌딩 10층',
        'phone': '02-1234-5678',
        'website': 'https://lshlawfirm.com',
        'business_hours': '평일 09:00-18:00'
    },
    
    # SMTP 설정
    'smtp_server': 'smtp.gmail.com',
    'smtp_port': 587,
    
    # 뉴스 수집 설정 (개선된 안정적인 소스들)
    'auto_collect_news': True,
    'default_news_sources': [
        # 네이버 뉴스 RSS (사회/경제 섹션)
        'https://news.naver.com/rss/section/102.xml',  # 사회
        'https://news.naver.com/rss/section/101.xml',  # 경제
        'https://news.naver.com/rss/section/100.xml',  # 정치
        
        # 다음 뉴스 RSS
        'https://news.daum.net/rss/society',
        'https://news.daum.net/rss/economic',
        
        # Google News에서 법률 관련 뉴스 검색 (실제 뉴스 기사)
        'https://news.google.com/rss/search?q=법률+개정&hl=ko&gl=KR&ceid=KR:ko',
        'https://news.google.com/rss/search?q=법원+판결&hl=ko&gl=KR&ceid=KR:ko',
        'https://news.google.com/rss/search?q=변호사+법무&hl=ko&gl=KR&ceid=KR:ko',
        'https://news.google.com/rss/search?q=개인정보보호법&hl=ko&gl=KR&ceid=KR:ko',
        'https://news.google.com/rss/search?q=부동산+법률&hl=ko&gl=KR&ceid=KR:ko',
        'https://news.google.com/rss/search?q=노동법+근로기준법&hl=ko&gl=KR&ceid=KR:ko',
        'https://news.google.com/rss/search?q=법무부+정책&hl=ko&gl=KR&ceid=KR:ko',
    ],
    
    # 기본 메시지
    'default_subject_template': '[{company_name}] 법률 뉴스레터 - {date}',
    'default_greeting': '안녕하세요, 임앤리 법률사무소입니다. 최신 소식을 전해 드립니다.',
    'footer_message': '더 자세한 상담이 필요하시면 언제든 연락주세요.',
    
    # 자동화 설정
    'skip_email_setup': True,
    'skip_smtp_test': True,
    
    # OpenAI API 설정 (보안을 위해 환경변수 사용)
    'use_openai': True,
    'openai_api_key': os.getenv('OPENAI_API_KEY', ''),
    
    # 디자인 설정
    'newsletter_template': 'simple',
    'font_style': 'pretendard',
    'use_newsletter_images': True,
    'image_timeout': 3,
    'fallback_to_gradient': True,
}

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