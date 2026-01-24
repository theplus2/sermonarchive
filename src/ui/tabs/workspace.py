import streamlit as st
import os
# processor는 src.core.processor 형식을 따름
from src.core import processor

BIBLE_ORDER = ["창세기","출애굽기","레위기","민수기","신명기","여호수아","사사기","룻기","사무엘상","사무엘하","열왕기상","열왕기하","역대상","역대하","에스라","느헤미야","에스더","욥기","시편","잠언","전도서","아가","이사야","예레미야","예레미야애가","에스겔","다니엘","호세아","요엘","아모스","오바댜","요나","미가","나훔","하박국","스바냐","학개","스가랴","말라기","마태복음","마가복음","누가복음","요한복음","사도행전","로마서","고린도전서","고린도후서","갈라디아서","에베소서","빌립보서","골로새서","데살로니가전서","데살로니가후서","디모데전서","디모데후서","디도서","빌레몬서","히브리서","야고보서","베드로전서","베드로후서","요한1서","요한2서","요한3서","유다서","요한계시록"]

def render_workspace(config, DRAFTS_DIR, DB_PATH):
    cl, cr = st.columns([6,4])
    with cl:
        st.header("🔍 설교 검색 (DB)")
        c1, c2 = st.columns([1,2])
        with c1: sel_bib = st.multiselect("성경", BIBLE_ORDER)
        with c2: q = st.text_input("검색어", placeholder="제목, 본문, 내용 검색...")
        
        sort_by_bible = st.toggle("📖 성경 장/절 순으로 정렬", value=False, help="켜면 성경 책 순서 → 장 번호 순으로 정렬됩니다.")
        
        if 'search_page' not in st.session_state: st.session_state['search_page'] = 0
        current_search_hash = f"{q}_{sel_bib}_{sort_by_bible}"
        if 'last_search_hash' not in st.session_state: st.session_state['last_search_hash'] = current_search_hash
        
        if st.session_state['last_search_hash'] != current_search_hash:
            st.session_state['search_page'] = 0
            st.session_state['last_search_hash'] = current_search_hash
        
        with st.container(height=config.get("ui_height", 650), border=True):
            if q or sel_bib:
                all_rows = processor.search_sermons(DB_PATH, q, sel_bib, sort_by_date=(not sort_by_bible))
                
                if sort_by_bible:
                    def get_bible_sort_key(row):
                        tags = row.get('bible_tags', '')
                        chapter = row.get('bible_chapter', 0) or 0
                        if not tags: return (len(BIBLE_ORDER), 0)
                        first_tag = tags.split(',')[0].strip()
                        for i, book in enumerate(BIBLE_ORDER):
                            if first_tag == book: return (i, chapter)
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
