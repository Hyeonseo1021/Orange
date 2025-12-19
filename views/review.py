# -*- coding: utf-8 -*-
"""
복습 화면
"""

import streamlit as st
from components.common import render_back_button
from rag import get_rag_system
from pipeline import get_pipeline, PipelineInput, TaskType


def render():
    """복습 화면"""

    render_back_button()

    st.markdown("""
    <div class="page-header">
        <span class="page-title">📝 복습</span>
    </div>
    """, unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["오답 노트", "요약"])

    with tab1:
        _render_wrong()

    with tab2:
        _render_summary()


def _render_wrong():
    """오답 노트"""
    wrong = st.session_state.get("wrong_notes", [])

    if not wrong:
        st.markdown("""
        <div style="text-align: center; padding: 3rem; color: #AAA;">
            <div style="font-size: 2rem; margin-bottom: 0.5rem;">✨</div>
            <div>아직 오답이 없어요</div>
            <div style="font-size: 0.85rem; margin-top: 0.3rem;">퀴즈를 풀면 틀린 문제가 여기 저장돼요</div>
        </div>
        """, unsafe_allow_html=True)
        return

    st.markdown(f"**{len(wrong)}개의 오답**")

    for i, item in enumerate(wrong):
        with st.expander(f"{item['question'][:35]}..."):
            st.markdown(f"내 답: ~~{item['your_answer']}~~")
            st.markdown(f"**정답: {item['correct_answer']}**")
            if item.get("explanation"):
                st.caption(item['explanation'])

    if st.button("초기화", type="secondary"):
        st.session_state.wrong_notes = []
        st.rerun()


def _render_summary():
    """학습 요약"""

    try:
        rag = get_rag_system()
        stats = rag.get_collection_stats()

        if stats.get("count", 0) == 0:
            st.markdown("""
            <div style="text-align: center; padding: 3rem; color: #AAA;">
                <div style="font-size: 2rem; margin-bottom: 0.5rem;">📚</div>
                <div>학습 자료가 없어요</div>
                <div style="font-size: 0.85rem; margin-top: 0.3rem;">자료를 추가하면 요약을 생성할 수 있어요</div>
            </div>
            """, unsafe_allow_html=True)
            return

        if st.button("요약 생성", type="primary", use_container_width=True):
            pipeline = get_pipeline()
            input_data = PipelineInput(
                query="학습 자료의 핵심 내용을 bullet point로 간결하게 요약해줘.",
                task_type=TaskType.SUMMARIZE,
                context_k=5,
                temperature=0.3
            )

            with st.spinner("요약 생성 중..."):
                result = pipeline.process(input_data)

            st.markdown("---")
            st.markdown(result.response)

    except Exception as e:
        st.error(f"오류: {e}")
