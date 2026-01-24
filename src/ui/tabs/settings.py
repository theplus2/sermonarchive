import streamlit as st
import os
import time
import subprocess
import tkinter as tk
from tkinter import filedialog
from src.core import processor

def render_settings(config, save_config_func, APP_DATA_DIR, DB_PATH):
    st.title("⚙️ 설정 및 동기화")
    t1, t2 = st.tabs(["폴더/동기화", "데이터 관리"])
    with t1:
        cur = config.get("target_folder","")
        st.info(f"현재 폴더: {cur}")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("📂 폴더 변경"):
                def select_folder_safe():
                    try:
                        root = tk.Tk(); root.withdraw(); root.wm_attributes('-topmost', 1)
                        folder_path = filedialog.askdirectory(master=root)
                        return folder_path
                    except: return None
                    finally:
                        try: root.destroy() 
                        except: pass
                p = select_folder_safe()
                if p: 
                    config['target_folder'] = p
                    save_config_func(config)
                    st.success(f"폴더가 변경되었습니다: {p}")
                    time.sleep(0.5); st.rerun()
                else: st.info("폴더 선택이 취소되었습니다.")
        with c2:
            if st.button("🔄 전체 동기화 (DB 업데이트)", type="primary"):
                if not cur: st.error("폴더 선택 필요")
                else:
                    bar=st.progress(0); txt=st.empty()
                    cnt, msg = processor.sync_files(cur, DB_PATH, bar.progress, txt.text)
                    bar.empty(); txt.empty()
                    st.success(msg)
    with t2:
        if st.button("데이터 폴더 열기"): subprocess.Popen(f'explorer "{APP_DATA_DIR}"')
        if st.button("DB 초기화 (삭제)", type="primary"):
            if os.path.exists(DB_PATH): os.remove(DB_PATH)
            processor.init_db(DB_PATH)
            st.success("초기화 완료")
