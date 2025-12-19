
# 실시간 스트리밍 AI 챗봇 (Flask + WebSocket)

이 프로젝트는 로컬 AI 모델의 응답을 웹 UI에서 실시간 스트리밍으로 보여주는 챗봇 애플리케이션입니다. Flask-SocketIO를 사용하여 백엔드와 프론트엔드 간의 실시간 통신을 구현했습니다.

## ✨ 주요 기능

  - **실시간 응답 스트리밍**: AI가 생성하는 텍스트를 타이핑하듯이 한 글자씩 실시간으로 표시합니다.
  - **WebSocket 통신**: Flask-SocketIO를 사용하여 서버와 클라이언트 간의 효율적인 양방향 통신을 구현합니다.
  - **비동기 백엔드 처리**: AI 모델의 응답을 기다리는 동안 서버가 블로킹되지 않도록 백그라운드 작업을 사용합니다.
  - **세련된 UI**: 다크 모드 기반의 깔끔하고 반응형인 채팅 인터페이스를 제공합니다.

-----

## 📂 프로젝트 구조

```
/chatbot-app
├── app.py              # Flask 백엔드 서버
├── requirements.txt    # 필요한 Python 라이브러리 목록
├── functions/          # LLM이 호출하는 함수
├── templates/
│   └── index.html      # 프론트엔드 HTML
└── static/
    └── style.css       # 프론트엔드 CSS
```

-----

## 🚀 설치 및 실행 방법

### 1\. 사전 준비

  - **Python 3.8 이상**이 설치되어 있어야 합니다.
  - LM Studio, Ollama 등과 같은 **로컬 AI 서버**가 실행 중이어야 합니다. (`http://localhost:1234`)

### 2\. 프로젝트 클론 및 설정

프로젝트를 다운로드하고 해당 디렉토리로 이동합니다.

git을 사용하는 경우 아래와 같이 프로젝트를 다운로드 할 수 있습니다.

```bash
git clone https://gitlab.ngrid.kr/root/class_software.git
cd chatbot-app
```

git을 사용하지 않는 경우 프로젝트를 zip으로 다운받아서 사용하세요.


### 3\. 가상 환경 생성 및 활성화

프로젝트 의존성을 시스템 전체가 아닌 독립된 공간에 설치하기 위해 가상 환경을 생성하고 활성화합니다.

  - **macOS / Linux**:

    ```bash
    # 'venv'라는 이름의 가상 환경 생성
    python3 -m venv venv

    # 가상 환경 활성화
    source venv/bin/activate
    ```

  - **Windows**:

    ```bash
    # 'venv'라는 이름의 가상 환경 생성
    python -m venv venv

    # 가상 환경 활성화
    .\venv\Scripts\activate
    ```

    > 💡 가상 환경이 활성화되면 터미널 프롬프트 앞에 `(venv)`가 표시됩니다.
    > 가상환경 생성에 오류가 발생하는 경우 powershell 을 관리자 권한으로 실행해 다음의 명령어를 입력하세요. 
    
    ```
    Set-ExecutionPolicy RemoteSigned
    ```
    
    위에 코드를 입력해 주고 y를 입력해 주면 오류가 해결됩니다. 


### 4\. 의존성 라이브러리 설치

`requirements.txt` 파일을 사용하여 프로젝트에 필요한 모든 라이브러리를 설치합니다.

```bash
pip install -r requirements.txt
```

### 5\. 애플리케이션 실행

1.  **로컬 AI 서버를 먼저 실행**하세요.

2.  아래 명령어를 터미널에 입력하여 Flask 웹 서버를 시작합니다.

    ```bash
    python main.py
    ```

3.  웹 브라우저를 열고 주소창에 `http://127.0.0.1:8000`을 입력하여 챗봇을 실행합니다.


### 6\. Docker build
```
docker build -t my-fastapi-app .
docker run -d -p 8000:8000 my-fastapi-app
```
-----


## ⚙️ 배포시 주의사항

.env 파일의 "http://127.0.0.1:1234/v1" 부분이
http://host.docker.internal:1234/v1 이 되어야 합니다.




## ⚙️ 동작 원리

1.  **사용자 입력 (Frontend)**: 사용자가 웹 UI에서 메시지를 입력하고 전송합니다.
2.  **WebSocket 메시지 전송**: JavaScript가 입력된 메시지를 WebSocket을 통해 Flask 백엔드로 전송합니다. (`send_message` 이벤트)
3.  **백그라운드 작업 시작 (Backend)**: Flask 서버는 `send_message` 이벤트를 수신하고, AI 서버에 응답을 요청하는 작업을 백그라운드 태스크로 시작합니다.
4.  **AI 서버 스트리밍 요청**: 백엔드는 로컬 AI 서버(`localhost:1234`)에 HTTP POST 요청을 보내고, 응답을 스트림 형태로 수신합니다.
5.  **실시간 응답 전송**: 백엔드는 스트림에서 응답 조각(토큰)을 받을 때마다 WebSocket을 통해 프론트엔드로 즉시 전송합니다. (`stream_response` 이벤트)
6.  **UI 업데이트 (Frontend)**: JavaScript는 `stream_response` 이벤트를 수신할 때마다 채팅창에 텍스트를 추가하여 실시간 스트리밍 효과를 구현합니다.

-----

## 📄 라이선스

이 프로젝트는 MIT 라이선스를 따릅니다. 자세한 내용은 `LICENSE` 파일을 참고하세요.