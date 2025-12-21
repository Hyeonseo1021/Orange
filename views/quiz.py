# -*- coding: utf-8 -*-
"""
퀴즈 화면
"""

import streamlit as st
import json
from rag import get_rag_system
from pipeline import get_pipeline, PipelineInput, TaskType


def render():
    """퀴즈 화면"""


    st.markdown("""
    <div class="page-header">
        <span class="page-title">✏️ 퀴즈</span>
    </div>
    """, unsafe_allow_html=True)

    # 퀴즈 상태
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


def _render_start():
    """퀴즈 시작 화면"""

    st.markdown("""
    <div style="text-align: center; padding: 2rem;">
        <div style="font-size: 2.5rem; margin-bottom: 0.5rem;">✏️</div>
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

형식:
[{{"question": "질문", "options": ["A", "B", "C", "D"], "answer": 0, "explanation": "설명"}}]

answer는 정답 인덱스(0-3). JSON만 출력해."""

        input_data = PipelineInput(
            query=prompt,
            task_type=TaskType.QA,
            context_k=5,
            temperature=0.7
        )

        with st.spinner("퀴즈 생성 중..."):
            result = pipeline.process(input_data)

        # JSON 파싱
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
            "generated": True
        }
        st.rerun()

    except json.JSONDecodeError:
        st.error("퀴즈 생성에 실패했어요. 다시 시도해주세요.")
    except Exception as e:
        st.error(f"오류: {e}")


def _render_question():
    """문제 화면"""
    state = st.session_state.quiz_state
    idx = state["current"]
    total = len(state["questions"])
    q = state["questions"][idx]

    # 진행바
    progress = (idx + 1) / total
    st.markdown(f"""
    <div style="margin-bottom: 1.5rem;">
        <div style="display: flex; justify-content: space-between; font-size: 0.85rem; color: #888; margin-bottom: 0.5rem;">
            <span>{idx + 1} / {total}</span>
            <span>{int(progress * 100)}%</span>
        </div>
        <div class="progress-wrap">
            <div class="progress-fill" style="width: {progress * 100}%"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 질문
    st.markdown(f"**{q['question']}**")
    st.markdown("<br>", unsafe_allow_html=True)

    # 선택지
    selected = state["answers"][idx]
    for i, opt in enumerate(q["options"]):
        label = ["A", "B", "C", "D"][i]
        is_sel = selected == i

        if st.button(
            f"{label}. {opt}",
            key=f"opt_{idx}_{i}",
            use_container_width=True,
            type="primary" if is_sel else "secondary"
        ):
            state["answers"][idx] = i
            st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    # 네비게이션
    col1, col2 = st.columns(2)
    with col1:
        if idx > 0 and st.button("← 이전", use_container_width=True):
            state["current"] -= 1
            st.rerun()
    with col2:
        if idx < total - 1:
            if st.button("다음 →", use_container_width=True):
                if state["answers"][idx] is not None:
                    state["current"] += 1
                    st.rerun()
                else:
                    st.warning("답을 선택해주세요")
        else:
            if st.button("완료", type="primary", use_container_width=True):
                if None in state["answers"]:
                    st.warning("모든 문제에 답해주세요")
                else:
                    _submit()


def _submit():
    """제출"""
    state = st.session_state.quiz_state
    questions = state["questions"]
    answers = state["answers"]

    score = 0
    wrong = []

    for i, (q, a) in enumerate(zip(questions, answers)):
        if a == q["answer"]:
            score += 1
        else:
            wrong.append({
                "question": q["question"],
                "your_answer": q["options"][a],
                "correct_answer": q["options"][q["answer"]],
                "explanation": q.get("explanation", "")
            })

    state["score"] = score
    state["current"] = len(questions)

    # 오답 저장
    if wrong:
        if "wrong_notes" not in st.session_state:
            st.session_state.wrong_notes = []
        st.session_state.wrong_notes.extend(wrong)

    # 통계
    if "study_stats" not in st.session_state:
        st.session_state.study_stats = {"studied": 0, "accuracy": 0, "review": 0}

    acc = int(score / len(questions) * 100) if questions else 0
    st.session_state.study_stats["accuracy"] = acc
    st.session_state.study_stats["review"] = len(wrong)

    st.rerun()


def _render_result():
    """결과 화면"""
    state = st.session_state.quiz_state
    score = state["score"]
    total = len(state["questions"])
    acc = int(score / total * 100) if total else 0

    # 결과
    emoji = "🎉" if acc >= 80 else "💪" if acc >= 50 else "📚"
    st.markdown(f"""
    <div style="text-align: center; padding: 2rem;">
        <div style="font-size: 3rem;">{emoji}</div>
        <div style="font-size: 2.5rem; font-weight: 700; color: #FF6B35; margin: 0.5rem 0;">{acc}%</div>
        <div style="color: #888;">{total}문제 중 {score}문제 정답</div>
    </div>
    """, unsafe_allow_html=True)

    # 문제별 결과
    with st.expander("문제별 결과 보기"):
        for i, q in enumerate(state["questions"]):
            ans = state["answers"][i]
            correct = ans == q["answer"]
            icon = "✓" if correct else "✗"
            color = "#27AE60" if correct else "#E74C3C"

            st.markdown(f"**{icon} {q['question'][:40]}...**")
            if not correct:
                st.caption(f"내 답: {q['options'][ans]} → 정답: {q['options'][q['answer']]}")
            st.markdown("---")

    # 버튼
    col1, col2 = st.columns(2)
    with col1:
        if st.button("다시 풀기", use_container_width=True):
            st.session_state.quiz_state = {
                "questions": [],
                "current": 0,
                "answers": [],
                "score": 0,
                "generated": False
            }
            st.rerun()
   
