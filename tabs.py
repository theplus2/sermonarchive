import streamlit as st
import os
import pandas as pd
import tkinter as tk
from tkinter import filedialog
from wordcloud import WordCloud
from io import BytesIO
import subprocess
import time
import processor # DB 엔진

# 성경 데이터
BIBLE_ORDER = ["창세기","출애굽기","레위기","민수기","신명기","여호수아","사사기","룻기","사무엘상","사무엘하","열왕기상","열왕기하","역대상","역대하","에스라","느헤미야","에스더","욥기","시편","잠언","전도서","아가","이사야","예레미야","예레미야애가","에스겔","다니엘","호세아","요엘","아모스","오바댜","요나","미가","나훔","하박국","스바냐","학개","스가랴","말라기","마태복음","마가복음","누가복음","요한복음","사도행전","로마서","고린도전서","고린도후서","갈라디아서","에베소서","빌립보서","골로새서","데살로니가전서","데살로니가후서","디모데전서","디모데후서","디도서","빌레몬서","히브리서","야고보서","베드로전서","베드로후서","요한1서","요한2서","요한3서","유다서","요한계시록"]
OT_BOOKS = BIBLE_ORDER[:39]
NT_BOOKS = BIBLE_ORDER[39:]
OT_SET = set(OT_BOOKS)
NT_SET = set(NT_BOOKS)

def go_home():
    st.session_state['mode'] = 'main_menu'
    st.rerun()

# 1. 작업실
def render_workspace(config, DRAFTS_DIR):


    cl, cr = st.columns([6,4])
    with cl:
        st.header("🔍 설교 검색 (DB)")
        c1, c2 = st.columns([1,2])
        with c1: sel_bib = st.multiselect("성경", BIBLE_ORDER)
        with c2: q = st.text_input("검색어", placeholder="제목, 본문, 내용 검색...")
        
        # 정렬 토글 추가
        sort_by_bible = st.toggle("📖 성경 장/절 순으로 정렬", value=False, help="켜면 성경 책 순서 → 장 번호 순으로 정렬됩니다.")
        
        if 'search_page' not in st.session_state: st.session_state['search_page'] = 0
        current_search_hash = f"{q}_{sel_bib}_{sort_by_bible}"
        if 'last_search_hash' not in st.session_state: st.session_state['last_search_hash'] = current_search_hash
        
        if st.session_state['last_search_hash'] != current_search_hash:
            st.session_state['search_page'] = 0
            st.session_state['last_search_hash'] = current_search_hash
        
        with st.container(height=config.get("ui_height", 650), border=True):
            if q or sel_bib:
                # 성경순 정렬 시에는 DB 정렬 안함 (Python에서 직접 정렬)
                all_rows = processor.search_sermons(q, sel_bib, sort_by_date=(not sort_by_bible))
                
                # 성경순 정렬 로직 (DB에 저장된 bible_chapter 사용)
                if sort_by_bible:
                    def get_bible_sort_key(row):
                        tags = row.get('bible_tags', '')
                        chapter = row.get('bible_chapter', 0) or 0
                        
                        if not tags:
                            return (len(BIBLE_ORDER), 0)  # 태그 없으면 맨 뒤
                        
                        first_tag = tags.split(',')[0].strip()
                        
                        # 성경 순서 찾기
                        for i, book in enumerate(BIBLE_ORDER):
                            if first_tag == book:
                                return (i, chapter)
                        
                        return (len(BIBLE_ORDER), 0)
                    
                    all_rows = sorted(all_rows, key=get_bible_sort_key)
                
                total_count = len(all_rows)
                
                PER_PAGE = 30
                start_idx = st.session_state['search_page'] * PER_PAGE
                end_idx = start_idx + PER_PAGE
                page_rows = all_rows[start_idx:end_idx]
                
                sort_label = "📖 성경순" if sort_by_bible else "📅 날짜순"
                st.subheader(f"검색 결과: {total_count}건 ({sort_label})")
                if not all_rows: st.warning("결과가 없습니다.")
                else:
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
                    
                    col_prev, col_info, col_next = st.columns([1, 2, 1])
                    with col_prev:
                        if st.session_state['search_page'] > 0:
                            if st.button("◀️ 이전 30개", key="btn_prev"):
                                st.session_state['search_page'] -= 1
                                st.rerun()
                    with col_info:
                        total_pages = (total_count - 1) // PER_PAGE + 1
                        current_p = st.session_state['search_page'] + 1
                        st.markdown(f"<div style='text-align:center; color:#666; padding-top:10px;'><b>{current_p}</b> / {total_pages} 페이지</div>", unsafe_allow_html=True)
                    with col_next:
                        if end_idx < total_count:
                            if st.button("다음 30개 ▶️", key="btn_next"):
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

