import streamlit as st
import json
import os
import random
import webbrowser
import pandas as pd
import tkinter as tk
from tkinter import filedialog
from wordcloud import WordCloud
from io import BytesIO
from docx import Document
import matplotlib.pyplot as plt
import sys
import subprocess
import processor # DB 엔진
import time
import streamlit.components.v1 as components

# ==========================================
# ⚙️ 설정 및 초기화
# ==========================================
st.set_page_config(layout="wide", page_title="설교자의 서재 v4.4")

# 경로 설정
APP_DATA_DIR = os.path.join(os.path.expanduser("~"), "AppData", "Local", "SermonLibrary")
if not os.path.exists(APP_DATA_DIR): os.makedirs(APP_DATA_DIR)
CONFIG_FILE = os.path.join(APP_DATA_DIR, "config.json")
DB_PATH = os.path.join(APP_DATA_DIR, "library.db")
DRAFTS_DIR = os.path.join(APP_DATA_DIR, "drafts")

# DB 초기화
processor.init_db(DB_PATH)

# ==========================================
# 🎨 공통 스타일 및 사이드바
# ==========================================
st.markdown("""
<style>
    /* 기본 폰트 */
    html, body, [class*="css"] {
        font-family: 'Malgun Gothic', sans-serif !important;
    }
    
    /* 사이드바 종료 버튼 */
    section[data-testid="stSidebar"] div.stButton > button {
        background-color: #ff4b4b !important; 
        color: white !important; 
        border: none !important;
        width: 100% !important;
        height: 3.5rem !important;
        aspect-ratio: auto !important;
        
        display: flex !important;
        align-items: center;
        justify-content: center;
        
        font-size: 1rem !important;
        font-weight: bold !important;
        padding: 0px 5px !important;
        margin-top: 10px;
    }

    /* 태그 및 배지 */
    .bible-tag { background-color: #e8f0fe; color: #1558d6; padding: 2px 8px; border-radius: 10px; font-weight: 700; font-size: 0.8em; }
    .date-badge { background-color: #f1f3f4; color: #3c4043; padding: 2px 6px; border-radius: 4px; font-weight: 600; font-size: 0.8em; border: 1px solid #dadce0; }
    
    /* 히트맵 스타일 */
    .heatmap-container { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 20px; }
    .heatmap-box {
        width: 70px; height: 70px; border-radius: 12px;
        display: flex; flex-direction: column; justify-content: center; align-items: center;
        text-align: center; font-size: 0.8rem; font-weight: bold;
        transition: transform 0.2s; box-shadow: 0 2px 4px rgba(0,0,0,0.05); border: 1px solid rgba(0,0,0,0.05); line-height: 1.2;
    }
    .heatmap-box:hover { transform: scale(1.15); z-index: 10; box-shadow: 0 6px 12px rgba(0,0,0,0.15); border: 1px solid #555; }
    .heatmap-count { font-size: 0.7rem; font-weight: normal; margin-top: 3px; opacity: 0.9; }
</style>
""", unsafe_allow_html=True)

# 사이드바
with st.sidebar:
    st.title("🚪 종료 메뉴")
    if st.button("❌ 프로그램 완전 종료", type="primary"):
        st.warning("종료 중입니다...")
        components.html(
            """<script>window.parent.window.close(); window.close();</script>""", 
            height=0, width=0
        )
        time.sleep(1)
        os.system(f"taskkill /F /PID {os.getpid()}")

