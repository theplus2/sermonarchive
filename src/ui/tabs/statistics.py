import streamlit as st
from wordcloud import WordCloud
try:
    from src.core import processor
except ImportError:
    import processor

BIBLE_ORDER = ["창세기","출애굽기","레위기","민수기","신명기","여호수아","사사기","룻기","사무엘상","사무엘하","열왕기상","열왕기하","역대상","역대하","에스라","느헤미야","에스더","욥기","시편","잠언","전도서","아가","이사야","예레미야","예레미야애가","에스겔","다니엘","호세아","요엘","아모스","오바댜","요나","미가","나훔","하박국","스바냐","학개","스가랴","말라기","마태복음","마가복음","누가복음","요한복음","사도행전","로마서","고린도전서","고린도후서","갈라디아서","에베소서","빌립보서","골로새서","데살로니가전서","데살로니가후서","디모데전서","디모데후서","디도서","빌레몬서","히브리서","야고보서","베드로전서","베드로후서","요한1서","요한2서","요한3서","유다서","요한계시록"]
OT_BOOKS = BIBLE_ORDER[:39]
NT_BOOKS = BIBLE_ORDER[39:]
OT_SET = set(OT_BOOKS)
NT_SET = set(NT_BOOKS)

def render_statistics(DB_PATH):
    st.title("📊 통계 대시보드")
    total, no_tag, rows = processor.get_stats(DB_PATH)
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
    
    if no_tag > 0:
        with st.expander(f"📂 미분류 설교 명단 보기 ({no_tag}편)"):
            st.warning("아래 파일들은 성경 태그가 인식되지 않았습니다. 파일명이나 본문 초반 300자 안에 **'창세기 1:1'** 또는 **'창1장'** 형식으로 성경 본문을 추가해주세요.")
            all_meta = processor.get_all_sermons_metadata(DB_PATH)
            no_tag_rows = [row for row in all_meta if not row['bible_tags']]
            if 'stats_page' not in st.session_state: st.session_state['stats_page'] = 0
            PER_PAGE = 30
            total_count = len(no_tag_rows)
            start_idx = st.session_state['stats_page'] * PER_PAGE
            end_idx = start_idx + PER_PAGE
            page_rows = no_tag_rows[start_idx:end_idx]
            for row in page_rows:
                reasons = []
                if not row['bible_tags']: reasons.append("🚫 성경 태그 없음")
                if not row['date']: reasons.append("⏳ 날짜 없음")
                reason_text = " / ".join(reasons) if reasons else ""
                content_preview = row.get('content', '')[:50].replace('\n', ' ')
                if len(row.get('content', '')) > 50: content_preview += "..."
                with st.expander(f"**{row['file_name']}** - {reason_text}"):
                    st.caption(f"📄 제목: {row['title']}")
                    if row['date']: st.caption(f"📅 날짜: {row['date']}")
                    else: st.caption("📅 날짜: _(인식 안됨)_")
                    st.caption(f"📝 본문 미리보기: {content_preview if content_preview else '_(내용 없음)_'}")
            st.divider()
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
    max_val = max(cnts.values()) if cnts else 1
    if 'selected_ot' not in st.session_state: st.session_state['selected_ot'] = None
    if 'selected_nt' not in st.session_state: st.session_state['selected_nt'] = None

    def render_html_heatmap(book_list, theme='blue'):
        style_id = "heatmap_" + theme
        css = f'''<style>.heatmap-box-{theme} {{ width: 70px; height: 70px; border-radius: 12px; display: flex; flex-direction: column; justify-content: center; align-items: center; font-size: 0.75rem; font-weight: 700; box-shadow: 0 2px 5px rgba(0,0,0,0.1); transition: transform 0.2s ease, box-shadow 0.2s ease; cursor: default; }} .heatmap-box-{theme}:hover {{ transform: scale(1.18); box-shadow: 0 6px 15px rgba(0,0,0,0.25); z-index: 100; }}</style>'''
        items = []
        for book in book_list:
            count = cnts.get(book, 0)
            if count == 0: bg = "#f0f0f0"; fg = "#bbb"; border = "1px solid #ddd"
            else:
                ratio = count / max_val; opacity = 0.15 + ratio * 0.85
                if theme == 'red': bg = f"rgba(220, 53, 69, {round(opacity, 2)})"; fg = "#fff" if opacity > 0.4 else "#c62828"
                else: bg = f"rgba(13, 110, 253, {round(opacity, 2)})"; fg = "#fff" if opacity > 0.4 else "#0d6efd"
                border = "1px solid transparent"
            item = f'<div class="heatmap-box-{theme}" style="background:{bg};color:{fg};border:{border};"><span>{book}</span><span style="font-size:0.65rem;opacity:0.85;margin-top:2px;">{count}</span></div>'
            items.append(item)
        return css + f'<div style="display:grid;grid-template-columns:repeat(6,70px);gap:5px;">' + ''.join(items) + '</div>'
    
    def render_sermon_list(selected_book, book_set, testament_name, page_key):
        if selected_book and selected_book in book_set:
            book_count = cnts.get(selected_book, 0)
            sermons = processor.search_sermons(DB_PATH, "", [selected_book], sort_by_date=True)
            st.markdown(f"### 📚 {selected_book} ({book_count}편)")
            if not sermons: st.info("설교가 없습니다.")
            else:
                if page_key not in st.session_state: st.session_state[page_key] = 0
                PER_PAGE = 30; total_count = len(sermons); current_page = st.session_state[page_key]
                start_idx = current_page * PER_PAGE; end_idx = start_idx + PER_PAGE
                page_sermons = sermons[start_idx:end_idx]
                with st.container(height=550):
                    for s in page_sermons:
                        date_str = s.get('date', '') or '날짜없음'; title = s.get('title', '제목없음')
                        with st.expander(f"{title} ({date_str})"):
                            preview = s.get('content', '')[:1000].replace('\n', '\n\n')
                            if len(s.get('content', '')) > 1000: preview += "..."
                            st.markdown(preview if preview else "_(내용 없음)_")
                if total_count > PER_PAGE:
                    st.divider()
                    c_prev, c_info, c_next = st.columns([1, 2, 1])
                    with c_prev:
                        if current_page > 0:
                            if st.button("◀️ 이전", key=f"{page_key}_prev"):
                                st.session_state[page_key] -= 1; st.rerun()
                    with c_info:
                        total_pages = (total_count - 1) // PER_PAGE + 1
                        st.markdown(f"<div style='text-align:center;color:#666;padding-top:8px;'><b>{current_page+1}</b> / {total_pages} 페이지</div>", unsafe_allow_html=True)
                    with c_next:
                        if end_idx < total_count:
                            if st.button("다음 ▶️", key=f"{page_key}_next"):
                                st.session_state[page_key] += 1; st.rerun()
        else:
            st.markdown(f"### 📖 {testament_name} 성경 선택")

    st.markdown("### 📜 구약 (Old Testament)")
    ot_col_map, ot_col_list = st.columns([4, 6])
    with ot_col_map:
        st.markdown(render_html_heatmap(OT_BOOKS, 'blue'), unsafe_allow_html=True)
        ot_options = ["선택하세요..."] + [b for b in OT_BOOKS if cnts.get(b, 0) > 0]
        ot_selected = st.selectbox("구약 성경 선택", ot_options, key="ot_select", label_visibility="collapsed")
        if ot_selected != "선택하세요...": st.session_state['selected_ot'] = ot_selected
    with ot_col_list: render_sermon_list(st.session_state.get('selected_ot'), OT_SET, "구약", "ot_page")
    
    st.divider()
    st.markdown("### 🕊️ 신약 (New Testament)")
    nt_col_map, nt_col_list = st.columns([4, 6])
    with nt_col_map:
        st.markdown(render_html_heatmap(NT_BOOKS, 'red'), unsafe_allow_html=True)
        nt_options = ["선택하세요..."] + [b for b in NT_BOOKS if cnts.get(b, 0) > 0]
        nt_selected = st.selectbox("신약 성경 선택", nt_options, key="nt_select", label_visibility="collapsed")
        if nt_selected != "선택하세요...": st.session_state['selected_nt'] = nt_selected
    with nt_col_list: render_sermon_list(st.session_state.get('selected_nt'), NT_SET, "신약", "nt_page")
    
    st.divider()
    st.subheader("☁️ 핵심 키워드")
    if total > 0:
        with st.spinner("생성 중..."):
            text = processor.get_wordcloud_text(DB_PATH)
            if text:
                stops = {'은','는','이','가','을','를','의','에','에서','로','으로','과','와','도','합니다','것입니다','있습니다','아니라','그','저','우리','나','너','여러분','할','수','있는','말씀','하나님','예수님','주님','제목','본문','설교','아멘','그리고','그러나','하지만','그런데','때문에','위해','통해','대한','모든','어떤','그래서','것','것이다','이러한','하는','줄','있을','한','수','등','더','그','때'}
                try:
                    wc = WordCloud(font_path="C:/Windows/Fonts/malgun.ttf", width=1200, height=400, background_color="white", stopwords=stops, max_words=100).generate(text)
                    st.image(wc.to_array(), use_container_width=True)
                except:
                    wc = WordCloud(width=1200, height=400, background_color="white", stopwords=stops, max_words=100).generate(text)
                    st.image(wc.to_array(), use_container_width=True)