# 2. 연대기
def render_chronicle():

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

# 3. 통계 (미분류 페이징 적용)
def render_statistics():

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
                    book_name = b; break
            if book_name in BIBLE_ORDER:
                cnts[book_name] = cnts.get(book_name, 0) + 1
                if book_name in OT_SET: ot_cnt += 1
                elif book_name in NT_SET: nt_cnt += 1

    c1,c2,c3,c4 = st.columns(4)
    c1.metric("총 설교", f"{total}편"); c2.metric("구약", f"{ot_cnt}회"); c3.metric("신약", f"{nt_cnt}회"); c4.metric("미분류", f"{no_tag}편")
    
    st.divider()
    
    # [v4.8] 미분류 명단 페이징 처리
    if no_tag > 0:
        with st.expander(f"📂 미분류 설교 명단 보기 ({no_tag}편)"):
            st.warning("아래 파일들은 성경 태그가 인식되지 않았습니다. 파일명이나 본문 초반 300자 안에 **'창세기 1:1'** 또는 **'창1장'** 형식으로 성경 본문을 추가해주세요.")
            
            st.info("""
**미분류 사유 안내:**
- 🚫 **성경 태그 없음**: 파일명이나 본문 초반에 '성경이름 + 장' 패턴이 없음
- ⏳ **날짜 없음**: 파일명에서 날짜를 인식하지 못함 (예: 250115, 2025-01-15)
            """)
            
            # 1. 전체 데이터 가져와서 미분류만 필터링
            all_meta = processor.get_all_sermons_metadata()
            no_tag_rows = [row for row in all_meta if not row['bible_tags']]
            
            # 2. 페이징 상태 관리 (통계 페이지용 별도 키 사용)
            if 'stats_page' not in st.session_state: st.session_state['stats_page'] = 0
            
            PER_PAGE = 30
            total_count = len(no_tag_rows)
            start_idx = st.session_state['stats_page'] * PER_PAGE
            end_idx = start_idx + PER_PAGE
            page_rows = no_tag_rows[start_idx:end_idx]
            
            # 3. 목록 출력 (미분류 사유 표시)
            for row in page_rows:
                reasons = []
                if not row['bible_tags']:
                    reasons.append("🚫 성경 태그 없음")
                if not row['date']:
                    reasons.append("⏳ 날짜 없음")
                reason_text = " / ".join(reasons) if reasons else ""
                
                # 본문 미리보기 (50자)
                content_preview = row.get('content', '')[:50].replace('\n', ' ')
                if len(row.get('content', '')) > 50:
                    content_preview += "..."
                
                with st.expander(f"**{row['file_name']}** - {reason_text}"):
                    st.caption(f"📄 제목: {row['title']}")
                    if row['date']:
                        st.caption(f"📅 날짜: {row['date']}")
                    else:
                        st.caption("📅 날짜: _(인식 안됨)_")
                    st.caption(f"📝 본문 미리보기: {content_preview if content_preview else '_(내용 없음)_'}")
            
            st.divider()
            
            # 4. 페이징 버튼
            c_prev, c_info, c_next = st.columns([1, 2, 1])
            with c_prev:
                if st.session_state['stats_page'] > 0:
                    if st.button("◀️ 이전 30개", key="stats_prev"):
                        st.session_state['stats_page'] -= 1
                        st.rerun()
            with c_info:
                total_pages = (total_count - 1) // PER_PAGE + 1
                current_p = st.session_state['stats_page'] + 1
                st.markdown(f"<div style='text-align:center; color:#666;'><b>{current_p}</b> / {total_pages} 페이지</div>", unsafe_allow_html=True)
            with c_next:
                if end_idx < total_count:
                    if st.button("다음 30개 ▶️", key="stats_next"):
                        st.session_state['stats_page'] += 1
                        st.rerun()

    st.subheader("🔥 성경 설교 히트맵 (Bible Heatmap)")
    st.caption("📌 색이 진할수록 설교가 많습니다. 아래에서 성경을 선택하면 목록이 표시됩니다.")
    max_val = max(cnts.values()) if cnts else 1
    
    # session_state 초기화
    if 'selected_ot' not in st.session_state:
        st.session_state['selected_ot'] = None
    if 'selected_nt' not in st.session_state:
        st.session_state['selected_nt'] = None
    
    def render_html_heatmap(book_list, theme='blue'):
        """예쁜 HTML 히트맵 렌더링 (6열 그리드, 색상 농도 적용, 호버 애니메이션)"""
        # CSS 스타일 정의 (호버 애니메이션 포함)
        style_id = "heatmap_" + theme
        css = '''
        <style>
        .heatmap-box-''' + theme + ''' {
            width: 70px;
            height: 70px;
            border-radius: 12px;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            font-size: 0.75rem;
            font-weight: 700;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            transition: transform 0.2s ease, box-shadow 0.2s ease;
            cursor: default;
        }
        .heatmap-box-''' + theme + ''':hover {
            transform: scale(1.18);
            box-shadow: 0 6px 15px rgba(0,0,0,0.25);
            z-index: 100;
        }
        </style>
        '''
        
        items = []
        for book in book_list:
            count = cnts.get(book, 0)
            if count == 0:
                bg = "#f0f0f0"
                fg = "#bbb"
                border = "1px solid #ddd"
            else:
                ratio = count / max_val
                opacity = 0.15 + ratio * 0.85
                if theme == 'red':
                    bg = "rgba(220, 53, 69, " + str(round(opacity, 2)) + ")"
                    fg = "#fff" if opacity > 0.4 else "#c62828"
                else:
                    bg = "rgba(13, 110, 253, " + str(round(opacity, 2)) + ")"
                    fg = "#fff" if opacity > 0.4 else "#0d6efd"
                border = "1px solid transparent"
            
            item = '<div class="heatmap-box-' + theme + '" style="background:' + bg + ';color:' + fg + ';border:' + border + ';"><span>' + book + '</span><span style="font-size:0.65rem;opacity:0.85;margin-top:2px;">' + str(count) + '</span></div>'
            items.append(item)
        
        # 6열 그리드 레이아웃
        html = css + '<div style="display:grid;grid-template-columns:repeat(6,70px);gap:5px;">' + ''.join(items) + '</div>'
        return html
    
    def render_sermon_list(selected_book, book_set, testament_name, page_key):
        """선택된 성경의 설교 목록 렌더링 (미리보기 확장 + 페이징)"""
        if selected_book and selected_book in book_set:
            book_count = cnts.get(selected_book, 0)
            sermons = processor.search_sermons("", [selected_book], sort_by_date=True)
            
            st.markdown(f"### 📚 {selected_book} ({book_count}편)")
            
            if not sermons:
                st.info("설교가 없습니다.")
            else:
                # 페이징 상태 관리
                if page_key not in st.session_state:
                    st.session_state[page_key] = 0
                
                PER_PAGE = 30
                total_count = len(sermons)
                total_pages = (total_count - 1) // PER_PAGE + 1
                current_page = st.session_state[page_key]
                
                start_idx = current_page * PER_PAGE
                end_idx = start_idx + PER_PAGE
                page_sermons = sermons[start_idx:end_idx]
                
                with st.container(height=550):
                    for s in page_sermons:
                        date_str = s.get('date', '') or '날짜없음'
                        title = s.get('title', '제목없음')
                        with st.expander(f"{title} ({date_str})"):
                            # 미리보기 4배 확장 (250 → 1000자)
                            preview = s.get('content', '')[:1000].replace('\n', '\n\n')
                            if len(s.get('content', '')) > 1000:
                                preview += "..."
                            st.markdown(preview if preview else "_(내용 없음)_")
                
                # 페이징 버튼 (30건 이상일 때)
                if total_count > PER_PAGE:
                    st.divider()
                    c_prev, c_info, c_next = st.columns([1, 2, 1])
                    with c_prev:
                        if current_page > 0:
                            if st.button("◀️ 이전", key=f"{page_key}_prev"):
                                st.session_state[page_key] -= 1
                                st.rerun()
                    with c_info:
                        st.markdown(f"<div style='text-align:center;color:#666;padding-top:8px;'><b>{current_page+1}</b> / {total_pages} 페이지</div>", unsafe_allow_html=True)
                    with c_next:
                        if end_idx < total_count:
                            if st.button("다음 ▶️", key=f"{page_key}_next"):
                                st.session_state[page_key] += 1
                                st.rerun()
        else:
            st.markdown(f"### 📖 {testament_name} 성경 선택")
            st.caption("아래 selectbox에서 성경을 선택하세요.")
    
    # ========== 구약 섹션 ==========
    st.markdown("### 📜 구약 (Old Testament)")
    ot_col_map, ot_col_list = st.columns([4, 6])
    
    with ot_col_map:
        st.markdown(render_html_heatmap(OT_BOOKS, 'blue'), unsafe_allow_html=True)
        st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
        # 구약 성경 선택
        ot_options = ["선택하세요..."] + [b for b in OT_BOOKS if cnts.get(b, 0) > 0]
        ot_selected = st.selectbox("구약 성경 선택", ot_options, key="ot_select", label_visibility="collapsed")
        if ot_selected != "선택하세요...":
            st.session_state['selected_ot'] = ot_selected
    
    with ot_col_list:
        render_sermon_list(st.session_state.get('selected_ot'), OT_SET, "구약", "ot_page")
    
    st.divider()
    
    # ========== 신약 섹션 ==========
    st.markdown("### 🕊️ 신약 (New Testament)")
    nt_col_map, nt_col_list = st.columns([4, 6])
    
    with nt_col_map:
        st.markdown(render_html_heatmap(NT_BOOKS, 'red'), unsafe_allow_html=True)
        st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
        # 신약 성경 선택
        nt_options = ["선택하세요..."] + [b for b in NT_BOOKS if cnts.get(b, 0) > 0]
        nt_selected = st.selectbox("신약 성경 선택", nt_options, key="nt_select", label_visibility="collapsed")
        if nt_selected != "선택하세요...":
            st.session_state['selected_nt'] = nt_selected
    
    with nt_col_list:
        render_sermon_list(st.session_state.get('selected_nt'), NT_SET, "신약", "nt_page")
    
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

