# -*- coding: utf-8 -*-
"""
통합 파이프라인 모듈 (Integrated Pipeline Module)
- 문서 요약 + Q&A를 하나의 프로세스로 통합
- 입력 데이터 처리 및 출력 포맷 정규화
- 성능 테스트 및 품질 측정
"""

import os
import time
from typing import List, Dict, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.documents import Document

from rag import get_rag_system, RAGSystem

# Load environment variables
load_dotenv(dotenv_path=Path(__file__).resolve().parent / ".env")

# Settings
MODEL = os.getenv("MODEL", "qwen3-4b-2507")
BASE_URL = os.getenv("BASE_URL", "http://127.0.0.1:1234/v1")
API_KEY = os.getenv("API_KEY", "not-needed")


class TaskType(Enum):
    """작업 유형 열거형"""
    SUMMARIZE = "summarize"
    QA = "qa"
    CONCEPT = "concept"
    COMPARE = "compare"
    APPLY = "apply"


@dataclass
class PipelineInput:
    """파이프라인 입력 데이터 구조"""
    query: str
    task_type: TaskType = TaskType.QA
    context_k: int = 3
    max_tokens: int = 1024
    temperature: float = 0.4
    chat_history: List[Dict[str, str]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "query": self.query,
            "task_type": self.task_type.value,
            "context_k": self.context_k,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "history_length": len(self.chat_history)
        }


@dataclass
class PipelineOutput:
    """파이프라인 출력 데이터 구조"""
    response: str
    sources: List[Dict[str, str]]
    task_type: TaskType
    metrics: Dict[str, Any]
    raw_context: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "response": self.response,
            "sources": self.sources,
            "task_type": self.task_type.value,
            "metrics": self.metrics,
            "has_context": bool(self.raw_context)
        }


@dataclass
class TestResult:
    """성능 테스트 결과"""
    query: str
    task_type: TaskType
    response_time_ms: float
    token_count: int
    context_relevance: float  # 0.0 ~ 1.0
    response_quality: Dict[str, Any]
    success: bool
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "query": self.query,
            "task_type": self.task_type.value,
            "response_time_ms": round(self.response_time_ms, 2),
            "token_count": self.token_count,
            "context_relevance": round(self.context_relevance, 3),
            "response_quality": self.response_quality,
            "success": self.success,
            "error": self.error
        }


