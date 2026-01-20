# run.py (v4.8 - 안정성 강화 및 앱 모드 실행)
import streamlit.web.cli as stcli
import os, sys
import subprocess
import webbrowser
from threading import Timer

def resolve_path(path):
    if getattr(sys, "frozen", False):
        basedir = sys._MEIPASS
    else:
        basedir = os.path.dirname(__file__)
    return os.path.join(basedir, path)

def open_browser():
    # [수정] 일반 탭이 아니라 '앱 모드'로 열기 시도 (크롬/엣지 기준)
    # 이렇게 하면 주소창이 없고 진짜 프로그램처럼 보입니다.
    # 만약 크롬이 없으면 기본 브라우저로 열립니다.
    url = "http://localhost:8501"
    
    # 크롬 앱 모드 시도 (Windows & macOS)
    chrome_paths = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        r"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" # macOS path
    ]
    
    chrome_found = False
    for path in chrome_paths:
        if os.path.exists(path):
            try:
                # 앱 모드로 실행 (--app 옵션)
                subprocess.Popen([path, f'--app={url}'])
                chrome_found = True
                break
            except: pass
    
    # 크롬을 못 찾았거나 실행 실패하면 그냥 기본 브라우저 띄우기
    if not chrome_found:
        webbrowser.open_new(url)

if __name__ == "__main__":
    # subprocess는 파일 상단에서 import됨
    
    # 환경설정
    os.environ["STREAMLIT_SERVER_HEADLESS"] = "true"
    os.environ["STREAMLIT_SERVER_MAX_UPLOAD_SIZE"] = "500"
    
    # [중요] 방화벽 문제 최소화를 위해 localhost 강제 지정
    # 이 설정이 없으면 가끔 외부 IP를 잡으려다 차단당해 흰 화면이 뜹니다.
    sys.argv = [
        "streamlit",
        "run",
        resolve_path("app.py"),
        "--global.developmentMode=false",
        "--server.address=localhost",  # [추가] 오직 내 컴퓨터에서만 접속 허용
        "--server.port=8501",          # [추가] 포트 고정
        "--browser.serverAddress=localhost", # [추가] 브라우저가 찾아갈 주소 명시
    ]
    
    # 2초 뒤 브라우저 실행 (서버 켜지는 시간 확보를 위해 1.5 -> 2.0초로 늘림)
    Timer(2.0, open_browser).start()
    
    # 실행
    sys.exit(stcli.main())