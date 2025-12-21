# -*- coding: utf-8 -*-
"""
자료 관리 화면
"""

import streamlit as st
from rag import get_rag_system
from views.home import add_study_history


def render():
    """자료 관리 화면"""

    st.markdown("""
    <div class="page-header">
        <span class="page-title">📚 학습 자료</span>
    </div>
    """, unsafe_allow_html=True)

    # 자료 업로드
    tab1, tab2 = st.tabs(["파일 업로드", "직접 입력"])

    with tab1:
        uploaded_file = st.file_uploader(
            "PDF, TXT, 이미지 파일",
            type=["txt", "pdf", "png", "jpg", "jpeg"],
            label_visibility="collapsed"
        )

        if uploaded_file:
            use_ocr = st.checkbox("OCR 사용", value=True, help="스캔된 문서나 이미지에서 텍스트 추출")

            if st.button("추가하기", type="primary", use_container_width=True):
                _upload_file(uploaded_file, use_ocr)

    with tab2:
        text = st.text_area("학습할 내용", height=120, placeholder="여기에 텍스트를 붙여넣으세요")
        title = st.text_input("제목", placeholder="예: 파이썬 기초")

        if st.button("추가", type="primary", use_container_width=True) and text.strip():
            _add_text(text, title)

    st.markdown("<br>", unsafe_allow_html=True)

    # 저장된 자료
    st.markdown("**저장된 자료**")

    try:
        rag = get_rag_system()
        sources = rag.get_sources()
        stats = rag.get_collection_stats()

        if sources:
            # 태그 형식으로 표시
            tags_html = "".join([f'<span class="source-tag">{s}</span>' for s in sources])
            st.markdown(f'<div class="source-tags">{tags_html}</div>', unsafe_allow_html=True)
            st.caption(f"{stats['count']}개 조각으로 분할됨")

            if st.button("전체 삭제", type="secondary"):
                if st.session_state.get("confirm_clear"):
                    rag.clear()
                    st.session_state.confirm_clear = False
                    st.rerun()
                else:
                    st.session_state.confirm_clear = True
                    st.warning("다시 클릭하면 삭제됩니다")
        else:
            st.markdown("""
            <div style="text-align: center; padding: 2rem; color: #AAA; font-size: 0.9rem;">
                아직 학습 자료가 없어요
            </div>
            """, unsafe_allow_html=True)

    except Exception as e:
        st.error(f"오류: {e}")


def _upload_file(file, use_ocr: bool):
    """파일 업로드 처리"""
    try:
        rag = get_rag_system()
        name = file.name
        ext = name.lower().split(".")[-1]

        with st.spinner("처리 중..."):
            if ext == "txt":
                content = file.read().decode("utf-8")
                rag.add_document(content, metadata={"source": name, "type": "txt"})
            elif ext == "pdf":
                rag.add_pdf(file, name, use_ocr=use_ocr)
            elif ext in ["png", "jpg", "jpeg"]:
                rag.add_image(file, name)

        st.success(f"'{name}' 추가됨")
        add_study_history(f"자료: {name}")
        st.rerun()

    except Exception as e:
        st.error(f"오류: {e}")


def _add_text(text: str, title: str):
    """텍스트 추가"""
    try:
        rag = get_rag_system()
        source = title.strip() if title.strip() else "직접입력"
        rag.add_document(text, metadata={"source": source, "type": "manual"})
        st.success("추가됨")
        add_study_history(f"자료: {source}")
        st.rerun()
    except Exception as e:
        st.error(f"오류: {e}")
