# launcher.py
import sys
import os
import time
import socket
import subprocess
import webbrowser
from pathlib import Path

APP_FILE = "newsletter_app_sqlite.py"

def find_free_port(preferred=8501, max_tries=20):
    # preferred부터 시작해서 비어있는 포트 찾기
    port = preferred
    for _ in range(max_tries):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.5)
            if s.connect_ex(("127.0.0.1", port)) != 0:
                return port
        port += 1
    return preferred  # 못 찾으면 그냥 preferred

def main():
    # PyInstaller로 묶였을 때 현재 폴더를 실행 파일 위치로 고정
    os.chdir(Path(__file__).resolve().parent)

    port = find_free_port(8501)
    url = f"http://localhost:{port}"

    # Streamlit 서버 실행 (headless)
    cmd = [
        sys.executable, "-m", "streamlit", "run", APP_FILE,
        "--server.headless", "true",
        "--server.port", str(port)
    ]
    # 콘솔창 숨기고 싶으면 creationflags 사용 (Windows 전용):
    creationflags = 0
    if os.name == "nt":
        creationflags = subprocess.CREATE_NO_WINDOW

    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        creationflags=creationflags
    )

    # 서버가 뜰 때까지 잠깐 대기 후 브라우저 오픈
    time.sleep(2.5)
    try:
        webbrowser.open(url, new=1)
    except Exception:
        pass

    # 서버 종료까지 대기
    try:
        proc.wait()
    except KeyboardInterrupt:
        proc.terminate()

if __name__ == "__main__":
    main()
