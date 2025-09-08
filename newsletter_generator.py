from datetime import datetime
from config import COMPANY_CONFIG
from utils import get_font_css, get_reliable_image

def create_html_newsletter(news_items, custom_message=""):
    """모바일 최적화되고 AI 메시지가 통합된 HTML 뉴스레터 생성"""
    
    font_style = COMPANY_CONFIG.get('font_style', 'pretendard')
    font_css = get_font_css(font_style)
    
    # 이미지 가져오기 (항상 성공)
    hero_image_url = None
    if COMPANY_CONFIG.get('use_newsletter_images', True):
        hero_image_url = get_reliable_image(600, 200)
    
    # 인사말과 AI 메시지 통합
    base_greeting = COMPANY_CONFIG['default_greeting']
    if custom_message:
        # AI 생성 메시지를 자연스럽게 인사말에 통합
        integrated_greeting = f"{base_greeting}<br><br>{custom_message}<br><br>항상 정확하고 신뢰할 수 있는 법률 정보로 여러분과 함께하겠습니다."
    else:
        integrated_greeting = f"{base_greeting}<br>항상 정확하고 신뢰할 수 있는 법률 정보로 여러분과 함께하겠습니다."
    
    # 웹메일 호환성을 극대화한 헤더 이미지 생성
    if hero_image_url:
        if hero_image_url.startswith('data:'):
            # SVG Data URL인 경우 - 완전한 가운데 정렬 보장
            hero_html = f'''
            <table width="100%" cellpadding="0" cellspacing="0" border="0" style="margin: 0; padding: 0;">
                <tr>
                    <td align="center" valign="middle" style="padding: 0; margin: 0;">
                        <table width="100%" cellpadding="0" cellspacing="0" border="0" style="background: url('{hero_image_url}'); background-size: cover; background-position: center; max-width: 680px;">
                            <tr>
                                <td height="200" align="center" valign="middle" style="text-align: center; padding: 20px;">
                                    <div style="text-align: center;">
                                        <!-- SVG에 텍스트가 포함되어 있음 -->
                                    </div>
                                </td>
                            </tr>
                        </table>
                    </td>
                </tr>
            </table>
            '''
        else:
            # 외부 이미지 URL인 경우 - 텍스트 오버레이와 완전한 가운데 정렬
            hero_html = f'''
            <table width="100%" cellpadding="0" cellspacing="0" border="0" style="margin: 0; padding: 0;">
                <tr>
                    <td align="center" valign="middle" style="padding: 0; margin: 0;">
                        <table width="100%" cellpadding="0" cellspacing="0" border="0" style="background: linear-gradient(rgba(102, 126, 234, 0.8), rgba(118, 75, 162, 0.8)), url('{hero_image_url}'); background-size: cover; background-position: center; max-width: 680px;">
                            <tr>
                                <td height="200" align="center" valign="middle" style="text-align: center; padding: 20px;">
                                    <!--[if mso]>
                                    <table width="100%" cellpadding="0" cellspacing="0" border="0">
                                        <tr>
                                            <td align="center" valign="middle">
                                    <![endif]-->
                                    <div style="text-align: center; width: 100%;">
                                        <h2 style="margin: 0 auto; font-size: 28px; font-weight: bold; text-shadow: 2px 2px 4px rgba(0,0,0,0.7); color: white; text-align: center; display: block; width: 100%; max-width: 400px;">
                                            법률 뉴스레터
                                        </h2>
                                        <p style="margin: 10px auto 0 auto; font-size: 16px; opacity: 0.95; text-shadow: 1px 1px 2px rgba(0,0,0,0.7); color: white; text-align: center; display: block; width: 100%; max-width: 300px;">
                                            신뢰할 수 있는 법률 정보
                                        </p>
                                    </div>
                                    <!--[if mso]>
                                            </td>
                                        </tr>
                                    </table>
                                    <![endif]-->
                                </td>
                            </tr>
                        </table>
                    </td>
                </tr>
            </table>
            '''
    else:
        # 이미지 없는 경우의 기본 헤더 - 완전한 가운데 정렬 보장
        hero_html = '''
        <table width="100%" cellpadding="0" cellspacing="0" border="0" style="margin: 0; padding: 0;">
            <tr>
                <td align="center" valign="middle" style="padding: 0; margin: 0;">
                    <table width="100%" cellpadding="0" cellspacing="0" border="0" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); max-width: 680px;">
                        <tr>
                            <td height="200" align="center" valign="middle" style="text-align: center; padding: 20px;">
                                <!--[if mso]>
                                <table width="100%" cellpadding="0" cellspacing="0" border="0">
                                    <tr>
                                        <td align="center" valign="middle">
                                <![endif]-->
                                <div style="text-align: center; width: 100%;">
                                    <h2 style="margin: 0 auto; font-size: 28px; font-weight: bold; color: white; text-align: center; display: block; width: 100%; max-width: 400px;">
                                        법률 뉴스레터
                                    </h2>
                                    <p style="margin: 10px auto 0 auto; font-size: 16px; opacity: 0.95; color: white; text-align: center; display: block; width: 100%; max-width: 300px;">
                                        신뢰할 수 있는 법률 정보
                                    </p>
                                </div>
                                <!--[if mso]>
                                        </td>
                                    </tr>
                                </table>
                                <![endif]-->
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
        '''
    
    # 사무실 정보
    office_info = COMPANY_CONFIG['office_info']
    today = datetime.now().strftime('%Y년 %m월 %d일')
    
    # 웹메일 호환성을 위한 테이블 기반 레이아웃 (개선된 버전)
    html_template = f"""
    <!DOCTYPE html>
    <html lang="ko">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <meta http-equiv="X-UA-Compatible" content="IE=edge">
        <title>{COMPANY_CONFIG['company_name']} 뉴스레터</title>
        <style>
            {font_css}
            
            /* 웹메일 호환성을 위한 기본 스타일 리셋 */
            body, table, td, p, a, li, blockquote {{
                -webkit-text-size-adjust: 100%;
                -ms-text-size-adjust: 100%;
            }}
            
            table, td {{
                mso-table-lspace: 0pt;
                mso-table-rspace: 0pt;
            }}
            
            img {{
                -ms-interpolation-mode: bicubic;
                border: 0;
                height: auto;
                line-height: 100%;
                outline: none;
                text-decoration: none;
                max-width: 100%;
            }}
            
            body {{
                margin: 0 !important;
                padding: 0 !important;
                background-color: #ffffff;
                color: #333333;
                line-height: 1.7;
                font-size: 15px;
                width: 100% !important;
                height: 100% !important;
            }}
            
            /* 가운데 정렬을 위한 강화된 스타일 */
            .center-wrapper {{
                width: 100% !important;
                text-align: center !important;
                margin: 0 auto !important;
            }}
            
            .center-content {{
                margin: 0 auto !important;
                text-align: center !important;
                display: block !important;
                width: 100% !important;
            }}
            
            /* 컨테이너 스타일 */
            .email-container {{
                max-width: 680px;
                margin: 0 auto;
                background-color: #ffffff;
                text-align: center;
            }}
            
            /* 모바일 우선 반응형 스타일 */
            .content-table {{
                width: 100%;
                max-width: 680px;
                margin: 0 auto;
            }}
            
            .main-content {{
                padding: 40px 30px;
            }}
            
            /* 제목 스타일 - 가운데 정렬 강화 */
            .header-title {{
                font-size: 42px;
                font-weight: 700;
                margin: 0 auto 8px auto;
                color: #000000;
                letter-spacing: -1px;
                text-align: center;
                display: block;
                width: 100%;
            }}
            
            .header-subtitle {{
                font-size: 16px;
                color: #666666;
                margin: 0 auto;
                font-weight: 400;
                text-align: center;
                display: block;
                width: 100%;
            }}
            
            /* 인사말 스타일 */
            .greeting-text {{
                font-size: 16px;
                line-height: 1.8;
                color: #333333;
                margin: 30px 0 40px 0;
                text-align: left;
            }}
            
            /* 뉴스 섹션 스타일 */
            .news-divider {{
                width: 100%;
                height: 1px;
                background-color: #333333;
                margin: 30px 0 25px 0;
                position: relative;
            }}
            
            .section-number {{
                position: absolute;
                left: 0;
                top: -15px;
                background-color: #ffffff;
                width: 30px;
                height: 30px;
                border: 2px solid #333333;
                border-radius: 50%;
                text-align: center;
                line-height: 26px;
                font-weight: 700;
                font-size: 14px;
                color: #333333;
            }}
            
            /* 뉴스 아이템 스타일 */
            .news-item {{
                margin: 25px 0;
                padding: 0;
                text-align: left;
            }}
            
            .news-title {{
                font-size: 18px;
                font-weight: 600;
                color: #000000;
                text-decoration: none;
                line-height: 1.4;
                margin-bottom: 8px;
                display: block;
            }}
            
            .news-title:hover {{
                color: #333333;
                text-decoration: underline;
            }}
            
            .news-meta {{
                font-size: 13px;
                color: #888888;
                margin-top: 8px;
            }}
            
            /* 푸터 스타일 */
            .footer {{
                background-color: #f8f9fa;
                padding: 30px;
                text-align: center;
            }}
            
            .office-info {{
                background-color: #ffffff;
                padding: 20px;
                margin: 20px 0;
                text-align: left;
                border-radius: 5px;
                border: 1px solid #e0e0e0;
            }}
            
            .office-info h3 {{
                margin: 0 0 12px 0;
                font-size: 16px;
                font-weight: 600;
                color: #333333;
            }}
            
            .office-info p {{
                margin: 6px 0;
                font-size: 14px;
                color: #666666;
            }}
            
            .footer-text {{
                font-size: 13px;
                color: #888888;
                margin: 15px 0;
                line-height: 1.6;
                text-align: center;
            }}
            
            .unsubscribe {{
                margin-top: 20px;
                padding-top: 15px;
                border-top: 1px solid #e0e0e0;
                text-align: center;
            }}
            
            .unsubscribe a {{
                color: #333333;
                text-decoration: underline;
            }}
            
            /* 모바일 최적화 */
            @media only screen and (max-width: 600px) {{
                .email-container {{
                    width: 100% !important;
                }}
                
                .main-content {{
                    padding: 25px 20px !important;
                }}
                
                .header-title {{
                    font-size: 32px !important;
                }}
                
                .news-title {{
                    font-size: 16px !important;
                }}
                
                .section-number {{
                    display: none;
                }}
                
                .news-divider {{
                    margin: 20px 0 15px 0 !important;
                }}
                
                /* 모바일에서 헤더 텍스트 크기 조정 */
                .hero-title {{
                    font-size: 24px !important;
                }}
                
                .hero-subtitle {{
                    font-size: 14px !important;
                }}
            }}
            
            /* Outlook 호환성 강화 */
            @media screen and (-webkit-min-device-pixel-ratio: 0) {{
                .header-title {{
                    font-size: 42px !important;
                }}
            }}
            
            /* 웹메일별 호환성 */
            .ReadMsgBody {{
                width: 100%;
            }}
            
            .ExternalClass {{
                width: 100%;
            }}
            
            .ExternalClass, .ExternalClass p, .ExternalClass span, .ExternalClass font, .ExternalClass td, .ExternalClass div {{
                line-height: 100%;
            }}
        </style>
        <!--[if mso]>
        <style type="text/css">
            .fallback-text {{
                font-family: Arial, sans-serif !important;
            }}
            .hero-title {{
                font-size: 28px !important;
                text-align: center !important;
            }}
            .hero-subtitle {{
                font-size: 16px !important;
                text-align: center !important;
            }}
        </style>
        <![endif]-->
    </head>
    <body>
        <div class="center-wrapper">
            <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="margin: 0 auto;">
                <tr>
                    <td align="center" style="padding: 0;">
                        <div class="email-container">
                            <!-- 헤더 이미지 -->
                            {hero_html}
                            
                            <!-- 메인 콘텐츠 -->
                            <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="max-width: 680px; margin: 0 auto;">
                                <tr>
                                    <td class="main-content">
                                        <!-- 제목 -->
                                        <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
                                            <tr>
                                                <td align="center" style="text-align: center; margin-bottom: 40px; padding-bottom: 20px; border-bottom: 1px solid #e0e0e0;">
                                                    <h1 class="header-title fallback-text center-content">Newsletter</h1>
                                                    <p class="header-subtitle fallback-text center-content">법률 정보 · {today}</p>
                                                </td>
                                            </tr>
                                        </table>
                                        
                                        <!-- 인사말 (AI 메시지 통합) -->
                                        <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
                                            <tr>
                                                <td class="greeting-text fallback-text">
                                                    {integrated_greeting}
                                                </td>
                                            </tr>
                                        </table>
                                        
                                        <!-- 뉴스 섹션 -->
                                        <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
                                            <tr>
                                                <td>
                                                    {generate_news_items_html_mobile(news_items)}
                                                </td>
                                            </tr>
                                        </table>
                                    </td>
                                </tr>
                            </table>
                            
                            <!-- 푸터 -->
                            <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="max-width: 680px; margin: 0 auto;">
                                <tr>
                                    <td class="footer">
                                        <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
                                            <tr>
                                                <td>
                                                    <div class="office-info">
                                                        <h3>{COMPANY_CONFIG['company_name']}</h3>
                                                        <p>이메일: {COMPANY_CONFIG['company_email']}</p>
                                                        <p>전화: {office_info['phone']}</p>
                                                        <p>주소: {office_info['address']}</p>
                                                        <p>운영시간: {office_info['business_hours']}</p>
                                                        {f"<p>웹사이트: {office_info['website']}</p>" if office_info.get('website') else ''}
                                                    </div>
                                                    
                                                    <div class="footer-text">
                                                        <p><strong>{COMPANY_CONFIG['footer_message']}</strong></p>
                                                        <p>본 뉴스레터는 법률 정보 제공을 목적으로 발송됩니다.</p>
                                                    </div>
                                                    
                                                    <div class="unsubscribe">
                                                        <p class="footer-text">
                                                            뉴스레터 수신을 중단하시려면 
                                                            <a href="mailto:{COMPANY_CONFIG['company_email']}?subject=수신거부신청">여기를 클릭</a>하여 신청해주세요.
                                                        </p>
                                                        <p style="font-size: 11px; color: #aaa; margin-top: 15px;">
                                                            © 2024 {COMPANY_CONFIG['company_name']}. All rights reserved.
                                                        </p>
                                                    </div>
                                                </td>
                                            </tr>
                                        </table>
                                    </td>
                                </tr>
                            </table>
                        </div>
                    </td>
                </tr>
            </table>
        </div>
    </body>
    </html>
    """
    return html_template

def generate_news_items_html_mobile(news_items):
    """모바일 최적화된 뉴스 아이템 HTML 생성"""
    html = ""
    
    for i, item in enumerate(news_items, 1):
        html += f"""
        <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="margin: 25px 0;">
            <tr>
                <td>
                    <div class="news-divider">
                        <div class="section-number">{i}</div>
                    </div>
                    <div class="news-item">
                        <a href="{item['url']}" class="news-title fallback-text" style="color: #000000; text-decoration: none;">{item['title']}</a>
                        <div class="news-meta fallback-text">
                            출처: {item.get('source', '자동수집')} · {item['date']}
                        </div>
                    </div>
                </td>
            </tr>
        </table>
        """
    
    return html

def generate_news_items_html(news_items):
    """심플한 뉴스 아이템 HTML 생성 (기존 호환성)"""
    html = ""
    
    for i, item in enumerate(news_items, 1):
        html += f"""
        <div class="section-divider">
            <div class="section-number">{i}</div>
        </div>
        <div class="news-item">
            <a href="{item['url']}" class="news-title">{item['title']}</a>
            <div class="news-meta">
                출처: {item.get('source', '자동수집')} · {item['date']}
            </div>
        </div>
        """
    
    return html