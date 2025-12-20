# -*- coding: utf-8 -*-
"""
공통 UI 컴포넌트 - 튜터 중심 디자인
"""

import streamlit as st


def apply_common_styles():
    """공통 CSS 스타일 적용"""
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;600;700&display=swap');

        html, body, [class*="css"] {
            font-family: 'Noto Sans KR', sans-serif;
        }
                
        section[data-testid="stSidebar"] .stButton button {
            width: 100%;
            border: 1px solid transparent;
            background-color: transparent;
            color: #444; /* 글자색 조금 진하게 */
            text-align: left;
            padding-left: 0.8rem;
            transition: all 0.2s;
        }
        
        /* 마우스 올렸을 때 */
        section[data-testid="stSidebar"] .stButton button:hover {
            background-color: #FFF9F5;
            color: #FF6B35;
        }
        
        /* 선택된 방 */
        section[data-testid="stSidebar"] .stButton button[kind="primary"] {
            background-color: #FFF3E0 !important;
            border: 1px solid #FFB088 !important;
            color: #E65100 !important;
            font-weight: 600;
        }

        [data-testid="stSidebar"] [data-testid="stPopover"] > button {
            border: none !important;
            background: transparent !important;
            box-shadow: none !important;
            color: #999 !important;
            padding: 0 !important;
            width: auto !important;
            
            opacity: 0 !important;
            transition: opacity 0.2s ease !important;
            transform: scale(1.2); 
            margin-top: 5px !important;
        }

        [data-testid="stSidebar"] [data-testid="stPopover"] > button:hover {
            opacity: 1 !important;
            color: #333 !important;
            background-color: rgba(0,0,0,0.05) !important; /* 살짝 원형 배경 */
            border-radius: 50% !important;
        }
        
      
        [data-testid="column"]:hover ~ [data-testid="column"] [data-testid="stPopover"] > button {
            opacity: 1 !important;
        }

        [data-testid="stSidebar"] [data-testid="stPopover"] > button[aria-expanded="true"] {
            opacity: 1 !important;
            color: #FF6B35 !important;
        }

        .main .block-container {
            padding: 1.5rem 1rem 6rem 1rem;
            max-width: 720px;
        }

        .tutor-greeting {
            text-align: center;
            padding: 2.5rem 1rem 1.5rem 1rem;
        }
        .tutor-avatar {
            font-size: 3.5rem;
            margin-bottom: 0.8rem;
        }
        .tutor-message {
            font-size: 1.2rem;
            font-weight: 500;
            color: #333;
            margin-bottom: 0.3rem;
        }
        .tutor-sub {
            font-size: 0.9rem;
            color: #999;
        }

        /* 빠른 질문 버튼들 */
        .quick-questions {
            display: flex;
            flex-wrap: wrap;
            justify-content: center;
            gap: 0.5rem;
            margin: 1.5rem 0;
        }
        .quick-btn {
            background: white;
            border: 1px solid #E8E8E8;
            border-radius: 20px;
            padding: 0.5rem 1rem;
            font-size: 0.85rem;
            color: #666;
            cursor: pointer;
            transition: all 0.2s;
        }
        .quick-btn:hover {
            border-color: #FF6B35;
            color: #FF6B35;
            background: #FFFAF8;
        }

        /* 하단 네비게이션 */
        .bottom-nav {
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            background: white;
            border-top: 1px solid #F0F0F0;
            padding: 0.6rem 1rem;
            z-index: 999;
        }
        .nav-inner {
            max-width: 720px;
            margin: 0 auto;
            display: flex;
            justify-content: space-around;
        }
        .nav-item {
            text-align: center;
            padding: 0.4rem 1rem;
            color: #AAA;
            font-size: 0.7rem;
            cursor: pointer;
            transition: color 0.2s;
            border-radius: 8px;
        }
        .nav-item:hover {
            color: #FF6B35;
            background: #FFF9F5;
        }
        .nav-item.active {
            color: #FF6B35;
        }
        .nav-icon {
            font-size: 1.2rem;
            margin-bottom: 0.2rem;
        }

        /* 학습 현황 미니 카드 */
        .mini-status {
            background: #FAFAFA;
            border-radius: 12px;
            padding: 1rem;
            margin: 1rem 0;
        }
        .mini-status-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .mini-status-item {
            text-align: center;
        }
        .mini-status-value {
            font-size: 1.1rem;
            font-weight: 600;
            color: #FF6B35;
        }
        .mini-status-label {
            font-size: 0.7rem;
            color: #999;
            margin-top: 0.1rem;
        }

        /* 자료 태그 */
        .source-tags {
            display: flex;
            flex-wrap: wrap;
            gap: 0.4rem;
            margin: 0.5rem 0;
        }
        .source-tag {
            background: #F5F5F5;
            border-radius: 6px;
            padding: 0.25rem 0.6rem;
            font-size: 0.75rem;
            color: #666;
        }

        /* 채팅 스타일 */
        .stChatMessage {
            padding: 0.8rem 0;
        }
        .stChatInput > div {
            border-radius: 24px !important;
            border: 2px solid #E8E8E8 !important;
            padding: 0.3rem 0.5rem !important;
        }
        .stChatInput > div:focus-within {
            border-color: #FF6B35 !important;
            box-shadow: 0 2px 12px rgba(255, 107, 53, 0.1) !important;
        }

        /* 페이지 헤더 */
        .page-header {
            display: flex;
            align-items: center;
            gap: 0.8rem;
            padding: 0.8rem 0 1.2rem 0;
        }
        .page-back {
            font-size: 1.2rem;
            color: #888;
            cursor: pointer;
        }
        .page-title {
            font-size: 1.1rem;
            font-weight: 600;
            color: #333;
        }

        /* 버튼 */
        .stButton > button {
            border-radius: 10px;
            font-weight: 500;
        }
        .stButton > button[kind="primary"] {
            background: #FF6B35;
            border: none;
        }
        .stButton > button[kind="primary"]:hover {
            background: #E85A2A;
        }

        /* 입력창 */
        .stTextInput > div > div > input,
        .stTextArea > div > div > textarea {
            border-radius: 10px;
            border: 1px solid #E0E0E0;
        }
        .stTextInput > div > div > input:focus,
        .stTextArea > div > div > textarea:focus {
            border-color: #FF6B35;
            box-shadow: 0 0 0 2px rgba(255, 107, 53, 0.08);
        }

        /* 퀴즈 옵션 */
        .quiz-option {
            background: white;
            border: 2px solid #E8E8E8;
            border-radius: 12px;
            padding: 1rem;
            margin: 0.5rem 0;
            cursor: pointer;
            transition: all 0.15s;
        }
        .quiz-option:hover {
            border-color: #FFB088;
        }
        .quiz-option.selected {
            border-color: #FF6B35;
            background: #FFFAF8;
        }
        .quiz-option.correct {
            border-color: #27AE60;
            background: #F5FFF8;
        }
        .quiz-option.wrong {
            border-color: #E74C3C;
            background: #FFF8F8;
        }

        /* 진행바 */
        .progress-wrap {
            background: #E8E8E8;
            border-radius: 8px;
            height: 6px;
            overflow: hidden;
            margin: 1rem 0;
        }
        .progress-fill {
            background: linear-gradient(90deg, #FF8C42, #FF6B35);
            height: 100%;
            border-radius: 8px;
            transition: width 0.3s;
        }

        /* 카드 */
        .card {
            background: white;
            border: 1px solid #EEEEEE;
            border-radius: 12px;
            padding: 1rem;
            margin: 0.5rem 0;
        }

        /* 파일 업로더 */
        .stFileUploader {
            border-radius: 12px;
        }
        .stFileUploader > div {
            border-radius: 12px;
        }

        /* 탭 */
        .stTabs [data-baseweb="tab-list"] {
            gap: 0;
            background: #F5F5F5;
            border-radius: 10px;
            padding: 0.3rem;
        }
        .stTabs [data-baseweb="tab"] {
            border-radius: 8px;
            padding: 0.5rem 1rem;
            font-size: 0.9rem;
        }
        .stTabs [aria-selected="true"] {
            background: white;
            box-shadow: 0 1px 3px rgba(0,0,0,0.08);
        }

        /* 학습 기록 */
        .history-item {
            padding: 0.6rem 0;
            border-bottom: 1px solid #F5F5F5;
            font-size: 0.9rem;
        }
        .history-item:last-child {
            border-bottom: none;
        }
        .history-date {
            font-size: 0.75rem;
            color: #AAA;
        }
                
    </style>
    """, unsafe_allow_html=True)


def render_header(title: str, subtitle: str = ""):
    """서브페이지 헤더"""
    st.markdown(f"""
    <div class="page-header">
        <span class="page-title">{title}</span>
    </div>
    """, unsafe_allow_html=True)


def render_back_button():
    """뒤로가기 버튼"""
    if st.button("← 돌아가기", key="back_btn"):
        st.session_state.current_page = "home"
        st.rerun()


def render_bottom_nav(current: str = "home"):
    """하단 네비게이션"""
    nav_html = f"""
    <div class="bottom-nav">
        <div class="nav-inner">
            <div class="nav-item {'active' if current == 'home' else ''}" onclick="window.location.reload()">
                <div class="nav-icon">🍊</div>
                <div>튜터</div>
            </div>
            <div class="nav-item {'active' if current == 'study' else ''}">
                <div class="nav-icon">📚</div>
                <div>자료</div>
            </div>
            <div class="nav-item {'active' if current == 'quiz' else ''}">
                <div class="nav-icon">✏️</div>
                <div>퀴즈</div>
            </div>
            <div class="nav-item {'active' if current == 'review' else ''}">
                <div class="nav-icon">📝</div>
                <div>복습</div>
            </div>
        </div>
    </div>
    """
    st.markdown(nav_html, unsafe_allow_html=True)
