# -*- coding: utf-8 -*-
"""
오렌지 튜터 - 메인 앱
"""

import streamlit as st
from pathlib import Path
import sys

# 경로 설정
sys.path.insert(0, str(Path(__file__).parent))

from components.common import apply_common_styles
from views import home, study, quiz, review

# 페이지 설정
st.set_page_config(
    page_title="오렌지 튜터",
    page_icon="🍊",
    layout="centered",
    initial_sidebar_state="expanded"
)


def init_session():
    """세션 상태 초기화"""
    defaults = {
        "current_page": "home",
        "messages": [],
        "study_stats": {"studied": 0, "accuracy": 0, "review": 0},
        "study_history": [],
        "wrong_notes": [],
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def main():
    """메인 함수"""
    init_session()
    apply_common_styles()

    page = st.session_state.current_page

    if page == "home":
        home.render()
    elif page == "study":
        study.render()
    elif page == "quiz":
        quiz.render()
    elif page == "review":
        review.render()
    else:
        home.render()


if __name__ == "__main__":
    main()
