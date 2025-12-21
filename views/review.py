# -*- coding: utf-8 -*-
"""
복습 화면
"""

import streamlit as st
import database as db  # DB 연동
from rag import get_rag_system
from pipeline import get_pipeline, PipelineInput, TaskType


def render():
    """복습 화면"""
    st.markdown("""
    <div class="page-header">
        <span class="page-title">📝 복습 노트</span>
    </div>
    """, unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["❌ 오답 노트", "📑 핵심 요약"])

    with tab1:
        _render_wrong_db()

    with tab2:
        _render_summary_selector()


def _render_wrong_db():
    """DB 기반 오답 노트"""
    # DB에서 미완료된 오답 노트 가져오기
    notes = db.get_review_notes(only_unreviewed=True)

    if not notes:
        st.markdown("""
        <div style="text-align: center; padding: 3rem; color: #AAA;">
            <div style="font-size: 2rem; margin-bottom: 0.5rem;">✨</div>
            <div>복습할 오답이 없어요!</div>
            <div style="font-size: 0.85rem; margin-top: 0.3rem;">퀴즈를 풀면 틀린 문제가 여기에 자동으로 쌓여요.</div>
        </div>
        """, unsafe_allow_html=True)
        return

    st.info(f"복습할 문제가 {len(notes)}개 있습니다.")

    for note in notes:
        with st.expander(f"Q. {note['question'][:40]}...", expanded=True):
            st.markdown(f"**문제:** {note['question']}")
            col1, col2 = st.columns(2)
            with col1:
                st.error(f"내 답: {note['my_answer']}")
            with col2:
                st.success(f"정답: {note['correct_answer']}")
            
            if note['explanation']:
                st.info(f"💡 해설: {note['explanation']}")
            
            # 완료 버튼
            if st.button("복습 완료 (목록에서 제거)", key=f"rev_{note['id']}", use_container_width=True):
                db.mark_reviewed(note['id'])
                st.rerun()


def _render_summary_selector():
    """자료 선택 후 요약 생성"""
    rag = get_rag_system()
    sources = rag.get_sources()

    if not sources:
        st.warning("등록된 학습 자료가 없습니다. 먼저 자료를 추가해주세요.")
        return

    st.markdown("### 📄 요약할 자료 선택")
    
    # 1. 자료 선택 (멀티 셀렉트 대신 단일 선택이 요약 품질에 더 유리함)
    selected_source = st.selectbox(
        "어떤 자료를 요약할까요?", 
        options=["전체 자료 통합 요약"] + sources
    )

    # 2. 요약 버튼
    if st.button("✨ 요약 생성하기", type="primary", use_container_width=True):
        pipeline = get_pipeline()
        
        # 프롬프트 구성
        if selected_source == "전체 자료 통합 요약":
            query_text = "저장된 모든 학습 자료의 핵심 내용을 주제별로 정리해서 요약해줘."
        else:
            query_text = f"학습 자료 중 문서 '{selected_source}'의 내용을 중심으로 핵심을 요약해줘."

        input_data = PipelineInput(
            query=query_text,
            task_type=TaskType.SUMMARIZE,
            context_k=7,  # 요약은 더 많은 컨텍스트 필요
            temperature=0.3
        )

        with st.spinner(f"'{selected_source}' 요약 중..."):
            result = pipeline.process(input_data)

        st.markdown("---")
        st.subheader("📝 요약 결과")
        st.markdown(result.response)