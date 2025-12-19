# -*- coding: utf-8 -*-
"""
홈 화면 - 튜터 중심 메인 화면
"""

import streamlit as st
from datetime import datetime
from rag import get_rag_system
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / ".env")

MODEL = os.getenv("MODEL", "qwen3-4b-2507")
BASE_URL = os.getenv("BASE_URL", "http://127.0.0.1:1234/v1")
API_KEY = os.getenv("API_KEY", "not-needed")

SYSTEM_PROMPT = """너는 '오렌지'라는 학습 튜터야.

[역할]
학습 자료를 바탕으로 질문에 답변해주는 튜터.

[원칙]
1. 학습 자료에 있는 내용을 기반으로 답변해
2. 자료에 없는 내용은 솔직하게 말해줘
3. 어려운 내용은 쉬운 예시로 설명해
4. 답변은 구조화해서 읽기 쉽게

[학습 자료]
{context}
"""

QUICK_QUESTIONS = [
    "이 개념 설명해줘",
    "쉽게 요약해줘",
    "예시 들어줘",
    "핵심만 정리해줘"
]


def render():
    """홈 화면 렌더링"""

    # 사이드바
    _render_sidebar()

    # 메인 영역
    if "messages" not in st.session_state:
        st.session_state.messages = []

    if not st.session_state.messages:
        _render_greeting()
    else:
        _render_chat()


def _render_sidebar():
    """사이드바 - 자료/퀴즈/복습"""
    with st.sidebar:
        st.markdown("### 🍊 오렌지 튜터")

        st.divider()

        # 자료 추가
        st.markdown("**자료 추가**")
        uploaded = st.file_uploader(
            "파일 선택",
            type=["txt", "pdf", "png", "jpg"],
            label_visibility="collapsed"
        )
        if uploaded:
            if st.button("추가", type="primary", use_container_width=True):
                _add_file(uploaded)

        # 저장된 자료
        try:
            rag = get_rag_system()
            sources = rag.get_sources()
            if sources:
                st.markdown("**저장된 자료**")
                for s in sources[:5]:
                    st.caption(f"• {s}")
                if len(sources) > 5:
                    st.caption(f"외 {len(sources) - 5}개")

                if st.button("자료 관리", use_container_width=True):
                    st.session_state.current_page = "study"
                    st.rerun()
        except:
            pass

        st.divider()

        # 학습 도구
        st.markdown("**학습 도구**")

        if st.button("퀴즈 풀기", use_container_width=True):
            st.session_state.current_page = "quiz"
            st.rerun()

        if st.button("복습 노트", use_container_width=True):
            st.session_state.current_page = "review"
            st.rerun()

        st.divider()

        # 학습 현황
        stats = st.session_state.get("study_stats", {"studied": 0, "accuracy": 0, "review": 0})
        col1, col2 = st.columns(2)
        with col1:
            st.metric("질문", stats["studied"])
        with col2:
            st.metric("정답률", f"{stats['accuracy']}%")


def _render_greeting():
    """튜터 인사 화면"""

    st.markdown("""
    <div class="tutor-greeting">
        <div class="tutor-avatar">🍊</div>
        <div class="tutor-message">안녕! 나는 오렌지야</div>
        <div class="tutor-sub">무엇이든 물어봐, 같이 공부하자!</div>
    </div>
    """, unsafe_allow_html=True)

    # 빠른 질문
    st.markdown("<br>", unsafe_allow_html=True)
    cols = st.columns(4)
    for i, q in enumerate(QUICK_QUESTIONS):
        with cols[i]:
            if st.button(q, key=f"quick_{i}", use_container_width=True):
                st.session_state.messages.append({"role": "user", "content": q})
                st.rerun()

    # 입력창
    prompt = st.chat_input("질문을 입력하세요...")
    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.rerun()


def _render_chat():
    """채팅 화면"""

    # 대화 기록
    for msg in st.session_state.messages:
        role = msg["role"]
        with st.chat_message(role, avatar="🍊" if role == "assistant" else None):
            st.markdown(msg["content"])

    # 응답 생성
    if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
        with st.chat_message("assistant", avatar="🍊"):
            response = _generate_response(st.session_state.messages[-1]["content"])
            st.session_state.messages.append({"role": "assistant", "content": response})

    # 입력창
    prompt = st.chat_input("질문을 입력하세요...")
    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.rerun()

    # 새 대화 버튼
    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("새 대화", use_container_width=True):
            st.session_state.messages = []
            st.rerun()


def _generate_response(prompt: str) -> str:
    """LLM 응답 생성"""
    context = ""
    try:
        rag = get_rag_system()
        docs = rag.search(prompt, k=3)
        if docs:
            context_parts = []
            for i, doc in enumerate(docs, 1):
                source = doc.metadata.get("source", "unknown")
                context_parts.append(f"[{i}] ({source})\n{doc.page_content}")
            context = "\n\n".join(context_parts)
    except:
        pass

    system_prompt = SYSTEM_PROMPT.format(
        context=context if context else "등록된 학습 자료가 없습니다."
    )

    chat_history = []
    for msg in st.session_state.messages[:-1]:
        if msg["role"] == "user":
            chat_history.append(HumanMessage(content=msg["content"]))
        else:
            chat_history.append(AIMessage(content=msg["content"]))
    chat_history = chat_history[-10:]

    llm = ChatOpenAI(
        model=MODEL,
        base_url=BASE_URL,
        api_key=API_KEY,
        temperature=0.4,
        streaming=True
    )

    prompt_template = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{user_input}")
    ])

    chain = prompt_template | llm
    response_placeholder = st.empty()
    full_response = ""

    try:
        for chunk in chain.stream({
            "chat_history": chat_history,
            "user_input": prompt
        }):
            if chunk.content:
                full_response += chunk.content
                response_placeholder.markdown(full_response + " ▌")

        response_placeholder.markdown(full_response)
        add_study_history(f"질문: {prompt[:20]}...")
        return full_response

    except Exception as e:
        error_msg = "잠시 문제가 생겼어. LLM 서버 상태를 확인해줘!"
        response_placeholder.error(error_msg)
        return error_msg


def _add_file(uploaded):
    """사이드바에서 파일 추가"""
    try:
        rag = get_rag_system()
        name = uploaded.name
        ext = name.lower().split(".")[-1]

        with st.spinner("처리 중..."):
            if ext == "txt":
                content = uploaded.read().decode("utf-8")
                rag.add_document(content, metadata={"source": name, "type": "txt"})
            elif ext == "pdf":
                rag.add_pdf(uploaded, name, use_ocr=True)
            elif ext in ["png", "jpg", "jpeg"]:
                rag.add_image(uploaded, name)

        st.success(f"'{name}' 추가됨")
        add_study_history(f"자료: {name}")
        st.rerun()

    except Exception as e:
        st.error(f"오류: {e}")


def add_study_history(title: str):
    """학습 기록 추가"""
    if "study_history" not in st.session_state:
        st.session_state.study_history = []

    st.session_state.study_history.append({
        "date": datetime.now().strftime("%m/%d %H:%M"),
        "title": title
    })

    if "study_stats" not in st.session_state:
        st.session_state.study_stats = {"studied": 0, "accuracy": 0, "review": 0}
    st.session_state.study_stats["studied"] += 1
