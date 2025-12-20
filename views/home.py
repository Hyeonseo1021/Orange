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
    "이 개념 설명해줘",
    "쉽게 요약해줘",
    "예시 들어줘",
    "핵심만 정리해줘"
]

def render():
    """홈 화면 렌더링"""
    
    # 1. DB 및 세션 초기화
    db.init_db()
    
    # 현재 세션 ID가 없으면 설정 (가장 최근 대화 or 새 대화)
    if "current_session_id" not in st.session_state:
        sessions = db.get_sessions()
        
        # [수정됨] 최근 대화방이 비어있으면 재사용, 대화가 있으면 새 방 만들기
        if sessions:
            last_id = sessions[0]["id"]
            last_msgs = db.load_messages(last_id)
            
            if not last_msgs:
                # 최근 방이 비어있음 -> 재사용 (Greeting 화면)
                st.session_state.current_session_id = last_id
            else:
                # 최근 방에 대화가 있음 -> 새 대화 시작 (Greeting 화면)
                st.session_state.current_session_id = db.create_session()
        else:
            # 방이 아예 없음 -> 생성
            st.session_state.current_session_id = db.create_session()
    
    _render_sidebar()

    # 선택된 세션의 메시지 불러오기
    session_id = st.session_state.current_session_id
    st.session_state.messages = db.load_messages(session_id)

    # 2. 화면 구성
    
    # 메시지가 없으면 인사말, 있으면 채팅창 표시
    if not st.session_state.messages:
        _render_greeting()
    else:
        _render_chat()


def _render_sidebar():
    """사이드바 - 대화 목록 (삭제 기능 추가됨)"""
    with st.sidebar:
        st.markdown("### 🍊 오렌지 튜터")
        
        # [1] 대화 목록
        st.markdown("### 💬 대화 목록")
        
        if st.button("+ 새 대화 시작", use_container_width=True):
            new_id = db.create_session()
            st.session_state.current_session_id = new_id
            st.session_state.messages = []
            st.rerun()
            
        st.markdown("<div style='height: 10px'></div>", unsafe_allow_html=True)
        
        sessions = db.get_sessions()
        
        if not sessions:
            st.caption("대화 기록이 없습니다.")
            
        for s in sessions:
            is_active = (s["id"] == st.session_state.get("current_session_id"))
            title_label = s['title'] if s['title'] and s['title'].strip() else "새로운 대화"
            
            col1, col2 = st.columns([0.9, 0.1])
            
            with col1:
                if st.button(
                    title_label, 
                    key=f"session_{s['id']}", 
                    use_container_width=True, # 제목은 꽉 차게
                    type="primary" if is_active else "secondary"
                ):
                    st.session_state.current_session_id = s["id"]
                    st.rerun()
            
            with col2:
                # ▼▼▼ [핵심 수정] use_container_width=False 로 변경! ▼▼▼
                # 이렇게 해야 흰색 박스가 안 생기고 글자 크기만큼만 작아집니다.
                with st.popover("⋮", use_container_width=False, help="옵션"):
                    
                    # 팝오버 메뉴 안의 내용
                    st.markdown("##### 현재 대화")
                    if st.button("🗑️ 삭제하기", key=f"del_{s['id']}", use_container_width=True):
                        db.delete_session(s['id'])
                        if is_active:
                             # 세션 초기화 로직
                             sessions = db.get_sessions()
                             if sessions:
                                 st.session_state.current_session_id = sessions[0]["id"]
                             else:
                                 st.session_state.current_session_id = db.create_session()
                             st.session_state.messages = []
                        st.rerun()

        st.divider()

        # --- [2] 자료 추가 섹션 (복구됨) ---
        st.markdown("### 자료 추가")
        uploaded = st.file_uploader(
            "파일 선택",
            type=["txt", "pdf", "png", "jpg"],
            label_visibility="collapsed"
        )
        if uploaded:
            if st.button("파일 업로드", type="primary", use_container_width=True):
                _add_file(uploaded)

        # --- [3] 저장된 자료 목록 (복구됨) ---
        try:
            rag = get_rag_system()
            sources = rag.get_sources()
            if sources:
                st.caption(f"저장된 자료 ({len(sources)}개)")
                for s in sources[:5]:
                    st.caption(f"• {s}")
                if len(sources) > 5:
                    st.caption(f"...외 {len(sources) - 5}개")
                
                # 자료 관리 페이지 이동 버튼
                if st.button("자료 전체 관리", use_container_width=True):
                    st.session_state.current_page = "study"
        except Exception:
            pass

        st.divider()

        # --- [4] 학습 도구 섹션 ---
        st.markdown("### 학습 도구")
        if st.button("퀴즈 풀기", use_container_width=True):
            st.session_state.current_page = "quiz"
 
        if st.button("복습 노트", use_container_width=True):
            st.session_state.current_page = "review"
            
        # 학습 현황 (선택사항)
        stats = st.session_state.get("study_stats", {"studied": 0, "accuracy": 0})
        if stats["studied"] > 0:
            st.caption(f"오늘 {stats['studied']}개의 질문을 공부했어요!")