BIBLE_ORDER = ["창세기","출애굽기","레위기","민수기","신명기","여호수아","사사기","룻기","사무엘상","사무엘하","열왕기상","열왕기하","역대상","역대하","에스라","느헤미야","에스더","욥기","시편","잠언","전도서","아가","이사야","예레미야","예레미야애가","에스겔","다니엘","호세아","요엘","아모스","오바댜","요나","미가","나훔","하박국","스바냐","학개","스가랴","말라기","마태복음","마가복음","누가복음","요한복음","사도행전","로마서","고린도전서","고린도후서","갈라디아서","에베소서","빌립보서","골로새서","데살로니가전서","데살로니가후서","디모데전서","디모데후서","디도서","빌레몬서","히브리서","야고보서","베드로전서","베드로후서","요한1서","요한2서","요한3서","유다서","요한계시록"]
OT_BOOKS = BIBLE_ORDER[:39]; NT_BOOKS = BIBLE_ORDER[39:]
OT_SET = set(OT_BOOKS); NT_SET = set(NT_BOOKS)

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
# 🏠 메인 메뉴
# ==========================================
if st.session_state['mode'] == 'main_menu':
    st.markdown("""
    <style>
        section[data-testid="stMain"] div.stButton > button {
            width: 250px !important; height: 250px !important;
            background-color: white !important; color: #333 !important;
            border: 2px solid #eee !important; border-radius: 20px !important;
            box-shadow: 0 4px 10px rgba(0,0,0,0.08) !important;
            display: flex !important; flex-direction: column !important; justify-content: center !important; align-items: center !important;
            white-space: pre-wrap !important; padding: 10px !important; transition: transform 0.2s !important; margin: auto !important; 
        }
        section[data-testid="stMain"] div.stButton > button:hover {
            transform: translateY(-8px) !important; border-color: #5D5CDE !important;
            background-color: #f8f9ff !important; box-shadow: 0 10px 20px rgba(0,0,0,0.15) !important; color: #5D5CDE !important;
        }
        section[data-testid="stMain"] div.stButton > button p::first-line {
            font-size: 3rem !important; line-height: 1.3 !important; margin-bottom: 10px !important;
        }
        section[data-testid="stMain"] div.stButton > button p {
            font-size: 1rem !important; line-height: 1.3 !important; font-weight: bold !important; margin: 0 !important;
        }
    </style>
    """, unsafe_allow_html=True)

    st.title("✝️ 설교자의 서재 v4.4")
    st.caption("Developed by **한빛교회 부목사 윤영천** (theplus2@gmail.com)")
    st.divider()
    
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


