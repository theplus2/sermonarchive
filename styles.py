import streamlit as st

def apply_global_styles():
    st.markdown("""
    <style>
        /* 기본 폰트 */
        html, body, [class*="css"] {
            font-family: 'Malgun Gothic', sans-serif !important;
        }
        
        /* ========================================= */
        /* 🎨 사이드바 네비게이션 스타일 (v4.9) */
        /* ========================================= */
        
        /* 1. 사이드바 버튼 공통 스타일 (그림자, 호버 애니메이션) */
        section[data-testid="stSidebar"] div.stButton > button {
            width: 100% !important;
            height: 3rem !important;
            border-radius: 10px !important;
            border: 1px solid rgba(0,0,0,0.05) !important;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05) !important;
            transition: all 0.2s ease-in-out !important;
            color: #333 !important;
            font-weight: 800 !important; /* 버튼 자체 폰트 굵기 */
            background-color: white !important; /* 기본 배경 */
            margin-bottom: 5px !important;
        }
        
        /* 버튼 내부 텍스트(p태그) 강제 볼드 처리 (Streamlit 구조 대응) */
        section[data-testid="stSidebar"] div.stButton > button p {
            font-weight: 900 !important;
        }

        /* 호버 효과 (공통) */
        section[data-testid="stSidebar"] div.stButton > button:hover {
            transform: translateY(-3px) !important;
            box-shadow: 0 6px 12px rgba(0,0,0,0.1) !important;
            border-color: rgba(0,0,0,0.1) !important;
            z-index: 10;
        }

        /* 2. 홈 버튼 (첫 번째 버튼) - 옅은 하늘색 */
        section[data-testid="stSidebar"] div.stButton:nth-of-type(1) > button {
            background-color: #E3F2FD !important; /* Light Sky Blue */
            color: #1565C0 !important;
            border: 1px solid #BBDEFB !important;
        }
        section[data-testid="stSidebar"] div.stButton:nth-of-type(1) > button p {
            color: #1565C0 !important;
        }
        section[data-testid="stSidebar"] div.stButton:nth-of-type(1) > button:hover {
            background-color: #cbE2ff !important;
        }

        /* 3. 일반 메뉴 버튼 (2~6번째) - 투명(글자 검정) */
        section[data-testid="stSidebar"] div.stButton:nth-of-type(n+2):nth-of-type(-n+6) > button {
            background-color: transparent !important; /* 투명 */
            color: #2c3e50 !important;
            border: 1px solid transparent !important; /* 테두리도 투명하게 시작 */
            box-shadow: none !important; /* 그림자 제거 */
        }
        section[data-testid="stSidebar"] div.stButton:nth-of-type(n+2):nth-of-type(-n+6) > button p {
            color: #2c3e50 !important;
        }
        section[data-testid="stSidebar"] div.stButton:nth-of-type(n+2):nth-of-type(-n+6) > button:hover {
            background-color: white !important;
            border: 1px solid rgba(0,0,0,0.1) !important; /* 호버 시 테두리 등장 */
            box-shadow: 0 4px 10px rgba(0,0,0,0.08) !important; /* 호버 시 그림자 등장 */
        }
        
        /* 4. 프로그램 완전 종료 버튼 (7번째, 마지막) - 옅은 빨간색 */
        section[data-testid="stSidebar"] button[kind="primary"] {
            background-color: #FFEBEE !important; /* Light Red */
            color: #C62828 !important; /* Deep Red Text */
            border: 1px solid #FFCDD2 !important;
            margin-top: 10px !important;
            padding-left: 20px !important; /* 요청하신 패딩 반영 */
            padding-right: 20px !important;
        }
        section[data-testid="stSidebar"] button[kind="primary"] p {
             color: #C62828 !important;
        }
        section[data-testid="stSidebar"] button[kind="primary"]:hover {
            background-color: #FFCDD2 !important;
            color: #B71C1C !important;
            box-shadow: 0 4px 12px rgba(255, 0, 0, 0.15) !important;
        }

        /* 태그 및 배지 */
        .bible-tag { background-color: #e8f0fe; color: #1558d6; padding: 2px 8px; border-radius: 10px; font-weight: 700; font-size: 0.8em; }
        .date-badge { background-color: #f1f3f4; color: #3c4043; padding: 2px 6px; border-radius: 4px; font-weight: 600; font-size: 0.8em; border: 1px solid #dadce0; }
        
        /* 히트맵 버튼 그리드 스타일 (v4.9.2) */
        div[data-testid="stHorizontalBlock"] div.heatmap-grid-btn button {
            width: 70px !important;
            height: 70px !important;
            min-width: 70px !important;
            max-width: 70px !important;
            padding: 4px !important;
            margin: 2px !important;
            border-radius: 12px !important;
            font-size: 0.75rem !important;
            font-weight: bold !important;
            line-height: 1.2 !important;
            white-space: pre-wrap !important;
            transition: transform 0.2s, box-shadow 0.2s !important;
        }
        div[data-testid="stHorizontalBlock"] div.heatmap-grid-btn button:hover {
            transform: scale(1.15) !important;
            z-index: 10 !important;
            box-shadow: 0 6px 12px rgba(0,0,0,0.2) !important;
        }
        div[data-testid="stHorizontalBlock"] div.heatmap-grid-btn button p {
            font-size: 0.75rem !important;
            line-height: 1.2 !important;
            margin: 0 !important;
        }
        
        /* 선택된 히트맵 버튼 강조 */
        div.heatmap-selected button {
            border: 3px solid #333 !important;
            box-shadow: 0 0 10px rgba(0,0,0,0.3) !important;
        }
        
        /* 기존 히트맵 스타일 (하위 호환) */
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

def apply_home_styles():
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

def apply_subpage_styles():
    st.markdown("""
    <style>
    section[data-testid="stMain"] div.stButton > button {
        width: 100% !important; height: 3rem !important;
        background-color: #f0f2f6 !important; border: 1px solid #ddd !important;
        border-radius: 8px !important; display: flex !important; align-items: center !important; justify-content: center !important; font-size: 1rem !important;
    }
    </style>
    """, unsafe_allow_html=True)

def apply_settings_styles():
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