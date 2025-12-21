# common.py
# -*- coding: utf-8 -*-
"""
공통 UI 컴포넌트 - 튜터 중심 디자인 (모든 사이드바 버튼 호버 적용)
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

        /* ================================================================= */
        /* [1] 사이드바 버튼 공통 스타일 (모든 버튼 적용) */
        /* ================================================================= */
        
        /* 1-1. 버튼 기본 상태: 투명하고 깔끔하게 */
        section[data-testid="stSidebar"] .stButton button {
            background: transparent !important;
            border: none !important;
            box-shadow: none !important;
            color: #555 !important;
            text-align: left !important;
            padding: 0.5rem 0.5rem !important;
            font-weight: 400 !important;
            transition: all 0.2s ease-in-out !important;
            border-radius: 6px !important;
            margin: 0 !important;
            width: 100%;
            line-height: 1.5 !important;
        }

        /* 1-2. ★ 일반 버튼 호버 효과 (자료관리, 퀴즈, 복습노트 등) */
        /* 사이드바의 모든 버튼에 대해 기본적으로 배경색과 이동 효과 적용 */
        section[data-testid="stSidebar"] .stButton button:hover {
            background-color: #FFF3E0 !important; /* 연한 오렌지 배경 */
            color: #FF6B35 !important;            /* 진한 오렌지 글씨 */
            transform: translateX(3px);           /* 오른쪽으로 살짝 이동 */
        }

        /* 1-3. Primary 버튼 (현재 선택된 방) 텍스트 색상 */
        section[data-testid="stSidebar"] .stButton button[kind="primary"] {
            color: #FF6B35 !important;
            font-weight: 700 !important;
            background: transparent !important; 
        }

        /* ================================================================= */
        /* [2] 대화 목록 리스트 (여기는 줄(Row) 전체가 반응해야 함) */
        /* ================================================================= */
        
        /* 2-1. 줄(Row) 컨테이너 설정 */
        section[data-testid="stSidebar"] [data-testid="stHorizontalBlock"] {
            border-radius: 6px;
            padding: 2px 0;
            margin-bottom: 2px;
            transition: background-color 0.2s;
            align-items: center !important;
            display: flex !important;
            gap: 0 !important;
        }

        /* 2-2. 줄 전체 호버 시 배경색 */
        section[data-testid="stSidebar"] [data-testid="stHorizontalBlock"]:hover {
            background-color: #FFF3E0 !important; 
        }

        /* 2-3. ★ [예외 처리] 대화 목록 안의 버튼은 자체 배경색 제거 */
        /* 줄(Row)이 배경을 담당하므로, 버튼 자체의 배경은 투명하게 유지해야 겹치지 않음 */
        section[data-testid="stSidebar"] [data-testid="stHorizontalBlock"] .stButton button:hover {
            background-color: transparent !important; 
        }

        /* 2-4. 선택된 방의 '줄(Row) 전체' 배경색 */
        section[data-testid="stSidebar"] [data-testid="stHorizontalBlock"]:has(button[kind="primary"]) {
            background-color: rgba(255, 107, 53, 0.1) !important;
            border-radius: 6px;
        }

        /* ================================================================= */
        /* [3] 삭제(X) 버튼 스타일링 */
        /* ================================================================= */
        
        /* 3-1. 평소 상태: 투명함 */
        section[data-testid="stSidebar"] [data-testid="stHorizontalBlock"] [data-testid="column"]:last-child button {
            opacity: 0 !important;
            color: #999 !important;
            font-weight: 300 !important;
            transition: opacity 0.2s, color 0.2s !important;
            text-align: center !important;
            padding: 0 !important;
            height: 100% !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
        }

        /* 3-2. 선택된 방일 경우 -> X 버튼 오렌지색 */
        section[data-testid="stSidebar"] [data-testid="stHorizontalBlock"]:has(button[kind="primary"]) [data-testid="column"]:last-child button {
            color: #FF6B35 !important; 
        }

        /* 3-3. 줄 호버 시 -> X 버튼 나타남 */
        section[data-testid="stSidebar"] [data-testid="stHorizontalBlock"]:hover [data-testid="column"]:last-child button {
            opacity: 1 !important;
        }
        
        /* 3-4. X 버튼 호버 시 (빨간색 강제 적용) */
        section[data-testid="stSidebar"] [data-testid="stHorizontalBlock"] [data-testid="column"]:last-child button:hover {
            color: #FF3B30 !important; 
            background-color: rgba(255, 59, 48, 0.1) !important;
            border-radius: 50% !important;
            width: 28px !important;
            height: 28px !important;
            margin: 0 auto !important;
        }

        /* ================================================================= */
        /* [4] 메인 콘텐츠 및 기타 스타일 */
        /* ================================================================= */

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

        /* 빠른 질문 버튼 */
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

        /* 메인 영역 버튼 */
        section[data-testid="stMain"] .stButton > button {
            border-radius: 10px;
            font-weight: 500;
        }
        section[data-testid="stMain"] .stButton > button[kind="primary"] {
            background: #FF6B35;
            border: none;
        }
        section[data-testid="stMain"] .stButton > button[kind="primary"]:hover {
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