# 4. 설정
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
                    cnt, msg = processor.sync_files(cur, bar.progress, txt.text)
                    bar.empty(); txt.empty()
                    st.success(msg)
    with t2:
        if st.button("데이터 폴더 열기"): subprocess.Popen(f'explorer "{APP_DATA_DIR}"')
        if st.button("DB 초기화 (삭제)", type="primary"):
            if os.path.exists(DB_PATH): os.remove(DB_PATH)
            processor.init_db(DB_PATH)
            st.success("초기화 완료")

# 5. 도움말
def render_help():
    st.title("❓ 도움말 (User Manual)")
    st.caption("설교자의 서재 v5.0.3 사용 가이드")
    
    # 아이콘 및 마크다운 제거하여 깔끔하게 표시
    # Stremlit의 st.tabs는 마크다운을 일부 지원하지만, 때로 기호가 깨질 수 있음.
    tab0, tab1, tab2, tab3, tab4 = st.tabs([
        "👨‍💻 개발자 소개", 
        "🚀 시작하기 (필독)", 
        "🌟 기능 상세 가이드", 
        "❓ 자주 묻는 질문 (FAQ)", 
        "📢 업데이트 로그"
    ])
    
    # 개발자 소개 탭
    with tab0:
        st.markdown("""
        ### 👋 안녕하세요. 윤영천 목사입니다.
        
        코딩을 전혀 몰라도 프로그램을 만들 수 있는 시대가 되었습니다.
        
        ---
        
        #### 📖 &lt;목사님도 코딩 하실 수 있어요!&gt;
        **- 코딩 1도 모르는 목사가 알려주는 바이브 코딩 -**
        
        이라는 프로젝트로 여러가지 프로그램을 개발하고,  
        목회에 도움이 되는 AI 활용법을 친절하고 상세하게 알려드릴 계획입니다.
        
        ---
        
        #### ✝️ 설교자의 서재를 만들게 된 이유
        
        이번 **'설교자의 서재'** 프로그램은  
        설교원고를 **HWP 파일**이나 **DOCX 파일**로 작업하시던 목사님들의 편의를 위해  
        이 프로그램을 개발하게 되었습니다.
        
        설교 원고는 파일로 쌓여가지만, **색인작업과 검색을 매우 불편해 하셨던 저희 아버지**를 생각하면서  
        프로그램을 기획하고 만들게 되었습니다.
        
        ---
        
        #### 🔗 연락처 및 업데이트 안내
        
        기능이 업데이트 될 때마다 확인하시고 다운로드 받으시기 위해서는  
        **제 블로그를 방문**해 주시면 되겠습니다.
        
        📎 **블로그 주소**: [http://blog.naver.com/theplus2](http://blog.naver.com/theplus2)
        
        모든 문의는 **블로그**나 **이메일**로 해주시면 확인하고 답변드리겠습니다.
        
        ---
        
        감사합니다. 🙏
        
        **잠실한빛교회(기성) 청년부 담당 윤영천 목사 드림.**
        
        ---
        
        ### ☕ 따뜻한 후원의 마음
        
        이 프로그램은 누구나 자유롭게 사용할 수 있는 무료 소프트웨어입니다.  
        하지만 개발에는 정말 많은 시간과 노력이 들어갔습니다.  
        프로그램이 마음에 드신다면, 개발자님께 커피 한 잔의 응원을 보내주시는 건 어떨까요?
        
        **후원 계좌: 하나은행 670-910177-84807 (윤영천)**
        """, unsafe_allow_html=True)
    
    # 시작하기 탭
    with tab1:
        st.markdown("""
        ### 🎉 설교자의 서재에 오신 것을 환영합니다!
        
        이 프로그램은 목사님의 컴퓨터에 저장된 <strong>한글(HWP)</strong> 및 <strong>워드(DOCX)</strong> 설교 파일을 자동으로 읽어와서  
        <strong>검색, 통계, 연대기</strong> 기능을 제공하는 설교 원고 관리 프로그램입니다.
        
        ---
        
        ### 📌 1단계: 설교 파일 준비하기
        
        가장 중요한 것은 <strong>"컴퓨터가 알아먹게 이름을 짓는 것"</strong>입니다.
        
        #### ✅ 날짜 인식 규칙 (파일명)
        파일 이름에 날짜가 있어야 <strong>'연대기'</strong> 탭에 표시됩니다.
        
        | 형식 | 예시 | 설명 |
        |------|------|------|
        | 6자리 붙여쓰기 | `230521` | ✨ <strong>가장 추천!</strong> (2023년 5월 21일) |
        | 8자리 붙여쓰기 | `20230521` | 연도 4자리 포함 |
        | 구분자 사용 | `2023-05-21` | 하이픈(-), 점(.), 공백( ) 모두 가능 |
        | 영문자 + 6자리 | `p220703` | 파일명 앞에 영문자 하나 있어도 OK |
        | 연도 띄우기 | `2023 0521` | 연도와 월일 사이 공백 |
        
        #### ✅ 성경 본문 인식 규칙
        본문 내용이나 파일명에 <strong>"성경이름 + 장:절"</strong> 형식이 있어야 통계에 잡힙니다.
        
        | 형식 | 예시 |
        |------|------|
        | 정식 표기 | `마태복음 5:3`, `창세기 1:1` |
        | 약어 표기 | `마 5:3`, `창 1:1` |
        | 장만 표기 | `마태복음 5장`, `창14장` |
        
        ---
        
        ### 📌 2단계: 폴더 연결 및 동기화
        
        1. 왼쪽 메뉴에서 **[⚙️ 설정]**을 클릭하세요.
        2. **[📂 폴더 변경하기]** 버튼을 눌러 설교 파일들이 모여있는 폴더를 선택하세요.
        3. **[🔄 전체 동기화]** 버튼을 누르세요.
        4. 처음 동기화는 파일 수에 따라 몇 분이 걸릴 수 있습니다. ☕ 커피 한 잔 하고 오세요!
        
        ---
        
        ### 📌 3단계: 설교 검색 및 활용
        
        - **✍️ 작업실**: 키워드로 설교를 검색하고, 성경별로 필터링할 수 있습니다.
        - **📅 연대기**: 연도별/월별로 설교 목록을 확인하고 엑셀로 내려받을 수 있습니다.
        - **📊 통계**: 어떤 성경을 많이 설교했는지 히트맵으로 확인할 수 있습니다.
        
        > 💡 **팁**: 왼쪽 사이드바 메뉴를 사용하면 어느 페이지에서든 원하는 메뉴로 바로 이동할 수 있습니다!
        """, unsafe_allow_html=True)
    
    # 기능 상세 가이드 탭
    with tab2:
        st.markdown("""
        ### 🌟 기능별 상세 가이드
        
        ---
        
        #### ✍️ 1. 작업실 (Workspace)
        
        설교 원고를 **검색하고 열람**하는 핵심 기능입니다.
        
        | 기능 | 설명 |
        |------|------|
        | 🔍 **통합 검색** | 제목과 본문을 동시에 검색합니다. 띄어쓰기 주의! |
        | 📖 **성경 필터** | 특정 성경만 선택해서 볼 수 있습니다. 복수 선택 가능! |
        | 📖 **성경순 정렬** | 토글을 켜면 성경 책 순서 → 장 번호 순으로 정렬됩니다. |
        | 🎨 **키워드 하이라이트** | 검색된 단어는 **빨간색 볼드체**로 표시됩니다. |
        | 📄 **페이징** | 결과가 많아도 30개씩 끊어서 빠르게 볼 수 있습니다. |
        
        ---
        
        #### 📅 2. 연대기 (Chronicle)
        
        **언제 어떤 설교를 했는지** 시간순으로 확인할 수 있습니다.
        
        | 기능 | 설명 |
        |------|------|
        | 📆 **연도 필터** | 원하는 연도만 선택해서 볼 수 있습니다. |
        | 📂 **접기/펼치기** | 제목을 클릭하면 본문 전문이 펼쳐집니다. |
        | 📥 **엑셀 내보내기** | 선택한 연도의 설교 목록을 엑셀 파일로 다운로드합니다. |
        
        ---
        
        #### 📊 3. 통계 (Statistics)
        
        나의 **설교 편식 패턴**을 분석해 줍니다.
        
        | 기능 | 설명 |
        |------|------|
        | 🗺️ **성경 히트맵** | 구약(파랑)과 신약(빨강)의 설교 빈도를 색상 농도로 시각화합니다. |
        | 📂 **미분류 명단** | 성경 태그가 인식되지 않은 파일들을 30개씩 페이징하여 보여줍니다. 사유와 미리보기도 제공! |
        | ☁️ **워드 클라우드** | 내 설교에서 가장 자주 등장하는 단어들을 구름 모양으로 시각화합니다. |
        
        ---
        
        #### ⚙️ 4. 설정 (Settings)
        
        프로그램의 **데이터 관리**를 담당합니다.
        
        | 기능 | 설명 |
        |------|------|
        | 📂 **폴더 변경** | 설교 파일이 저장된 폴더를 지정합니다. |
        | 🔄 **동기화** | 파일 변경 사항을 DB에 반영합니다. 파일명 변경/삭제 시 자동 정리됩니다. |
        | 🗑️ **DB 초기화** | 데이터베이스를 완전히 리셋합니다. (주의!) |
        | 📏 **화면 높이 조정** | UI 컨테이너의 높이를 조절합니다. |
        
        ---
        
        #### ❓ 5. 도움말 (Help)
        
        지금 보고 계신 이 페이지입니다! 😊
        """, unsafe_allow_html=True)
    
    # FAQ 탭
    with tab3:
        st.markdown("""
        ### ❓ 자주 묻는 질문 (FAQ)
        
        ---
        
        #### Q. 설교 파일을 수정했는데 반영이 안 돼요.
        
        **A.** 프로그램을 껐다 켜거나 **[⚙️ 설정] > [🔄 동기화 시작]** 버튼을 눌러주세요.  
        동기화를 하면 변경된 파일만 자동으로 업데이트됩니다.
        
        ---
        
        #### Q. 검색했는데 결과가 안 나와요.
        
        **A.** 다음 사항을 확인해 보세요:
        - ✅ 띄어쓰기가 정확한지 확인
        - ✅ 동기화가 최신 상태인지 확인
        - ✅ 성경 필터가 선택되어 있다면 해제해 보기
        
        ---
        
        #### Q. '미분류' 설교가 너무 많아요.
        
        **A.** **[📊 통계]** 메뉴에서 **"📂 미분류 설교 명단 보기"**를 클릭하세요.  
        각 파일별로 왜 미분류되었는지 사유(날짜 없음, 성경 태그 없음)가 표시됩니다.  
        원본 파일의 제목이나 본문 앞부분에 `창세기 1:1` 같은 형식을 추가한 뒤 다시 동기화해주세요.
        
        ---
        
        #### Q. 엑셀 다운로드가 안 돼요.
        
        **A.** 연대기 탭에서 **연도를 하나 이상 선택**하셨는지 확인해 주세요.  
        연도 선택 후 접기를 펼치면 다운로드 버튼이 나타납니다.
        
        ---
        
        #### Q. 파일명을 바꿨는데 이전 파일이 검색돼요.
        
        **A.** v4.9부터는 동기화 시 **폴더에 없는 파일은 자동으로 DB에서 삭제**됩니다.  
        **[⚙️ 설정] > [🔄 동기화 시작]**을 눌러주세요.
        
        ---
        
        #### Q. HWP 파일 내용이 제대로 안 보여요.
        
        **A.** v4.9에서 HWP 텍스트 추출 기능이 대폭 개선되었습니다.  
        DB 초기화 후 다시 동기화하면 개선된 내용을 확인하실 수 있습니다.
        
        ---
        
        #### Q. 성경순 정렬이 제대로 안 돼요.
        
        **A.** v4.9에서 성경 장 번호가 DB에 별도 저장됩니다.  
        **DB 초기화 후 다시 동기화**하면 정확한 장 번호 순서로 정렬됩니다.
        """, unsafe_allow_html=True)
    
    # 업데이트 로그 탭
    with tab4:
        st.markdown("""
        ### 📢 업데이트 로그
        
        ---
        
        #### 🆕 v4.9.5 (2026-01-17) - 히트맵 UX 대폭 개선
        
        **✨ 새로운 기능**
        - 🔥 **클릭 가능한 히트맵**: 구약/신약 각각 6열 그리드로 정렬, 색상 농도로 빈도 시각화
        - 📋 **구약/신약 별도 목록**: 각 히트맵 옆에 해당 성경의 설교 목록 표시
        - 📄 **페이징 기능**: 30건 이상 시 이전/다음 페이지 버튼으로 탐색
        
        **🔧 개선 사항**
        - ⚡ **DB 동기화 성능 최적화**: ThreadPoolExecutor 병렬 처리로 2~5배 속도 향상
        - 📖 **미리보기 4배 확장**: 설교 본문 미리보기 250자 → 1000자
        - 🎨 **히트맵 호버 애니메이션**: scale(1.18) 효과 및 그림자로 인터랙티브 UX
        - 📏 **버튼 크기 증가**: 70x70px 정사각형으로 가독성 향상
        
        ---
        
        #### 🆕 v4.9 (2026-01-15) - 대규모 기능 개선
        
        **✨ 새로운 기능**
        - 📚 **사이드바 네비게이션**: 어느 페이지에서든 원하는 메뉴로 바로 이동 가능
        - 👨‍💻 **개발자 소개 탭**: 도움말에 개발자 인사말 추가
        - 📖 **성경 장 번호 DB 저장**: 정렬 정확도 대폭 향상
        
        **🔧 개선 사항**
        - 🔄 **동기화 시 삭제된 파일 자동 정리**: 파일명 변경/삭제 시 이전 데이터 자동 제거
        - 📅 **날짜 패턴 확장**: `YYYY MMDD`, `pYYMMDD` 등 더 많은 형식 지원
        - 🏷️ **성경 태깅 정교화**: 오탐지 방지 (한 글자 축약형 단어 경계 체크)
        - � **HWP 텍스트 추출 개선**: 버퍼 제한 회피로 전체 내용 추출
        - �📂 **미분류 목록 개선**: 사유(날짜/태그 없음) 및 미리보기 표시
        - 🎨 **푸터 추가**: 모든 페이지 하단에 개발자 정보 표시
        - 📝 **도움말 전면 개편**: 친절하고 상세한 설명으로 업데이트
        
        ---
        
        #### v4.8 (2026-01-14) - 미분류 목록 페이징
        
        - 📂 **미분류 명단 페이징**: 30개씩 나누어 보기
        - ✨ **상세 도움말 복구**: 최신 기능 반영
        
        ---
        
        #### v4.6 - 구조 개선
        
        - 🔧 검색 성능 최적화 및 코드 구조 개선
        - 🎨 UI 스타일 분리
        
        ---
        
        #### v4.0 - 첫 정식 배포
        
        - ✅ 설교 원고 통합 검색
        - ✅ 연대기 기능
        - ✅ 성경별 통계 및 히트맵
        - ✅ 워드 클라우드
        - ✅ 엑셀 내보내기
        """, unsafe_allow_html=True)