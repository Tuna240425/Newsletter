# app/services/mailer.py
import os, smtplib, re
from email.header import Header
from email.utils import formataddr
from email.message import EmailMessage

SMTP_HOST = os.getenv("SMTP_HOST", "localhost")
SMTP_PORT = int(os.getenv("SMTP_PORT", "1025"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASS = os.getenv("SMTP_PASS", "")
FROM_EMAIL = os.getenv("FROM_EMAIL", "no-reply@example.com")
FROM_NAME  = os.getenv("FROM_NAME", "Newsletter")

_nbsp_re = re.compile(r"\u00a0")  # NBSP
def norm(s: str) -> str:
    # NBSP → 일반 공백, 양끝 공백 제거
    return _nbsp_re.sub(" ", s or "").strip()

def send_email(to_email: str, subject: str, html: str, text_fallback: str | None = None):
    # 1) 값 정리(특히 NBSP 제거)
    to_email = norm(to_email)
    subject  = norm(subject)
    html     = html or ""
    text     = text_fallback or "HTML 본문을 지원하지 않는 클라이언트를 위한 텍스트 본문입니다."

    # 2) EmailMessage로 멀티파트/UTF-8 안전 생성
    msg = EmailMessage()
    # 헤더: UTF-8로 인코딩 (encoded-word)
    msg["Subject"] = Header(subject, "utf-8")
    msg["From"]    = formataddr((str(Header(norm(FROM_NAME), "utf-8")), FROM_EMAIL))
    msg["To"]      = to_email

    # 본문: text + html 대안
    msg.set_content(norm(text), charset="utf-8")
    msg.add_alternative(html, subtype="html", charset="utf-8")

    # 3) 전송
    if SMTP_PORT == 465:
        server = smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT)
    else:
        server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)

    try:
        server.ehlo()
        if SMTP_PORT == 587:
            server.starttls()
            server.ehlo()
        if SMTP_USER:
            server.login(SMTP_USER, SMTP_PASS)
        # SMTPUTF8 확장: 일부 서버에서만 지원 → 자동 처리 (EmailMessage는 헤더 인코딩을 해줌)
        server.send_message(msg)  # ← sendmail 대신 send_message를 쓰면 헤더 인코딩 처리 안전
    finally:
        server.quit()
