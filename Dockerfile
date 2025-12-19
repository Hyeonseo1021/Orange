# 1. 베이스 이미지 선택 (경량화된 Python 3.11 이미지 사용)
FROM python:3.11-slim

# 2. 작업 디렉토리 설정
WORKDIR /app

# 3. requirements.txt 파일을 먼저 복사하여 Docker 캐시를 활용
COPY requirements.txt .

# 4. pip를 최신 버전으로 업그레이드하고, requirements.txt에 명시된 의존성 설치
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 5. 나머지 애플리케이션 소스 코드 복사
# (main.py, templates/ 디렉토리, static/ 디렉토리 등)
COPY . .

# 6. 컨테이너가 8000번 포트를 외부에 노출하도록 설정
EXPOSE 8000

# 7. 컨테이너가 시작될 때 실행할 명령어
# uvicorn 서버를 실행합니다. main.py 파일의 app 객체를 실행한다는 의미입니다.
# --host 0.0.0.0 옵션은 외부에서 컨테이너에 접근할 수 있도록 합니다.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
