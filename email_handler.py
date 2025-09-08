import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from config import COMPANY_CONFIG
from utils import simple_clean

def auto_configure_smtp():
    """앱 시작시 자동으로 SMTP 설정을 로드"""
    auto_settings = {
        'server': COMPANY_CONFIG['smtp_server'],
        'port': COMPANY_CONFIG['smtp_port'],
        'email': COMPANY_CONFIG['company_email'],
        'password': COMPANY_CONFIG['company_password'],
        'sender_name': COMPANY_CONFIG['company_name']
    }
    return auto_settings

def send_newsletter(recipients, subject, html_content, smtp_settings):
    """뉴스레터 발송"""
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

def test_smtp_connection(smtp_settings):
    """SMTP 연결 테스트"""
    try:
        clean_server = simple_clean(smtp_settings['server'])
        clean_email = simple_clean(smtp_settings['email']).replace(' ', '')
        clean_password = simple_clean(smtp_settings['password'])
        
        server = smtplib.SMTP(clean_server, smtp_settings['port'])
        server.starttls()
        server.login(clean_email, clean_password)
        server.quit()
        
        return True, "SMTP 연결 성공"
    except Exception as e:
        return False, f"SMTP 연결 실패: {str(e)}"

def send_test_email(recipient, smtp_settings):
    """테스트 이메일 발송"""
    try:
        test_subject = f"[{COMPANY_CONFIG['company_name']}] 테스트 메일"
        test_content = f"""
        <html>
        <body>
            <h2>테스트 메일</h2>
            <p>안녕하세요! {COMPANY_CONFIG['company_name']}입니다.</p>
            <p>이메일 발송 시스템이 정상적으로 작동하고 있습니다.</p>
            <p>이 메일은 테스트 목적으로 발송되었습니다.</p>
            <hr>
            <p><small>본 메일은 테스트용이므로 답장하지 마세요.</small></p>
        </body>
        </html>
        """
        
        sent_count, failed_emails = send_newsletter(
            [recipient], test_subject, test_content, smtp_settings
        )
        
        if sent_count > 0:
            return True, "테스트 메일 발송 성공"
        else:
            return False, f"테스트 메일 발송 실패: {failed_emails[0] if failed_emails else '알 수 없는 오류'}"
            
    except Exception as e:
        return False, f"테스트 메일 발송 중 오류: {str(e)}"