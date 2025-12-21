import streamlit as st
import database as db
import os
from dotenv import load_dotenv
from pathlib import Path

# AI 및 메시지 관련 임포트
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from rag import get_rag_system

# 환경 변수 로드
load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / ".env")

MODEL = os.getenv("MODEL", "qwen3-4b-2507")
BASE_URL = os.getenv("BASE_URL", "http://127.0.0.1:1234/v1")
API_KEY = os.getenv("API_KEY", "not-needed")

SYSTEM_PROMPT = """너는 '오렌지'라는 학습 튜터야.

[역할]
학습 자료를 바탕으로 질문에 답변해주는 튜터.

[원칙]
1. 질문에 대한 답변이 학습 자료에 있다면, 자료 내용을 최우선으로 인용하여 답변해.
2. 만약 학습 자료에 내용이 없다면, 너의 일반적인 배경지식을 활용하여 친절하게 답변해줘.
3. 배경지식으로 답변할 때는 "이 내용은 학습 자료에는 없지만..." 이라고 언급해줘.
4. 어려운 내용은 쉬운 예시로 설명해.

[학습 자료]
{context}
"""

QUICK_QUESTIONS = [
    "오늘 뭐 공부할까?",
    "어디서부터 시작할까?",
    "핵심 개념 알려줘",
    "퀴즈 내줘"
]

def render():
    """홈 화면 렌더링 (사이드바 유지 + 중앙 화면 전환)"""
    
    # 1. DB 및 세션 초기화
    db.init_db()
    
    # 2. 홈 화면 내부 모드 초기화 (기본값: chat)
    if "home_mode" not in st.session_state:
        st.session_state.home_mode = "chat"

    # 현재 세션 ID가 없으면 설정
    if "current_session_id" not in st.session_state:
        sessions = db.get_sessions()
        if sessions:
            last_id = sessions[0]["id"]
            last_msgs = db.load_messages(last_id)
            if not last_msgs:
                st.session_state.current_session_id = last_id
            else:
                st.session_state.current_session_id = db.create_session()
        else:
            st.session_state.current_session_id = db.create_session()
    
    # 3. 사이드바 렌더링 (항상 보임)
    _render_sidebar()

    # 4. 모드에 따라 메인 화면 컨텐츠 교체
    # Import를 여기서 수행하여 순환 참조 에러 방지
    mode = st.session_state.home_mode

    if mode == "chat":
        # [기본] 채팅 화면
        session_id = st.session_state.current_session_id
        st.session_state.messages = db.load_messages(session_id)
        
        if not st.session_state.messages:
            _render_greeting()
        else:
            _render_chat()
            
    elif mode == "study":
        st.subheader("📂 자료 관리 및 학습")
        try:
            from views import study
            study.render() 
        except Exception as e:
            st.error(f"학습 모듈 로드 오류: {e}")
            
    elif mode == "quiz":
        st.subheader("✍️ 퀴즈 풀기")
        try:
            from views import quiz
            quiz.render()
        except Exception as e:
            st.error(f"퀴즈 모듈 로드 오류: {e}")
            
    elif mode == "review":
        st.subheader("🔄 복습 노트")
        try:
            from views import review
            review.render()
        except Exception as e:
            st.error(f"복습 모듈 로드 오류: {e}")


def _render_sidebar():
    """사이드바 - 네비게이션 역할 수행"""
    with st.sidebar:
        # [1] 타이틀 및 새 대화
        st.markdown("### 🍊 오렌지 튜터")
        
        # '새 대화' 클릭 시 -> 채팅 모드로 복귀
        if st.button("+ 새 대화 시작", use_container_width=True):
            new_id = db.create_session()
            st.session_state.current_session_id = new_id
            st.session_state.messages = []
            st.session_state.home_mode = "chat" # 채팅 화면으로 전환
            st.rerun()
            
        st.markdown("<div style='height: 15px'></div>", unsafe_allow_html=True)
        st.caption("대화 목록")

        sessions = db.get_sessions()
        
        if not sessions:
            st.caption("대화 기록이 없습니다.")
            
        # [2] 대화 목록 (클릭 시 채팅 모드로 전환)
        for s in sessions:
            # 현재 세션이고 + 채팅 모드일 때만 활성화 표시
            is_active = (s["id"] == st.session_state.get("current_session_id")) and (st.session_state.home_mode == "chat")
            title_label = s['title'] if s['title'] and s['title'].strip() else "새로운 대화"
            
            c_title, c_delete = st.columns([0.85, 0.15], gap="small")
            
            with c_title:
                if st.button(
                    title_label, 
                    key=f"session_{s['id']}", 
                    use_container_width=True,
                    type="primary" if is_active else "secondary"
                ):
                    st.session_state.current_session_id = s["id"]
                    st.session_state.home_mode = "chat" # ★ 채팅 모드로 강제 전환
                    st.rerun()
            
            with c_delete:
                if st.button("✕", key=f"del_{s['id']}", use_container_width=True, help="대화 삭제"):
                    db.delete_session(s['id'])
                    remain = db.get_sessions()
                    if remain:
                         st.session_state.current_session_id = remain[0]["id"]
                    else:
                         st.session_state.current_session_id = db.create_session()
                    st.session_state.messages = []
                    st.session_state.home_mode = "chat"
                    st.rerun()
        
        st.divider()

        # [3] 자료 추가
        st.markdown("### 자료 추가")
        uploaded = st.file_uploader(
            "파일 선택",
            type=["txt", "pdf", "png", "jpg"],
            label_visibility="collapsed"
        )
        if uploaded:
            if st.button("파일 업로드", type="primary", use_container_width=True):
                _add_file(uploaded)

        # [4] 자료 관리 메뉴 (클릭 시 학습 모드로 전환)
        try:
            rag = get_rag_system()
            sources = rag.get_sources()
            if sources:
                st.caption(f"저장된 자료 ({len(sources)}개)")
                if st.button("📂 자료 전체 관리", use_container_width=True):
                    st.session_state.home_mode = "study" # 화면 전환
                    st.rerun()
        except Exception:
            pass

        st.divider()

        # [5] 학습 도구 메뉴 (클릭 시 각 모드로 전환)
        st.markdown("### 학습 도구")
        
        if st.button("✍️ 퀴즈 풀기", use_container_width=True):
            st.session_state.home_mode = "quiz" # 화면 전환
            st.rerun()
 
        if st.button("🔄 복습 노트", use_container_width=True):
            st.session_state.home_mode = "review" # 화면 전환
            st.rerun()
            
        stats = st.session_state.get("study_stats", {"studied": 0, "accuracy": 0})
        if stats["studied"] > 0:
            st.caption(f"오늘 {stats['studied']}개의 질문을 공부했어요!")