# 작업 유형별 최적화된 프롬프트
TASK_PROMPTS = {
    TaskType.SUMMARIZE: """당신은 문서 요약 전문가입니다.

<지침>
1. 핵심 내용을 빠짐없이 추출하세요
2. 불필요한 수식어나 반복은 제거하세요
3. 논리적 구조를 유지하며 요약하세요
4. 원문의 의도와 맥락을 보존하세요
</지침>

<출력 형식>
## 핵심 요약
- [핵심 포인트 1]
- [핵심 포인트 2]
- [핵심 포인트 3]

## 주요 내용
[상세 요약 내용]

## 키워드
[관련 키워드 나열]
</출력 형식>

<학습 자료>
{context}
</학습 자료>

위 자료를 기반으로 요약해주세요.""",

    TaskType.QA: """당신은 학습 자료 기반 Q&A 전문가 '오렌지'입니다.

<지침>
1. 제공된 학습 자료를 기반으로만 답변하세요
2. 자료에 없는 내용은 추측하지 말고 솔직히 안내하세요
3. 출처를 명확히 밝히세요
4. 이해하기 쉽게 설명하세요
</지침>

<출력 형식>
[질문에 대한 직접적인 답변]

**근거:**
- [출처1]: [관련 내용]
- [출처2]: [관련 내용]

**추가 설명:** (필요시)
[보충 설명]
</출력 형식>

<학습 자료>
{context}
</학습 자료>

위 자료를 바탕으로 질문에 답변해주세요.
자료에 관련 내용이 없다면 "현재 학습 자료에는 해당 내용이 없습니다."라고 안내해주세요.""",

    TaskType.CONCEPT: """당신은 개념 설명 전문가 '오렌지'입니다.

<지침>
1. 정의를 먼저 명확히 제시하세요
2. 핵심 포인트를 구조화하여 설명하세요
3. 이해를 돕는 예시를 포함하세요
4. 어려운 용어는 쉽게 풀어서 설명하세요
</지침>

<출력 형식>
## 정의
[개념의 정확한 정의]

## 핵심 포인트
1. [포인트 1]
2. [포인트 2]
3. [포인트 3]

## 예시
[이해를 돕는 구체적 예시]

## 관련 개념
- [연관 개념 1]
- [연관 개념 2]
</출력 형식>

<학습 자료>
{context}
</학습 자료>

위 자료를 바탕으로 개념을 설명해주세요.""",

    TaskType.COMPARE: """당신은 비교 분석 전문가 '오렌지'입니다.

<지침>
1. 비교 대상을 명확히 구분하세요
2. 공통점과 차이점을 체계적으로 분석하세요
3. 표 형식으로 시각화하세요
4. 각각의 장단점을 객관적으로 제시하세요
</지침>

<출력 형식>
## 비교 대상
- A: [대상 A 설명]
- B: [대상 B 설명]

## 비교표
| 항목 | A | B |
|------|---|---|
| [항목1] | [내용] | [내용] |
| [항목2] | [내용] | [내용] |

## 공통점
- [공통점 1]
- [공통점 2]

## 차이점
- [차이점 1]
- [차이점 2]

## 결론
[비교 분석 결론]
</출력 형식>

<학습 자료>
{context}
</학습 자료>

위 자료를 바탕으로 비교 분석해주세요.""",

    TaskType.APPLY: """당신은 응용/실습 전문가 '오렌지'입니다.

<지침>
1. 실제 활용 방법을 구체적으로 제시하세요
2. 단계별 가이드를 제공하세요
3. 코드가 필요하면 예시 코드를 포함하세요
4. 주의사항이나 팁을 추가하세요
</지침>

<출력 형식>
## 활용 방법
[실제 활용 방법 설명]

## 단계별 가이드
1. **단계 1**: [내용]
2. **단계 2**: [내용]
3. **단계 3**: [내용]

## 예시 코드 (해당시)
```
[코드 예시]
```

## 팁과 주의사항
- [팁 1]
- [주의사항 1]
</출력 형식>

<학습 자료>
{context}
</학습 자료>

위 자료를 바탕으로 실제 활용 방법을 설명해주세요."""
}


