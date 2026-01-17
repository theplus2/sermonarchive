import streamlit as st
import json
import os
import sys
import processor
import time
import styles # 분리한 스타일 파일
import tabs   # 분리한 기능 파일
import streamlit.components.v1 as components

# ==========================================
# ⚙️ 설정 및 초기화
# ==========================================
st.set_page_config(layout="wide", page_title="설교자의 서재 v5.0.5")

# 경로 설정 (크로스 플랫폼 지원)
import platform
system_os = platform.system()

if system_os == "Windows":
    APP_DATA_DIR = os.path.join(os.path.expanduser("~"), "AppData", "Local", "SermonLibrary")
elif system_os == "Darwin": # macOS
    APP_DATA_DIR = os.path.join(os.path.expanduser("~"), "Library", "Application Support", "SermonLibrary")
else: # Linux/Other
    APP_DATA_DIR = os.path.join(os.path.expanduser("~"), ".sermonlibrary")

if not os.path.exists(APP_DATA_DIR): os.makedirs(APP_DATA_DIR)
CONFIG_FILE = os.path.join(APP_DATA_DIR, "config.json")
DB_PATH = os.path.join(APP_DATA_DIR, "library.db")
DRAFTS_DIR = os.path.join(APP_DATA_DIR, "drafts")

# DB 초기화
processor.init_db(DB_PATH)

# ==========================================
# 🎨 공통 스타일 적용
# ==========================================
styles.apply_global_styles()

# 사이드바 - 네비게이션 메뉴
with st.sidebar:
    st.title("📚 메뉴")
    
    # 홈 버튼
    if st.button("🏠 홈", use_container_width=True):
        st.session_state['mode'] = 'main_menu'
        st.rerun()
    
    st.divider()
    
    # 메인 메뉴들
    if st.button("✍️ 작업실", use_container_width=True):
        st.session_state['mode'] = 'workspace'
        st.rerun()
    
    if st.button("📅 연대기", use_container_width=True):
        st.session_state['mode'] = 'chronicle'
        st.rerun()
    
    if st.button("📊 통계", use_container_width=True):
        st.session_state['mode'] = 'statistics'
        st.rerun()
    
    if st.button("⚙️ 설정", use_container_width=True):
        st.session_state['mode'] = 'settings'
        st.rerun()
    
    if st.button("❓ 도움말", use_container_width=True):
        st.session_state['mode'] = 'help'
        st.rerun()
    
    st.divider()
    
    
    if st.button("❌ 프로그램 완전 종료", type="primary", use_container_width=True):
        st.warning("종료 중입니다...")
        components.html(
            """<script>window.parent.window.close(); window.close();</script>""", 
            height=0, width=0
        )
        time.sleep(1)
        if system_os == "Windows":
            os.system(f"taskkill /F /PID {os.getpid()}")
        else:
            import signal
            os.kill(os.getpid(), signal.SIGTERM)

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f: return json.load(f)
    return {"target_folder": "sermons", "ui_height": 650}

def save_config(c):
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f: json.dump(c, f, indent=4)

config = load_config()

if 'startup_sync_done' not in st.session_state:
    target = config.get("target_folder")
    if target and os.path.exists(target):
        cnt, msg = processor.sync_files(target)
        if cnt > 0: st.toast(f"🎉 새 설교 {cnt}편 업데이트 완료!")
    st.session_state['startup_sync_done'] = True

if 'mode' not in st.session_state: st.session_state['mode'] = 'main_menu'

# ==========================================
# 🚀 메인 라우팅 (화면 전환)
# ==========================================

# 공통 푸터 함수
def render_footer():
    st.markdown("---")
    st.caption("Developed by 윤영천 목사 (theplus2@gmail.com)")

if st.session_state['mode'] == 'main_menu':
    styles.apply_home_styles()
    st.title("✠️ 설교자의 서재 v5.0.5")
    st.caption("Developed by **잠실한빛교회 윤영천 목사** (theplus2@gmail.com)")
    st.divider()
    
    # 홈 화면 4x2 그리드
    c1,c2,c3,c4 = st.columns(4, gap="medium")
    with c1:
        if st.button("✍️\n\n**작업실**\n설교 작성"): st.session_state['mode']='workspace'; st.rerun()
    with c2:
        if st.button("📅\n\n**연대기**\n목록 & 엑셀"): st.session_state['mode']='chronicle'; st.rerun()
    with c3:
        if st.button("📊\n\n**통계**\n편식 분석"): st.session_state['mode']='statistics'; st.rerun()
    with c4:
        if st.button("⚙️\n\n**설정**\n데이터 관리"): st.session_state['mode']='settings'; st.rerun()
    
    st.write("")
    c5,c6,c7,c8 = st.columns(4, gap="medium")
    with c5:
        if st.button("❓\n\n**도움말**\n사용법"): st.session_state['mode']='help'; st.rerun()
    
    render_footer()

elif st.session_state['mode'] == 'workspace':
    styles.apply_subpage_styles()
    tabs.render_workspace(config, DRAFTS_DIR)
    render_footer()

elif st.session_state['mode'] == 'chronicle':
    styles.apply_subpage_styles()
    tabs.render_chronicle()
    render_footer()

elif st.session_state['mode'] == 'statistics':
    styles.apply_subpage_styles()
    tabs.render_statistics()
    render_footer()

elif st.session_state['mode'] == 'settings':
    styles.apply_settings_styles()
    tabs.render_settings(config, save_config, APP_DATA_DIR, DB_PATH)
    render_footer()

elif st.session_state['mode'] == 'help':
    styles.apply_subpage_styles()
    tabs.render_help()
    render_footer()