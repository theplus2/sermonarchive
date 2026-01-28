import streamlit as st
from io import BytesIO
from src.core import processor

def render_chronicle(DB_PATH):
    import pandas as pd
    st.title("📅 설교 연대기")
    rows = processor.get_all_sermons_metadata(DB_PATH)
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