class IntegratedPipeline:
    """문서 요약 + Q&A 통합 파이프라인"""

    def __init__(
        self,
        rag_system: Optional[RAGSystem] = None,
        model: str = MODEL,
        base_url: str = BASE_URL,
        api_key: str = API_KEY
    ):
        self.rag = rag_system or get_rag_system()
        self.model = model
        self.base_url = base_url
        self.api_key = api_key
        self._test_results: List[TestResult] = []

    def _get_llm(self, temperature: float = 0.4, max_tokens: int = 1024) -> ChatOpenAI:
        """LLM 인스턴스 생성"""
        return ChatOpenAI(
            model=self.model,
            base_url=self.base_url,
            api_key=self.api_key,
            temperature=temperature,
            max_tokens=max_tokens
        )

    def _detect_task_type(self, query: str) -> TaskType:
        """질문에서 작업 유형 자동 감지"""
        query_lower = query.lower()

        # 요약 관련 키워드
        if any(kw in query_lower for kw in ["요약", "정리", "핵심", "간단히", "줄여"]):
            return TaskType.SUMMARIZE

        # 개념 설명 키워드
        if any(kw in query_lower for kw in ["뭐야", "무엇", "정의", "설명해", "이란", "이란?"]):
            return TaskType.CONCEPT

        # 비교 키워드
        if any(kw in query_lower for kw in ["비교", "차이", "vs", "다른점", "공통점", "장단점"]):
            return TaskType.COMPARE

        # 응용 키워드
        if any(kw in query_lower for kw in ["어떻게", "방법", "활용", "적용", "예시", "코드"]):
            return TaskType.APPLY

        # 기본값: Q&A
        return TaskType.QA

    def _retrieve_context(self, query: str, k: int = 3) -> tuple[str, List[Dict[str, str]]]:
        """문서 검색 및 컨텍스트 추출"""
        docs = self.rag.search(query, k=k)

        if not docs:
            return "", []

        context_parts = []
        sources = []

        for i, doc in enumerate(docs, 1):
            source = doc.metadata.get("source", "unknown")
            doc_type = doc.metadata.get("type", "text")
            content = doc.page_content

            context_parts.append(f"[문서 {i}] (출처: {source})\n{content}")
            sources.append({
                "index": i,
                "source": source,
                "type": doc_type,
                "preview": content[:200] + "..." if len(content) > 200 else content
            })

        return "\n\n".join(context_parts), sources

    def _build_messages(
        self,
        query: str,
        context: str,
        task_type: TaskType,
        chat_history: List[Dict[str, str]]
    ) -> List:
        """메시지 구성"""
        system_prompt = TASK_PROMPTS.get(task_type, TASK_PROMPTS[TaskType.QA])
        formatted_prompt = system_prompt.format(
            context=context if context else "등록된 학습 자료가 없습니다."
        )

        messages = [SystemMessage(content=formatted_prompt)]

        # 대화 히스토리 추가
        for msg in chat_history[-10:]:  # 최근 10개만
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            else:
                messages.append(AIMessage(content=msg["content"]))

        messages.append(HumanMessage(content=query))
        return messages

    def process(self, input_data: PipelineInput) -> PipelineOutput:
        """통합 파이프라인 실행

        Args:
            input_data: 파이프라인 입력 데이터

        Returns:
            PipelineOutput: 처리 결과
        """
        start_time = time.time()

        # 작업 유형 감지 (자동 또는 지정)
        task_type = input_data.task_type
        if task_type == TaskType.QA:
            # 자동 감지 시도
            detected = self._detect_task_type(input_data.query)
            if detected != TaskType.QA:
                task_type = detected

        # 컨텍스트 검색
        context, sources = self._retrieve_context(input_data.query, k=input_data.context_k)
        retrieval_time = time.time() - start_time

        # 메시지 구성
        messages = self._build_messages(
            input_data.query,
            context,
            task_type,
            input_data.chat_history
        )

        # LLM 호출
        llm = self._get_llm(
            temperature=input_data.temperature,
            max_tokens=input_data.max_tokens
        )

        llm_start = time.time()
        response = llm.invoke(messages)
        llm_time = time.time() - llm_start

        total_time = time.time() - start_time

        # 메트릭 수집
        metrics = {
            "total_time_ms": round(total_time * 1000, 2),
            "retrieval_time_ms": round(retrieval_time * 1000, 2),
            "llm_time_ms": round(llm_time * 1000, 2),
            "context_chunks": len(sources),
            "detected_task_type": task_type.value,
            "input_tokens": len(input_data.query.split()),
            "output_tokens": len(response.content.split()) if response.content else 0
        }

        return PipelineOutput(
            response=response.content,
            sources=sources,
            task_type=task_type,
            metrics=metrics,
            raw_context=context
        )

    def process_stream(
        self,
        input_data: PipelineInput,
        callback: Callable[[str], None]
    ) -> PipelineOutput:
        """스트리밍 파이프라인 실행

        Args:
            input_data: 파이프라인 입력 데이터
            callback: 청크 콜백 함수

        Returns:
            PipelineOutput: 처리 결과
        """
        start_time = time.time()

        # 작업 유형 감지
        task_type = input_data.task_type
        if task_type == TaskType.QA:
            detected = self._detect_task_type(input_data.query)
            if detected != TaskType.QA:
                task_type = detected

        # 컨텍스트 검색
        context, sources = self._retrieve_context(input_data.query, k=input_data.context_k)
        retrieval_time = time.time() - start_time

        # 메시지 구성
        messages = self._build_messages(
            input_data.query,
            context,
            task_type,
            input_data.chat_history
        )

        # LLM 스트리밍 호출
        llm = self._get_llm(
            temperature=input_data.temperature,
            max_tokens=input_data.max_tokens
        )

        llm_start = time.time()
        full_response = ""

        for chunk in llm.stream(messages):
            if chunk.content:
                full_response += chunk.content
                callback(chunk.content)

        llm_time = time.time() - llm_start
        total_time = time.time() - start_time

        metrics = {
            "total_time_ms": round(total_time * 1000, 2),
            "retrieval_time_ms": round(retrieval_time * 1000, 2),
            "llm_time_ms": round(llm_time * 1000, 2),
            "context_chunks": len(sources),
            "detected_task_type": task_type.value,
            "streaming": True
        }

        return PipelineOutput(
            response=full_response,
            sources=sources,
            task_type=task_type,
            metrics=metrics,
            raw_context=context
        )

    def summarize_document(self, text: str, source: str = "직접입력") -> PipelineOutput:
        """문서 요약 전용 메서드

        Args:
            text: 요약할 텍스트
            source: 문서 출처

        Returns:
            PipelineOutput: 요약 결과
        """
        # 임시로 문서 추가
        temp_ids = self.rag.add_document(text, metadata={"source": source, "type": "temp"})

        try:
            input_data = PipelineInput(
                query=f"다음 내용을 요약해주세요: {text[:500]}...",
                task_type=TaskType.SUMMARIZE,
                context_k=5,
                temperature=0.3
            )
            result = self.process(input_data)
            return result
        finally:
            # 임시 문서는 유지 (사용자가 원하면 삭제)
            pass

    def run_test(
        self,
        test_queries: List[Dict[str, Any]],
        verbose: bool = True
    ) -> List[TestResult]:
        """성능 테스트 실행

        Args:
            test_queries: 테스트 쿼리 목록
                [{"query": "...", "task_type": TaskType.QA, "expected_keywords": [...]}]
            verbose: 상세 출력 여부

        Returns:
            List[TestResult]: 테스트 결과 목록
        """
        results = []

        for i, test_case in enumerate(test_queries, 1):
            query = test_case.get("query", "")
            task_type = test_case.get("task_type", TaskType.QA)
            expected_keywords = test_case.get("expected_keywords", [])

            if verbose:
                print(f"\n[테스트 {i}/{len(test_queries)}] {query[:50]}...")

            start_time = time.time()

            try:
                input_data = PipelineInput(
                    query=query,
                    task_type=task_type
                )
                output = self.process(input_data)

                response_time = (time.time() - start_time) * 1000

                # 응답 품질 평가
                response_lower = output.response.lower()
                keyword_hits = sum(1 for kw in expected_keywords if kw.lower() in response_lower)
                keyword_score = keyword_hits / len(expected_keywords) if expected_keywords else 1.0

                # 컨텍스트 관련성 (검색된 문서 수 기반 간단 평가)
                context_relevance = min(1.0, len(output.sources) / 3)

                quality = {
                    "keyword_coverage": round(keyword_score, 2),
                    "response_length": len(output.response),
                    "has_structure": any(marker in output.response for marker in ["##", "**", "- ", "1."]),
                    "sources_count": len(output.sources)
                }

                result = TestResult(
                    query=query,
                    task_type=task_type,
                    response_time_ms=response_time,
                    token_count=output.metrics.get("output_tokens", 0),
                    context_relevance=context_relevance,
                    response_quality=quality,
                    success=True
                )

                if verbose:
                    print(f"  ✓ 응답 시간: {response_time:.0f}ms")
                    print(f"  ✓ 키워드 커버리지: {keyword_score:.0%}")

            except Exception as e:
                result = TestResult(
                    query=query,
                    task_type=task_type,
                    response_time_ms=0,
                    token_count=0,
                    context_relevance=0,
                    response_quality={},
                    success=False,
                    error=str(e)
                )

                if verbose:
                    print(f"  ✗ 오류: {e}")

            results.append(result)
            self._test_results.append(result)

        return results

    def get_test_summary(self) -> Dict[str, Any]:
        """테스트 결과 요약

        Returns:
            Dict: 테스트 요약 통계
        """
        if not self._test_results:
            return {"message": "테스트 결과가 없습니다."}

        successful = [r for r in self._test_results if r.success]
        failed = [r for r in self._test_results if not r.success]

        avg_time = sum(r.response_time_ms for r in successful) / len(successful) if successful else 0
        avg_relevance = sum(r.context_relevance for r in successful) / len(successful) if successful else 0

        return {
            "total_tests": len(self._test_results),
            "successful": len(successful),
            "failed": len(failed),
            "success_rate": round(len(successful) / len(self._test_results) * 100, 1),
            "avg_response_time_ms": round(avg_time, 2),
            "avg_context_relevance": round(avg_relevance, 3),
            "by_task_type": self._group_by_task_type()
        }

    def _group_by_task_type(self) -> Dict[str, Dict]:
        """작업 유형별 테스트 결과 그룹화"""
        groups = {}
        for result in self._test_results:
            task_name = result.task_type.value
            if task_name not in groups:
                groups[task_name] = {"count": 0, "success": 0, "avg_time": 0, "times": []}

            groups[task_name]["count"] += 1
            if result.success:
                groups[task_name]["success"] += 1
                groups[task_name]["times"].append(result.response_time_ms)

        # 평균 계산
        for task_name, data in groups.items():
            if data["times"]:
                data["avg_time"] = round(sum(data["times"]) / len(data["times"]), 2)
            del data["times"]

        return groups

    def clear_test_results(self):
        """테스트 결과 초기화"""
        self._test_results = []


