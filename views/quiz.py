# -*- coding: utf-8 -*-
"""
퀴즈 화면
"""

import streamlit as st
import json
import database as db  # DB 연동
from rag import get_rag_system
from pipeline import get_pipeline, PipelineInput, TaskType
from datetime import datetime

def render():
    """퀴즈 화면"""
    st.markdown("""
    <div class="page-header">
        <span class="page-title">✏️ 퀴즈</span>
    </div>
    """, unsafe_allow_html=True)

    # 탭 구성: 퀴즈 풀기 / 퀴즈 기록
    tab1, tab2 = st.tabs(["퀴즈 풀기", "푼 퀴즈 목록"])

    with tab1:
        _render_quiz_interface()
    
    with tab2:
        _render_history()


def _render_quiz_interface():
    """퀴즈 풀기 인터페이스"""
    if "quiz_state" not in st.session_state:
        st.session_state.quiz_state = {
            "questions": [],
            "current": 0,
            "answers": [],
            "score": 0,
            "generated": False
        }

    state = st.session_state.quiz_state

    if not state["generated"]:
        _render_start()
    elif state["current"] < len(state["questions"]):
        _render_question()
    else:
        _render_result()


def _render_history():
    """[추가됨] 푼 퀴즈 목록 표시"""
    results = db.get_quiz_results()
    
    if not results:
        st.info("아직 푼 퀴즈가 없습니다.")
        return

    # 데이터프레임 대신 깔끔한 리스트로 표시
    for r in results:
        # 날짜 포맷팅
        dt = datetime.strptime(r['created_at'], "%Y-%m-%d %H:%M:%S")
        date_str = dt.strftime("%Y-%m-%d %H:%M")
        
        # 점수에 따른 아이콘
        score_pct = (r['score'] / r['total']) * 100
        icon = "🏆" if score_pct >= 80 else "📝"
        
        with st.container():
            col1, col2, col3 = st.columns([1, 2, 1])
            with col1:
                st.write(f"**{icon} {date_str}**")
            with col2:
                st.write(f"주제: {r['topic']}")
            with col3:
                st.write(f"**{r['score']} / {r['total']}** 점")
            st.divider()


def _render_start():
    """퀴즈 시작 화면"""
    st.markdown("""
    <div style="text-align: center; padding: 2rem;">
        <div style="font-size: 2.5rem; margin-bottom: 0.5rem;">🎯</div>
        <div style="font-size: 1rem; color: #666;">학습 자료 기반 퀴즈</div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        num = st.selectbox("문제 수", [3, 5, 10], index=0)
    with col2:
        diff = st.selectbox("난이도", ["쉬움", "보통", "어려움"], index=1)

    if st.button("시작하기", type="primary", use_container_width=True):
        _generate_quiz(num, diff)


def _generate_quiz(num: int, diff: str):
    """퀴즈 생성"""
    try:
        pipeline = get_pipeline()
        prompt = f"""학습 자료 기반 {diff} 난이도 4지선다 퀴즈 {num}개를 JSON으로 만들어줘.
        형식: [{{"question": "질문", "options": ["A", "B", "C", "D"], "answer": 0, "explanation": "설명"}}]
        answer는 정답 인덱스(0-3). JSON만 출력해."""

        input_data = PipelineInput(query=prompt, task_type=TaskType.QA, context_k=5, temperature=0.7)

        with st.spinner("퀴즈 생성 중..."):
            result = pipeline.process(input_data)

        response = result.response.strip()
        if "```json" in response:
            response = response.split("```json")[1].split("```")[0]
        elif "```" in response:
            response = response.split("```")[1].split("```")[0]

        questions = json.loads(response)

        st.session_state.quiz_state = {
            "questions": questions,
            "current": 0,
            "answers": [None] * len(questions),
            "score": 0,
            "generated": True,
            "diff_label": diff # 난이도 저장 (토픽용)
        }
        st.rerun()

    except Exception:
        st.error("퀴즈 생성 실패. 다시 시도해주세요.")


def _render_question():
    """문제 화면"""
    state = st.session_state.quiz_state
    idx = state["current"]
    total = len(state["questions"])
    q = state["questions"][idx]

    progress = (idx + 1) / total
    st.progress(progress, text=f"{idx + 1} / {total}")

    st.markdown(f"**Q. {q['question']}**")

    selected = state["answers"][idx]
    for i, opt in enumerate(q["options"]):
        if st.button(f"{['A','B','C','D'][i]}. {opt}", key=f"opt_{idx}_{i}", use_container_width=True, type="primary" if selected == i else "secondary"):
            state["answers"][idx] = i
            st.rerun()

    col1, col2 = st.columns(2)
    with col1:
        if idx > 0 and st.button("이전"):
            state["current"] -= 1
            st.rerun()
    with col2:
        if idx < total - 1:
            if st.button("다음"):
                if state["answers"][idx] is not None:
                    state["current"] += 1
                    st.rerun()
                else:
                    st.warning("답을 선택해주세요")
        else:
            if st.button("제출", type="primary"):
                if None in state["answers"]:
                    st.warning("모든 문제에 답해주세요")
                else:
                    _submit()


def _submit():
    """제출 및 DB 저장"""
    state = st.session_state.quiz_state
    questions = state["questions"]
    answers = state["answers"]
    score = 0
    
    # 채점
    for i, (q, a) in enumerate(zip(questions, answers)):
        is_correct = (a == q["answer"])
        if is_correct:
            score += 1
        else:
            # 오답 노트 DB 저장
            db.add_review_note(
                question=q["question"],
                correct_answer=q["options"][q["answer"]],
                my_answer=q["options"][a],
                explanation=q.get("explanation", "")
            )

    # 퀴즈 결과 DB 저장
    topic = f"{state.get('diff_label', '보통')} 난이도 퀴즈"
    db.save_quiz_result(score, len(questions), topic)

    # 상태 업데이트
    state["score"] = score
    state["current"] = len(questions) # 결과 화면으로 이동
    st.rerun()


def _render_result():
    """결과 화면"""
    state = st.session_state.quiz_state
    score = state["score"]
    total = len(state["questions"])
    acc = int(score / total * 100) if total else 0

    st.balloons() if acc >= 80 else None

    st.markdown(f"""
    <div style="text-align: center; padding: 2rem;">
        <div style="font-size: 3rem;">{'🎉' if acc >= 80 else '💪'}</div>
        <div style="font-size: 2.5rem; font-weight: 700; color: #FF6B35;">{acc}점</div>
        <div style="color: #666;">{total}문제 중 {score}문제 정답</div>
        <div style="margin-top: 10px; font-size: 0.9rem; color: #888;">오답은 자동으로 복습 노트에 저장되었습니다.</div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("다시 풀기", use_container_width=True):
        st.session_state.quiz_state = {"questions": [], "current": 0, "answers": [], "score": 0, "generated": False}
        st.rerun()