def _render_greeting():
    """튜터 인사 화면"""
    st.markdown("""
    <div class="tutor-greeting">
        <div class="tutor-avatar">🍊</div>
        <div class="tutor-message">안녕! 나는 오렌지야</div>
        <div class="tutor-sub">무엇이든 물어봐, 같이 공부하자!</div>
    </div>
    """, unsafe_allow_html=True)

    clicked_question = None
    cols = st.columns(4)
    for i, q in enumerate(QUICK_QUESTIONS):
        with cols[i]:
            if st.button(q, key=f"quick_{i}", use_container_width=True):
                clicked_question = q

    if clicked_question:
        _handle_user_input(clicked_question)

    prompt = st.chat_input("질문을 입력하세요...")
    if prompt:
        _handle_user_input(prompt)


def _render_chat():
    """채팅 화면"""
    for msg in st.session_state.messages:
        role = msg["role"]
        with st.chat_message(role, avatar="🍊" if role == "assistant" else None):
            st.markdown(msg["content"])

    prompt = st.chat_input("질문을 입력하세요...")
    if prompt:
        _handle_user_input(prompt)


def _handle_user_input(user_text):
    """사용자 입력 처리"""
    st.session_state.messages.append({"role": "user", "content": user_text})
    db.save_message(st.session_state.current_session_id, "user", user_text)
    
    with st.chat_message("user"):
        st.markdown(user_text)
    
    with st.chat_message("assistant", avatar="🍊"):
        response = _generate_response(user_text)
        st.session_state.messages.append({"role": "assistant", "content": response})
        db.save_message(st.session_state.current_session_id, "assistant", response)
        
        if len(st.session_state.messages) == 2:
            _generate_title_summary(user_text, response)


def _generate_title_summary(user_text, ai_text):
    """제목 요약"""
    try:
        llm = ChatOpenAI(
            model=MODEL,
            base_url=BASE_URL,
            api_key=API_KEY,
            temperature=0.5,
            max_tokens=30
        )
        messages = [
            SystemMessage(content="10자 이내의 명사형 제목으로 요약해. 예: '파이썬 기초'."),
            HumanMessage(content=f"질문: {user_text}\n답변: {ai_text}")
        ]
        response = llm.invoke(messages)
        new_title = response.content.strip().replace('"', '').replace("'", "")
        if new_title and 1 < len(new_title) < 20:
            db.update_session_title(st.session_state.current_session_id, new_title)
    except Exception as e:
        print(f"제목 생성 건너뜀: {e}")


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
    except Exception:
        pass

    formatted_system_prompt = SYSTEM_PROMPT.format(
        context=context if context else "관련된 학습 자료가 없습니다."
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
        ("system", formatted_system_prompt),
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
        return full_response

    except Exception as e:
        error_msg = f"오류 발생: {e}"
        response_placeholder.error(error_msg)
        return error_msg
    

def _add_file(uploaded):
    """파일 추가 로직"""
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
        st.session_state.home_mode = "study" # 추가 후 자료 관리 화면으로 자동 이동
        st.rerun()

    except Exception as e:
        st.error(f"오류: {e}")


def add_study_history(title: str):
    if "study_history" not in st.session_state:
        st.session_state.study_history = []
    st.session_state.study_history.append({"title": title})
    if "study_stats" not in st.session_state:
        st.session_state.study_stats = {"studied": 0, "accuracy": 0, "review": 0}
    st.session_state.study_stats["studied"] += 1