# 기본 테스트 케이스
DEFAULT_TEST_CASES = [
    {
        "query": "RAG가 뭐야?",
        "task_type": TaskType.CONCEPT,
        "expected_keywords": ["retrieval", "검색", "생성", "augmented"]
    },
    {
        "query": "이 내용을 요약해줘",
        "task_type": TaskType.SUMMARIZE,
        "expected_keywords": ["핵심", "요약", "정리"]
    },
    {
        "query": "Python과 JavaScript의 차이점은?",
        "task_type": TaskType.COMPARE,
        "expected_keywords": ["python", "javascript", "차이", "비교"]
    },
    {
        "query": "이걸 어떻게 활용할 수 있어?",
        "task_type": TaskType.APPLY,
        "expected_keywords": ["활용", "방법", "예시"]
    },
    {
        "query": "LangChain의 주요 기능은 뭐야?",
        "task_type": TaskType.QA,
        "expected_keywords": ["langchain", "기능"]
    }
]


# 싱글톤 인스턴스
_pipeline_instance: Optional[IntegratedPipeline] = None


def get_pipeline() -> IntegratedPipeline:
    """파이프라인 싱글톤 인스턴스 반환"""
    global _pipeline_instance
    if _pipeline_instance is None:
        _pipeline_instance = IntegratedPipeline()
    return _pipeline_instance