# ==========================================
# ✍️ 작업실 (v4.4 - 검색 페이징 기능 추가)
# ==========================================
elif st.session_state['mode'] == 'workspace':
    st.markdown("""
    <style>
    section[data-testid="stMain"] div.stButton > button {
        width: 100% !important; height: 3rem !important;
        background-color: #f0f2f6 !important; border: 1px solid #ddd !important;
        border-radius: 8px !important; display: flex !important; align-items: center !important; justify-content: center !important; font-size: 1rem !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    if st.button("🏠 홈으로 돌아가기", key="home"): st.session_state['mode']='main_menu'; st.rerun()
    st.divider()

    cl, cr = st.columns([6,4])
    with cl:
        st.header("🔍 설교 검색 (DB)")
        c1, c2 = st.columns([1,2])
        with c1: sel_bib = st.multiselect("성경", BIBLE_ORDER)
        with c2: q = st.text_input("검색어", placeholder="제목, 본문, 내용 검색...")
        st.write("")
        
        # [v4.4] 페이지 상태 관리
        if 'search_page' not in st.session_state: st.session_state['search_page'] = 0
        
        # [v4.4] 검색 조건이 바뀌면 페이지를 0으로 리셋 (새로운 검색)
        # 이를 위해 현재 검색 조건을 식별할 해시를 만듭니다.
        current_search_hash = f"{q}_{sel_bib}"
        if 'last_search_hash' not in st.session_state: st.session_state['last_search_hash'] = current_search_hash
        
        if st.session_state['last_search_hash'] != current_search_hash:
            st.session_state['search_page'] = 0
            st.session_state['last_search_hash'] = current_search_hash
        
        with st.container(height=config.get("ui_height", 650), border=True):
            if q or sel_bib:
                # 1. DB에서 전체 결과를 가져옴 (속도 빠름)
                all_rows = processor.search_sermons(q, sel_bib)
                total_count = len(all_rows)
                
                # 2. 페이징 로직 (한 페이지당 50개)
                PER_PAGE = 50
                start_idx = st.session_state['search_page'] * PER_PAGE
                end_idx = start_idx + PER_PAGE
                
                # 현재 페이지에 보여줄 데이터만 슬라이싱
                page_rows = all_rows[start_idx:end_idx]
                
                st.subheader(f"검색 결과: {total_count}건")
                if not all_rows: st.warning("결과가 없습니다.")
                else:
                    # 3. 결과 출력
                    for r in page_rows:
                        title = r['title']
                        date = r['date'] if r['date'] else ""
                        tags = "".join([f"<span class='bible-tag'>{t}</span>" for t in r['bible_tags'].split(',') if t])
                        cnt_info = f"({r['content'].count(q)}회)" if q else f"({date})"
                        
                        with st.expander(f"{title} {cnt_info}"):
                            st.markdown(f"<span class='date-badge'>{date}</span> {tags}", unsafe_allow_html=True)
                            st.divider()
                            lines = r['content'].split('\n')
                            for l in lines:
                                if l.strip():
                                    if q: st.markdown(l.replace(q, f":red[**{q}**]"))
                                    else: st.markdown(l)
                    
                    st.divider()
                    
                    # 4. 페이징 버튼 UI
                    # 컬럼을 나누어 [이전] [현재페이지] [다음] 배치
                    col_prev, col_info, col_next = st.columns([1, 2, 1])
                    
                    with col_prev:
                        if st.session_state['search_page'] > 0:
                            if st.button("◀️ 이전 50개", key="btn_prev"):
                                st.session_state['search_page'] -= 1
                                st.rerun()
                                
                    with col_info:
                        # 현재 페이지 정보 표시
                        total_pages = (total_count - 1) // PER_PAGE + 1
                        current_p = st.session_state['search_page'] + 1
                        st.markdown(f"<div style='text-align:center; color:#666;'><b>{current_p}</b> / {total_pages} 페이지</div>", unsafe_allow_html=True)
                        
                    with col_next:
                        if end_idx < total_count:
                            if st.button("다음 50개 ▶️", key="btn_next"):
                                st.session_state['search_page'] += 1
                                st.rerun()

            else:
                st.info("👈 검색어를 입력하면 2만 편의 설교 중 순식간에 찾아냅니다.")

    with cr:
        with st.container(height=config.get("ui_height", 650)+150, border=True):
            st.subheader("📝 스케치")
            if not os.path.exists(DRAFTS_DIR): os.makedirs(DRAFTS_DIR)
            dfs = [f for f in os.listdir(DRAFTS_DIR) if f.endswith(".txt")]
            sel_d = st.selectbox("불러오기", ["(새 설교)"]+dfs)
            tit,dt,svc,scr,cnt = "","","","",""
            if sel_d != "(새 설교)":
                try:
                    with open(os.path.join(DRAFTS_DIR, sel_d), "r", encoding="utf-8") as f:
                        ft = f.read()
                        if "---SEPARATOR---" in ft:
                            m, b = ft.split("---SEPARATOR---", 1); cnt=b.strip()
                            for l in m.split('\n'):
                                if l.startswith("Date:"): dt=l.replace("Date:","").strip()
                                elif l.startswith("Service:"): svc=l.replace("Service:","").strip()
                                elif l.startswith("Scripture:"): scr=l.replace("Scripture:","").strip()
                        else: cnt=ft
                        tit=sel_d.replace(".txt","")
                except: pass
            tit=st.text_input("제목",value=tit); dt=st.text_input("일시",value=dt)
            svc=st.text_input("예배",value=svc); scr=st.text_input("본문",value=scr)
            cnt=st.text_area("내용",value=cnt,height=400)
            if st.button("저장"):
                with open(os.path.join(DRAFTS_DIR, f"{tit}.txt"), "w", encoding="utf-8") as f:
                    f.write(f"Date: {dt}\nService: {svc}\nScripture: {scr}\n---SEPARATOR---\n{cnt}")
                st.success("저장됨"); st.rerun()

# ==========================================
# 📅 연대기
# ==========================================
elif st.session_state['mode'] == 'chronicle':
    st.markdown("""
    <style>
    section[data-testid="stMain"] div.stButton > button {
        width: 100% !important; height: 3rem !important;
        background-color: #f0f2f6 !important; border: 1px solid #ddd !important;
        border-radius: 8px !important; display: flex !important; align-items: center !important; justify-content: center !important; font-size: 1rem !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    if st.button("🏠 홈으로 돌아가기", key="home"): st.session_state['mode']='main_menu'; st.rerun()
    st.divider()

    st.title("📅 설교 연대기")
    
    rows = processor.get_all_sermons_metadata()
    if not rows: st.warning("데이터가 없습니다. 설정에서 동기화를 해주세요.")
    else:
        df = pd.DataFrame(rows, columns=['file_name','title','date','bible_tags','content'])
        years = sorted(list(set([d[:4] for d in df['date'] if d])), reverse=True)
        
        with st.expander("📥 엑셀 다운로드"):
            sel_ys = st.multiselect("연도", years)
            if st.button("파일 생성") and sel_ys:
                out = df[df['date'].str[:4].isin(sel_ys)]
                b = BytesIO()
                with pd.ExcelWriter(b, engine='xlsxwriter') as w: out.to_excel(w, index=False)
                b.seek(0)
                st.download_button("다운로드", b, "sermons.xlsx")
        
        st.divider()
        c1, c2 = st.columns([1,4])
        with c1: sel_y = st.radio("연도 선택", years)
        with c2:
            st.subheader(f"{sel_y}년 설교")
            ys = [r for r in rows if r['date'] and r['date'].startswith(sel_y)]
            for m in range(12,0,-1):
                ms = [r for r in ys if r['date'][5:7] == f"{m:02d}"]
                if ms:
                    with st.expander(f"📂 {sel_y}년 {m}월 ({len(ms)}편)", expanded=True):
                        for r in ms:
                            tags = "".join([f"[{t}]" for t in r['bible_tags'].split(',') if t])
                            label = f"{r['date']} | {r['title']}  {tags}"
                            
                            with st.expander(label):
                                st.markdown(f"**{r['title']}**")
                                st.divider()
                                for line in r['content'].split('\n'):
                                    if line.strip(): st.markdown(line)

# ==========================================
# 📊 통계
# ==========================================
elif st.session_state['mode'] == 'statistics':
    st.markdown("""
    <style>
    section[data-testid="stMain"] div.stButton > button {
        width: 100% !important; height: 3rem !important;
        background-color: #f0f2f6 !important; border: 1px solid #ddd !important;
        border-radius: 8px !important; display: flex !important; align-items: center !important; justify-content: center !important; font-size: 1rem !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    if st.button("🏠 홈으로 돌아가기", key="home"): st.session_state['mode']='main_menu'; st.rerun()
    st.divider()

    st.title("📊 통계 대시보드")
    total, no_tag, rows = processor.get_stats()
    ot_cnt, nt_cnt, cnts = 0, 0, {}
    
    for r in rows:
        tags = r['bible_tags'].split(',')
        if not r['bible_tags']: continue
        for t in tags:
            t = t.strip()
            if not t: continue
            book_name = t.split()[0] if ' ' in t else t
            for b in BIBLE_ORDER:
                if t.startswith(b):
                    book_name = b
                    break
            
            if book_name in BIBLE_ORDER:
                cnts[book_name] = cnts.get(book_name, 0) + 1
                if book_name in OT_SET: ot_cnt += 1
                elif book_name in NT_SET: nt_cnt += 1

    c1,c2,c3,c4 = st.columns(4)
    c1.metric("총 설교", f"{total}편")
    c2.metric("구약", f"{ot_cnt}회")
    c3.metric("신약", f"{nt_cnt}회")
    c4.metric("미분류", f"{no_tag}편")
    
    st.divider()
    
    st.subheader("🔥 성경 설교 히트맵 (Bible Heatmap)")
    st.caption("색이 진할수록 설교 빈도가 높습니다.")
    
    max_val = max(cnts.values()) if cnts else 1
    
    def render_heatmap_safe(book_list, theme='blue'):
        html = '<div class="heatmap-container">'
        for book in book_list:
            count = cnts.get(book, 0)
            
            if count == 0:
                bg_style = "background-color: #f8f9fa; color: #ccc; border: 1px solid #eee;"
            else:
                opacity = 0.1 + (count / max_val) * 0.9
                if theme == 'red':
                    base_rgb = "255, 75, 75"
                    dark_text = "#d32f2f"
                else:
                    base_rgb = "21, 88, 214"
                    dark_text = "#1558d6"

                text_color = "white" if opacity > 0.5 else dark_text
                bg_style = f"background-color: rgba({base_rgb}, {opacity:.2f}); color: {text_color}; border: 1px solid transparent;"

            html += f'<div class="heatmap-box" style="{bg_style}"><div>{book}</div><div class="heatmap-count">{count}</div></div>'
            
        html += '</div>'
        st.markdown(html, unsafe_allow_html=True)

    st.markdown("### 📜 구약 (Old Testament)")
    render_heatmap_safe(OT_BOOKS, theme='blue')
    
    st.markdown("### 🕊️ 신약 (New Testament)")
    render_heatmap_safe(NT_BOOKS, theme='red')
            
    st.divider()
    
    st.subheader("☁️ 핵심 키워드")
    if total > 0:
        with st.spinner("생성 중..."):
            text = processor.get_wordcloud_text()
            if text:
                stops = {'은','는','이','가','을','를','의','에','에서','로','으로','과','와','도','합니다','것입니다','있습니다','아니라','그','저','우리','나','너','여러분','할','수','있는','말씀','하나님','예수님','주님','제목','본문','설교','아멘','그리고','그러나','하지만','그런데','때문에','위해','통해','대한','모든','어떤','그래서','것','것이다','이러한','하는','줄','있을','한','수','등','더','그','때'}
                try:
                    wc = WordCloud(font_path="C:/Windows/Fonts/malgun.ttf", width=1200, height=400, background_color="white", stopwords=stops, max_words=100).generate(text)
                    st.image(wc.to_array(), use_container_width=True)
                except:
                    wc = WordCloud(width=1200, height=400, background_color="white", stopwords=stops, max_words=100).generate(text)
                    st.image(wc.to_array(), use_container_width=True)

# ==========================================
# ⚙️ 설정
# ==========================================
elif st.session_state['mode'] == 'settings':
    st.markdown("""
    <style>
    section[data-testid="stMain"] div.stButton > button {
        width: 100% !important; height: 3rem !important;
        background-color: #f0f2f6 !important; border: 1px solid #ddd !important;
        border-radius: 8px !important; color: #333 !important; display: flex !important; align-items: center !important; justify-content: center !important; font-size: 1rem !important;
    }
    section[data-testid="stMain"] div.stButton > button[kind="primary"] {
        background-color: #FF4B4B !important; color: white !important; border: none !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    if st.button("🏠 홈으로 돌아가기", key="home"): st.session_state['mode']='main_menu'; st.rerun()
    st.divider()

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
                        root = tk.Tk()
                        root.withdraw()
                        root.wm_attributes('-topmost', 1)
                        folder_path = filedialog.askdirectory(master=root)
                        return folder_path
                    except: return None
                    finally:
                        try: root.destroy() 
                        except: pass
                
                p = select_folder_safe()
                if p: 
                    config['target_folder'] = p
                    save_config(config)
                    st.success(f"폴더가 변경되었습니다: {p}")
                    time.sleep(0.5)
                    st.rerun()
                else:
                    st.info("폴더 선택이 취소되었습니다.")

        with c2:
            if st.button("🔄 전체 동기화 (DB 업데이트)", type="primary"):
                if not cur: st.error("폴더 선택 필요")
                else:
                    bar=st.progress(0); txt=st.empty()
                    cnt, msg = processor.sync_files(cur, bar.progress, txt.text)
                    bar.empty(); txt.empty()
                    st.success(msg)
    with t2:
        if st.button("데이터 폴더 열기"): subprocess.Popen(f'explorer "{APP_DATA_DIR}"')
        if st.button("DB 초기화 (삭제)", type="primary"):
            if os.path.exists(DB_PATH): os.remove(DB_PATH)
            processor.init_db(DB_PATH)
            st.success("초기화 완료")

# ==========================================
# ❓ 도움말
# ==========================================
elif st.session_state['mode'] == 'help':
    st.markdown("""
    <style>
    section[data-testid="stMain"] div.stButton > button {
        width: 100% !important; height: 3rem !important;
        background-color: #f0f2f6 !important; border: 1px solid #ddd !important;
        border-radius: 8px !important; display: flex !important; align-items: center !important; justify-content: center !important; font-size: 1rem !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    if st.button("🏠 홈으로 돌아가기", key="home"): st.session_state['mode']='main_menu'; st.rerun()
    st.divider()

    st.title("❓ 사용 설명서 (User Manual)")
    tab1, tab2, tab3, tab4 = st.tabs(["🚀 **시작하기 (필독)**", "🌟 **기능 상세 가이드**", "❓ **자주 묻는 질문 (FAQ)**", "📢 **업데이트 로그**"])
    with tab1:
        st.markdown("""
        <h3>1단계: 설교 파일 준비하기</h3>
        <p>이 프로그램은 목사님의 컴퓨터에 저장된 <strong>한글(HWP)</strong> 및 <strong>워드(DOCX)</strong> 파일을 자동으로 읽어옵니다.<br>
        가장 중요한 것은 <strong>"컴퓨터가 알아먹게 이름을 짓는 것"</strong>입니다.</p>
        <h4>✅ 날짜 인식 규칙 (파일명)</h4>
        <p>파일 이름에 날짜가 있어야 '연대기' 탭에 표시됩니다.</p>
        <ul>
            <li><strong><code>230521</code></strong> (6자리 붙여쓰기) : 가장 추천하는 방식입니다. (2023년 5월 21일)</li>
            <li><strong><code>2023-05-21</code></strong> (구분자 사용) : 하이픈(-), 점(.), 공백( ) 모두 가능합니다.</li>
            <li><strong><code>p220703</code></strong> (영문자 + 6자리) : 파일명 맨 앞에 영문자가 하나 있어도 날짜로 인식합니다.</li>
            <li><strong><code>20230521</code></strong> (8자리 붙여쓰기)</li>
            <li><strong><code>2023 0521</code></strong> (연도는 띄고 월일은 붙이고)</li>
        </ul>
        <h4>✅ 성경 본문 인식 규칙</h4>
        <p>본문 내용이나 파일명에 <strong>"성경이름 + 장:절"</strong> 형식이 있어야 통계에 잡힙니다.</p>
        <ul>
            <li><code>마태복음 5:3</code> (정석)</li>
            <li><code>마 5:3</code> (약어도 OK)</li>
        </ul>
        <hr>
        <h3>2단계: 폴더 연결 및 동기화</h3>
        <ol>
            <li>메인 메뉴에서 <strong>[⚙️ 설정]</strong>을 누르세요.</li>
            <li><strong>[📂 폴더 변경하기]</strong> 버튼을 눌러 설교 파일들이 모여있는 폴더를 선택하세요.</li>
            <li><strong>[🔄 동기화 시작]</strong> 버튼을 누르세요.</li>
        </ol>
        """, unsafe_allow_html=True)
    with tab2:
        st.markdown("""
        <h3>🌟 이 프로그램만의 특별한 기능</h3>
        <h4>1. ✍️ 작업실 (Workspace)</h4>
        <ul>
            <li><strong>통합 검색:</strong> <strong>제목</strong>과 <strong>본문</strong>을 동시에 검색합니다.</li>
            <li><strong>키워드 하이라이트:</strong> 검색된 단어는 <span style='color:red; font-weight:bold;'>빨간색 볼드체</span>로 표시됩니다.</li>
            <li><strong>대용량 페이징(Paging):</strong> 수천 건의 검색 결과도 끊김 없이 50개씩 빠르게 열람할 수 있습니다.</li>
        </ul>
        <h4>2. 📅 설교 연대기 (Chronicle)</h4>
        <ul>
            <li><strong>타임라인:</strong> 내가 언제 무슨 설교를 했는지 연도별, 월별로 보여줍니다.</li>
            <li><strong>접기/펼치기:</strong> 제목을 클릭하면 본문 전문이 아래로 펼쳐집니다.</li>
            <li><strong>엑셀 내보내기:</strong> <strong>[📥 엑셀로 목록 내려받기]</strong> 메뉴를 사용해보세요.</li>
        </ul>
        <h4>3. 📊 통계 대시보드 (Statistics)</h4>
        <ul>
            <li><strong>성경 히트맵 (New):</strong> 구약(파랑)과 신약(빨강)의 설교 빈도를 바둑판 색상 농도로 한눈에 보여줍니다.</li>
            <li><strong>워드 클라우드:</strong> 내 설교에서 가장 자주 등장하는 핵심 단어들을 구름 모양으로 시각화해 줍니다.</li>
        </ul>
        """, unsafe_allow_html=True)
    with tab3:
        st.markdown("""
        <h3>Q. 설교 파일을 수정했는데 반영이 안 돼요.</h3>
        <p><strong>A.</strong> 프로그램을 껐다 켜거나 <strong>[⚙️ 설정] > [🔄 동기화 시작]</strong> 버튼을 눌러주세요.</p>
        <h3>Q. 검색했는데 결과가 안 나와요.</h3>
        <p><strong>A.</strong> 띄어쓰기를 확인해 보세요. 그리고 동기화가 최신 상태인지 확인해 주세요.</p>
        <h3>Q. '미분류' 설교가 너무 많아요.</h3>
        <p><strong>A.</strong> [📊 통계] 메뉴에 가시면 <strong>"📂 미분류 파일 명단 열기"</strong> 버튼이 있습니다. 거기서 파일명을 확인하고, 원본 파일의 제목이나 본문에 <code>[성경이름 장:절]</code>을 정확히 기입한 뒤 다시 동기화해주세요.</p>
        <h3>Q. 엑셀 다운로드가 안 돼요.</h3>
        <p><strong>A.</strong> 연대기 탭에서 연도를 하나 이상 선택하셨는지 확인해 주세요.</p>
        """, unsafe_allow_html=True)
    with tab4:
        st.markdown("""
        <h3>📢 업데이트 로그</h3>
        <h4>v4.4 (2026-01-13) - Performance & UI Completed</h4>
        <ul>
            <li><strong>⚡️ 검색 페이징 탑재:</strong> 작업실에서 검색 결과가 많을 때 50개씩 끊어서 볼 수 있는 '페이지 넘기기' 기능을 추가하여 속도를 극대화했습니다.</li>
            <li><strong>🔥 성경 히트맵 테마:</strong> 신약 성경을 붉은색 테마로 적용하여 가독성을 높였습니다.</li>
            <li><strong>💊 안정성 확보:</strong> 모든 기능의 충돌을 해결하고 안정화했습니다.</li>
        </ul>
        <h4>v4.x - Major Update</h4>
        <ul>
            <li><strong>🔥 성경 히트맵:</strong> 성경 66권 전체 설교 빈도 시각화 (바둑판 뷰)</li>
            <li><strong>🔳 UI 완성:</strong> 홈 화면 4x2 정사각형 레이아웃 완성</li>
        </ul>
        """, unsafe_allow_html=True)
    st.divider()
    st.caption("Developed by **한빛교회 부목사 윤영천** (theplus2@gmail.com)")