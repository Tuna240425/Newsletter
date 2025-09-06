#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
인사말 자동 생성 모듈
계절, 날짜, 특별한 날에 맞는 따뜻한 인사말을 자동 생성
"""

import random
from datetime import datetime, date
import calendar
import requests
import base64
from io import BytesIO

class GreetingGenerator:
    def __init__(self):
        self.season_greetings = {
            'spring': [
                "따뜻한 봄날, 새로운 시작과 함께 희망찬 소식을 전해드립니다.",
                "꽃피는 봄처럼 여러분의 일상에도 기쁜 일들이 가득하시길 바랍니다.",
                "봄바람과 함께 전하는 법률 소식, 오늘도 좋은 하루 되세요.",
                "새싹이 돋아나는 계절, 새로운 법률 정보로 인사드립니다.",
                "봄의 전령처럼 반가운 소식들을 가져왔습니다.",
                "만물이 소생하는 봄, 여러분께도 새로운 활력이 되길 바랍니다.",
                "벚꽃이 만개하듯 여러분의 꿈도 활짝 피어나시길 바랍니다."
            ],
            'summer': [
                "무더운 여름날, 시원한 법률 정보로 안녕하세요.",
                "여름 휴가철, 잠시 쉬어가는 마음으로 소식을 전해드립니다.",
                "뜨거운 태양 아래서도 변함없는 신뢰로 인사드립니다.",
                "활기찬 여름날, 유익한 정보와 함께 인사드립니다.",
                "여름 장마 속에서도 맑은 정보를 전해드립니다.",
                "휴가철이지만 쉬지 않는 법률 소식을 준비했습니다.",
                "더위에 지치지 않도록 시원한 소식으로 찾아뵙습니다."
            ],
            'autumn': [
                "가을 단풍처럼 풍성한 법률 소식을 전해드립니다.",
                "선선한 가을바람과 함께 유익한 정보를 나누고자 합니다.",
                "결실의 계절, 여러분께도 좋은 결과가 있으시길 바랍니다.",
                "가을 하늘만큼 맑은 마음으로 소식을 전해드립니다.",
                "단풍잎이 물들듯 알찬 내용으로 준비했습니다.",
                "가을 추수철처럼 풍성한 정보를 수확해가시길 바랍니다.",
                "선선한 바람과 함께 마음 편한 소식을 전합니다."
            ],
            'winter': [
                "추운 겨울, 따뜻한 마음으로 법률 소식을 전해드립니다.",
                "하얀 눈처럼 깨끗한 마음으로 인사드립니다.",
                "겨울 끝자락에서 봄을 기다리며, 희망찬 소식을 나눕니다.",
                "따뜻한 실내에서 편히 읽으실 수 있는 소식을 준비했습니다.",
                "눈 내리는 겨울날, 마음만은 따뜻한 소식을 전합니다.",
                "연말연시 분주한 시기, 잠시 여유를 갖고 읽어보세요.",
                "겨울 찬바람을 막아주는 따뜻한 정보를 전해드립니다."
            ]
        }
        
        self.special_day_greetings = {
            'new_year': [
                "새해 복 많이 받으세요! 2024년에도 함께하겠습니다.",
                "새로운 한 해의 시작, 더욱 발전하는 모습으로 찾아뵙겠습니다.",
                "희망찬 새해, 여러분의 모든 일이 순조롭게 이루어지길 바랍니다.",
                "새해 첫 소식으로 인사드립니다. 올 한 해도 잘 부탁드립니다."
            ],
            'monday': [
                "새로운 한 주의 시작, 활기찬 월요일 아침입니다.",
                "월요일 오전, 신선한 법률 정보로 한 주를 시작하세요.",
                "새 주간이 시작되었습니다. 좋은 일만 가득하시길 바랍니다.",
                "월요일의 새로운 에너지와 함께 인사드립니다."
            ],
            'friday': [
                "한 주간의 마무리, 편안한 주말 보내시길 바랍니다.",
                "금요일 오후, 여유로운 마음으로 소식을 전해드립니다.",
                "일주일을 마무리하며 감사한 마음으로 인사드립니다.",
                "주말을 앞둔 금요일, 기분 좋은 소식을 전합니다."
            ],
            'holiday': [
                "즐거운 휴일, 가족과 함께 행복한 시간 보내세요.",
                "휴일의 여유로움 속에서 가볍게 읽어보실 소식입니다.",
                "공휴일을 맞아 편안한 마음으로 준비한 소식입니다.",
                "휴일에도 찾아주셔서 감사합니다."
            ],
            'month_end': [
                "한 달을 마무리하며 그동안의 소식을 정리해드립니다.",
                "월말을 맞아 이번 달의 주요 동향을 전해드립니다.",
                "바쁜 월말, 중요한 정보만 간추려서 전해드립니다."
            ],
            'month_start': [
                "새로운 달의 시작, 신선한 마음으로 인사드립니다.",
                "월초를 맞아 이번 달 계획과 함께 소식을 전합니다.",
                "새 달 첫 소식으로 여러분께 인사드립니다."
            ]
        }
        
        self.weather_greetings = {
            'rainy': [
                "비 오는 날, 실내에서 따뜻하게 읽어보실 소식입니다.",
                "촉촉한 비와 함께 전하는 법률 정보입니다.",
                "장마철 우울함을 달래줄 밝은 소식을 준비했습니다."
            ],
            'sunny': [
                "맑은 하늘처럼 깨끗한 정보를 전해드립니다.",
                "화창한 날씨만큼 밝은 소식을 준비했습니다.",
                "햇살 좋은 날, 기분 좋은 소식과 함께합니다."
            ],
            'cloudy': [
                "구름 낀 하늘 아래, 잠시 여유를 갖고 읽어보세요.",
                "차분한 날씨에 어울리는 차분한 소식을 전합니다.",
                "흐린 날씨지만 마음만은 맑은 정보를 전해드립니다."
            ]
        }
        
        # 특별한 날짜들
        self.special_dates = {
            '1-1': 'new_year',
            '3-1': '삼일절',
            '5-5': '어린이날', 
            '6-6': '현충일',
            '8-15': '광복절',
            '10-3': '개천절',
            '10-9': '한글날',
            '12-25': '크리스마스'
        }
        
        # 법률 관련 특별 인사말
        self.legal_greetings = [
            "법과 정의가 함께하는 하루 되시길 바랍니다.",
            "공정하고 투명한 사회를 만들어가는 데 함께해주셔서 감사합니다.",
            "올바른 법률 정보로 여러분의 권익을 보호하겠습니다.",
            "신뢰할 수 있는 법률 파트너로서 항상 곁에 있겠습니다.",
            "정확한 정보와 성실한 서비스로 보답하겠습니다."
        ]
    
    def get_season(self, date_obj=None):
        """현재 계절 판단"""
        if date_obj is None:
            date_obj = datetime.now()
        
        month = date_obj.month
        
        if month in [3, 4, 5]:
            return 'spring'
        elif month in [6, 7, 8]:
            return 'summer'
        elif month in [9, 10, 11]:
            return 'autumn'
        else:
            return 'winter'
    
    def get_special_day_type(self, date_obj=None):
        """특별한 날 판단"""
        if date_obj is None:
            date_obj = datetime.now()
        
        # 새해
        if date_obj.month == 1 and date_obj.day <= 3:
            return 'new_year'
        
        # 월초/월말
        if date_obj.day <= 3:
            return 'month_start'
        elif date_obj.day >= 28:
            return 'month_end'
        
        # 요일별
        weekday = date_obj.weekday()
        if weekday == 0:  # 월요일
            return 'monday'
        elif weekday == 4:  # 금요일
            return 'friday'
        elif weekday >= 5:  # 주말
            return 'holiday'
        
        # 특별한 날짜 확인
        date_key = f"{date_obj.month}-{date_obj.day}"
        if date_key in self.special_dates:
            return self.special_dates[date_key]
        
        return None
    
    def get_time_greeting(self, date_obj=None):
        """시간대별 인사말"""
        if date_obj is None:
            date_obj = datetime.now()
        
        hour = date_obj.hour
        
        if 6 <= hour < 12:
            return "좋은 아침입니다"
        elif 12 <= hour < 18:
            return "좋은 오후입니다"
        elif 18 <= hour < 22:
            return "좋은 저녁입니다"
        else:
            return "늦은 시간까지 수고하십니다"
    
    def generate_greeting(self, include_weather=False, custom_message="", date_obj=None):
        """인사말 생성"""
        if date_obj is None:
            date_obj = datetime.now()
        
        season = self.get_season(date_obj)
        special_day = self.get_special_day_type(date_obj)
        
        # 인사말 선택 우선순위: 특별한 날 > 계절별
        if special_day and special_day in self.special_day_greetings:
            greeting = random.choice(self.special_day_greetings[special_day])
        else:
            greeting = random.choice(self.season_greetings[season])
        
        # 시간대 인사말 추가
        time_greeting = self.get_time_greeting(date_obj)
        
        # 날짜 정보 
        date_str = date_obj.strftime("%Y년 %m월 %d일")
        day_name = calendar.day_name[date_obj.weekday()]
        day_korean = {
            'Monday': '월요일', 'Tuesday': '화요일', 'Wednesday': '수요일',
            'Thursday': '목요일', 'Friday': '금요일', 'Saturday': '토요일', 'Sunday': '일요일'
        }
        
        # 법률 관련 추가 인사말 (랜덤으로 포함)
        legal_greeting = ""
        if random.choice([True, False]):  # 50% 확률로 추가
            legal_greeting = f"<br><br>{random.choice(self.legal_greetings)}"
        
        # HTML 구성
        full_greeting = f"""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    color: white; padding: 30px; border-radius: 12px; margin: 20px 0;
                    box-shadow: 0 4px 20px rgba(102, 126, 234, 0.3);">
            <div style="text-align: center; margin-bottom: 20px;">
                <h3 style="margin: 0 0 5px 0; font-size: 20px; font-weight: 600;">
                    {date_str} {day_korean[day_name]}
                </h3>
                <p style="margin: 0; font-size: 14px; opacity: 0.9;">
                    {time_greeting}
                </p>
            </div>
            <div style="text-align: center; padding: 15px 0; border-top: 1px solid rgba(255,255,255,0.2); border-bottom: 1px solid rgba(255,255,255,0.2);">
                <p style="margin: 0; font-size: 16px; line-height: 1.6;">
                    {greeting}
                </p>
                {legal_greeting}
            </div>
            {f'<div style="text-align: center; margin-top: 15px; padding-top: 15px; border-top: 1px solid rgba(255,255,255,0.2);"><p style="margin: 0; font-style: italic; font-size: 15px;">{custom_message}</p></div>' if custom_message else ''}
        </div>
        """
        
        return full_greeting.strip()
    
    def get_seasonal_image_url(self, season=None):
        """계절별 이미지 URL 반환 (Unsplash 무료 이미지)"""
        if season is None:
            season = self.get_season()
        
        # 고품질 무료 이미지 (Unsplash)
        image_urls = {
            'spring': [
                'https://images.unsplash.com/photo-1490750967868-88aa4486c946?w=600&h=250&fit=crop&auto=format',  # 벚꽃
                'https://images.unsplash.com/photo-1520637736862-4d197d17c93a?w=600&h=250&fit=crop&auto=format',  # 꽃밭
                'https://images.unsplash.com/photo-1463936575829-25148e1db1b8?w=600&h=250&fit=crop&auto=format',  # 봄 풍경
                'https://images.unsplash.com/photo-1426604966848-d7adac402bff?w=600&h=250&fit=crop&auto=format',  # 자연
            ],
            'summer': [
                'https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=600&h=250&fit=crop&auto=format',  # 해변
                'https://images.unsplash.com/photo-1473773508845-188df298d2d1?w=600&h=250&fit=crop&auto=format',  # 여름 풍경
                'https://images.unsplash.com/photo-1439066615861-d1af74d74000?w=600&h=250&fit=crop&auto=format',  # 호수
                'https://images.unsplash.com/photo-1501436513145-30f24e19fcc4?w=600&h=250&fit=crop&auto=format',  # 여름 하늘
            ],
            'autumn': [
                'https://images.unsplash.com/photo-1507038732509-8b2f3b3ba9c0?w=600&h=250&fit=crop&auto=format',  # 단풍
                'https://images.unsplash.com/photo-1478186015820-5d2c6b8e5fec?w=600&h=250&fit=crop&auto=format',  # 가을 나무
                'https://images.unsplash.com/photo-1445363017215-0deda59f5ac5?w=600&h=250&fit=crop&auto=format',  # 가을 길
                'https://images.unsplash.com/photo-1441974231531-c6227db76b6e?w=600&h=250&fit=crop&auto=format',  # 가을 숲
            ],
            'winter': [
                'https://images.unsplash.com/photo-1483664852095-d6cc6870702d?w=600&h=250&fit=crop&auto=format',  # 겨울 풍경
                'https://images.unsplash.com/photo-1477601263568-180e2c6d046e?w=600&h=250&fit=crop&auto=format',  # 눈 풍경
                'https://images.unsplash.com/photo-1481662875270-0ca22045d53c?w=600&h=250&fit=crop&auto=format',  # 겨울 나무
                'https://images.unsplash.com/photo-1421749810611-438cc492b581?w=600&h=250&fit=crop&auto=format',  # 설경
            ]
        }
        
        return random.choice(image_urls.get(season, image_urls['spring']))
    
    def generate_complete_greeting(self, custom_message="", include_image=True, date_obj=None):
        """완전한 인사말 (텍스트 + 이미지) 생성"""
        greeting_html = self.generate_greeting(custom_message=custom_message, date_obj=date_obj)
        
        if include_image:
            season = self.get_season(date_obj)
            image_url = self.get_seasonal_image_url(season)
            
            complete_greeting = f"""
            <div style="margin: 20px 0; background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 20px rgba(0,0,0,0.1);">
                <div style="position: relative;">
                    <img src="{image_url}" 
                         style="width: 100%; height: 200px; object-fit: cover; display: block;" 
                         alt="계절 이미지"
                         loading="lazy">
                    <div style="position: absolute; top: 0; left: 0; right: 0; bottom: 0; 
                                background: linear-gradient(to bottom, rgba(0,0,0,0.1), rgba(0,0,0,0.3));">
                    </div>
                </div>
                {greeting_html}
            </div>
            """
        else:
            complete_greeting = f"""
            <div style="margin: 20px 0;">
                {greeting_html}
            </div>
            """
        
        return complete_greeting
    
    def generate_email_signature(self):
        """이메일 서명 생성"""
        signatures = [
            "항상 정확한 정보로 함께하겠습니다.",
            "믿을 수 있는 법률 파트너",
            "정의로운 사회를 만들어가는 든든한 동반자",
            "여러분의 권익 보호를 위해 최선을 다하겠습니다.",
            "성실과 신뢰를 바탕으로 한 전문 서비스"
        ]
        
        return random.choice(signatures)
    
    def generate_seasonal_tips(self, season=None):
        """계절별 법률 팁 생성"""
        if season is None:
            season = self.get_season()
        
        tips = {
            'spring': [
                "봄철 이사 시 임대차 계약 검토 포인트를 확인하세요.",
                "새 학기 시작 전 교육 관련 법규 변경사항을 점검하세요.",
                "봄맞이 리모델링 전 건축 관련 법규를 확인하세요."
            ],
            'summer': [
                "휴가철 근로기준법상 연차 사용 권리를 확인하세요.",
                "여름철 전력 사용 관련 에너지 법규를 점검하세요.",
                "휴가지에서의 안전사고 대비 보험 약관을 확인하세요."
            ],
            'autumn': [
                "연말 정산 준비를 위한 세법 변경사항을 확인하세요.",
                "겨울 대비 건물 관리 관련 법규를 점검하세요.",
                "추석 연휴 관련 근로기준법 적용사항을 확인하세요."
            ],
            'winter': [
                "연말연시 보너스 관련 근로기준법을 확인하세요.",
                "새해 사업 계획 수립 시 관련 법규를 검토하세요.",
                "겨울철 안전사고 예방을 위한 법적 의무사항을 점검하세요."
            ]
        }
        
        return random.choice(tips.get(season, tips['spring']))

# 테스트 함수
if __name__ == "__main__":
    generator = GreetingGenerator()
    
    print("=== 인사말 생성 테스트 ===")
    
    print("\n1. 기본 인사말:")
    basic_greeting = generator.generate_greeting()
    print(basic_greeting)
    
    print("\n2. 사용자 메시지 포함:")
    custom_greeting = generator.generate_greeting(
        custom_message="3월 새학기를 맞아 새로운 마음으로 인사드립니다."
    )
    print(custom_greeting)
    
    print("\n3. 완전한 인사말 (이미지 포함):")
    complete_greeting = generator.generate_complete_greeting(
        custom_message="따뜻한 봄날 인사드립니다.",
        include_image=True
    )
    print("HTML 생성 완료 (이미지 포함)")
    
    print("\n4. 계절별 팁:")
    tip = generator.generate_seasonal_tips()
    print(f"💡 {tip}")
    
    print("\n5. 이메일 서명:")
    signature = generator.generate_email_signature()
    print(f"✨ {signature}")
    
    print("\n=== 테스트 완료 ===")