if __name__ == "__main__":
    # 테스트 실행
    print("=" * 60)
    print("통합 파이프라인 테스트")
    print("=" * 60)

    pipeline = get_pipeline()

    # 샘플 문서 추가
    sample_texts = [
        "RAG(Retrieval-Augmented Generation)는 검색 증강 생성 기술로, 외부 지식을 활용하여 LLM의 답변 정확도를 높입니다.",
        "Python은 간결하고 읽기 쉬운 문법을 가진 범용 프로그래밍 언어입니다.",
        "LangChain은 LLM 애플리케이션 개발을 위한 프레임워크로, 체인, 에이전트, 메모리 등의 기능을 제공합니다."
    ]

    rag = get_rag_system()
    for text in sample_texts:
        rag.add_document(text, metadata={"source": "test_data"})

    print(f"\n테스트 문서 {len(sample_texts)}개 추가 완료")

    # 테스트 실행
    results = pipeline.run_test(DEFAULT_TEST_CASES, verbose=True)

    # 결과 요약
    print("\n" + "=" * 60)
    print("테스트 결과 요약")
    print("=" * 60)

    summary = pipeline.get_test_summary()
    print(f"전체 테스트: {summary['total_tests']}개")
    print(f"성공: {summary['successful']}개")
    print(f"실패: {summary['failed']}개")
    print(f"성공률: {summary['success_rate']}%")
    print(f"평균 응답 시간: {summary['avg_response_time_ms']}ms")
    print(f"평균 컨텍스트 관련성: {summary['avg_context_relevance']}")

    print("\n작업 유형별 결과:")
    for task_type, data in summary['by_task_type'].items():
        print(f"  {task_type}: {data['success']}/{data['count']} 성공, 평균 {data['avg_time']}ms")