def _render_greeting():
    """튜터 인사 화면 (수정됨: 답변이 넓게 나오도록)"""
    st.markdown("""
    <div class="tutor-greeting">
        <div class="tutor-avatar">🍊</div>
        <div class="tutor-message">안녕! 나는 오렌지야</div>
        <div class="tutor-sub">무엇이든 물어봐, 같이 공부하자!</div>
    </div>
    """, unsafe_allow_html=True)

    # 1. 어떤 버튼이 눌렸는지 확인하는 변수
    clicked_question = None

    # 2. 버튼들을 4개 컬럼으로 배치
    cols = st.columns(4)
    for i, q in enumerate(QUICK_QUESTIONS):
        with cols[i]:
            # 버튼이 눌리면 변수에 저장만 하고, 여기서 함수를 실행하지 않음!
            if st.button(q, key=f"quick_{i}", use_container_width=True):
                clicked_question = q

    # 3. 만약 눌린 버튼이 있다면, 컬럼 '밖'에서 넓게 실행
    if clicked_question:
        _handle_user_input(clicked_question)

    # 4. 하단 입력창
    prompt = st.chat_input("질문을 입력하세요...")
    if prompt:
        _handle_user_input(prompt)


def _render_chat():
    """채팅 화면"""
    # 대화 기록 표시
    for msg in st.session_state.messages:
        role = msg["role"]
        with st.chat_message(role, avatar="🍊" if role == "assistant" else None):
            st.markdown(msg["content"])

    # 하단 입력창
    prompt = st.chat_input("질문을 입력하세요...")
    if prompt:
        _handle_user_input(prompt)


def _handle_user_input(user_text):
    """사용자 입력 처리 (깜빡임 제거 버전)"""
    
    # 1. 사용자 메시지 저장 및 즉시 표시
    st.session_state.messages.append({"role": "user", "content": user_text})
    db.save_message(st.session_state.current_session_id, "user", user_text)
    
    with st.chat_message("user"):
        st.markdown(user_text)
    
    # 2. AI 답변 생성 및 표시
    with st.chat_message("assistant", avatar="🍊"):
        response = _generate_response(user_text)
        
        # 답변 저장
        st.session_state.messages.append({"role": "assistant", "content": response})
        db.save_message(st.session_state.current_session_id, "assistant", response)
        
        # 3. [수정됨] 제목 자동 요약 (백그라운드 처리 느낌으로 변경)
        # 사이드바 제목은 다음번 버튼 클릭이나 상호작용 때 업데이트됩니다.
        if len(st.session_state.messages) == 2:
            _generate_title_summary(user_text, response)


def _generate_title_summary(user_text, ai_text):
    """제목 요약 (안전장치 추가됨)"""
    try:
        # LLM 호출 (제목 생성용)
        llm = ChatOpenAI(
            model=MODEL,
            base_url=BASE_URL,
            api_key=API_KEY,
            temperature=0.5,
            max_tokens=30 # 토큰 수 제한
        )
        
        messages = [
            SystemMessage(content="사용자 질문과 너의 답변을 토대로 10자 이내의 명사형 제목으로 요약해. 예: '파이썬 기초', '시간 관리 방법'. 따옴표나 설명 없이 텍스트만 출력해."),
            HumanMessage(content=f"질문: {user_text}\n답변: {ai_text}")
        ]
        
        response = llm.invoke(messages)
        new_title = response.content.strip().replace('"', '').replace("'", "")
        
        if new_title and len(new_title) > 1 and len(new_title) < 20:
            db.update_session_title(st.session_state.current_session_id, new_title)
        else:
            print(f"제목 생성 실패(내용 부실): {new_title}")
        
    except Exception as e:
        # 오류 나면 그냥 넘어감 (기본 제목 '새로운 대화' 유지)
        print(f"제목 생성 건너뜀: {e}")


def _generate_response(prompt: str) -> str:
    """LLM 응답 생성 로직"""
    # RAG 검색
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
        pass # RAG 오류 시 그냥 진행

    # 프롬프트 구성
    formatted_system_prompt = SYSTEM_PROMPT.format(
        context=context if context else "관련된 학습 자료가 없습니다."
    )

    # 대화 기록 (최근 10개)
    chat_history = []
    for msg in st.session_state.messages[:-1]: # 현재 질문 제외
        if msg["role"] == "user":
            chat_history.append(HumanMessage(content=msg["content"]))
        else:
            chat_history.append(AIMessage(content=msg["content"]))
    chat_history = chat_history[-10:]

    # LLM 호출
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
    
    # 스트리밍 출력
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
        error_msg = f"죄송해요, 답변을 생성하는 중에 오류가 발생했어요. (오류: {e})"
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
        "title": title
    })

    if "study_stats" not in st.session_state:
        st.session_state.study_stats = {"studied": 0, "accuracy": 0, "review": 0}
    st.session_state.study_stats["studied"] += 1
