# mailer.py
import os, smtplib, re, unicodedata
from email.header import Header
from email.utils import formataddr, parseaddr
from email.message import EmailMessage

SMTP_HOST = os.getenv("SMTP_HOST", "localhost")
SMTP_PORT = int(os.getenv("SMTP_PORT", "1025"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASS = os.getenv("SMTP_PASS", "")
FROM_EMAIL = os.getenv("FROM_EMAIL", "no-reply@example.com")
FROM_NAME  = os.getenv("FROM_NAME", "Newsletter")

# -------- 유틸: NBSP/유니코드 공백 제거 & 이메일 정규화 --------
_WS_RE = re.compile(r"[\u00a0\u2000-\u200b\u202f\u205f\u3000]")  # NBSP/좁은공백 등
def _norm_ws(s: str) -> str:
    s = s or ""
    s = _WS_RE.sub(" ", s)         # 특수 공백 → 일반 공백
    s = unicodedata.normalize("NFKC", s).strip()
    return s

def _ascii_email(email: str) -> str:
    """
    메일 주소는 SMTP envelope에서 ASCII만 허용되는 경우가 많음.
    - 공백/제어문자 제거
    - parseaddr로 주소만 추출
    - 남은 문자가 모두 ASCII인지 확인
    """
    name, addr = parseaddr(_norm_ws(email))
    addr = addr.replace(" ", "")
    # 아주 가끔 붙는 보이지 않는 제로폭 문자 제거
    addr = re.sub(r"[\u200b-\u200d\ufeff]", "", addr)
    # 주소 자체에 한글/이모지 등 있으면 오류 반환
    try:
        addr.encode("ascii")
    except UnicodeEncodeError:
        raise ValueError(f"이메일 주소에 비ASCII 문자가 포함되어 있습니다: {repr(addr)}")
    return addr

def send_email(to_email: str, subject: str, html: str, text_fallback: str | None = None):
    # 1) 주소/제목 정리
    envelope_from = _ascii_email(FROM_EMAIL)
    envelope_to   = _ascii_email(to_email)

    safe_subject = _norm_ws(subject or "")
    html = html or ""
    text = _norm_ws(text_fallback or "HTML을 지원하지 않는 클라이언트를 위한 텍스트 본문입니다.")

    # 2) EmailMessage로 UTF-8 헤더/본문 생성
    msg = EmailMessage()
    msg["Subject"] = Header(safe_subject, "utf-8")
    # 표시용 From(헤더)은 이름에 한글/이모지 가능 (Header로 안전 인코딩)
    display_name = str(Header(_norm_ws(FROM_NAME), "utf-8"))
    msg["From"] = formataddr((display_name, envelope_from))
    msg["To"] = envelope_to

    msg.set_content(text, charset="utf-8")
    msg.add_alternative(html, subtype="html", charset="utf-8")

    # 3) SMTP 연결 & 전송
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
            server.login(_norm_ws(SMTP_USER), _norm_ws(SMTP_PASS))

        # 서버가 SMTPUTF8을 지원하면 사용 (헤더에 UTF-8이 있을 때 안전)
        mail_opts = []
        try:
            if server.has_extn("smtputf8"):
                mail_opts.append("SMTPUTF8")
        except Exception:
            pass

        # envelope 주소는 ASCII(위에서 강제)로 전달
        server.send_message(msg, from_addr=envelope_from, to_addrs=[envelope_to], mail_options=mail_opts)
    finally:
        try:
            server.quit()
        except Exception:
            pass
