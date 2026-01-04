# 콘텐츠 제작 에이전트

Google ADK를 활용한 멀티 에이전트 콘텐츠 제작 시스템입니다.

## 기능

- **콘텐츠 주제 기반 자동 기획**: 사용자가 입력한 주제를 바탕으로 콘텐츠 구조를 기획
- **다양한 파일 형식 지원**: PDF, PNG, XLSX, CSV 등 참고자료 자동 해석
- **다양한 콘텐츠 형식**: 카드뉴스, 뉴스레터, 인포그래픽 형식 지원
- **Streamlit 기반 웹 인터페이스**: 직관적인 UI로 콘텐츠 제작

## 프로젝트 구조

Google ADK의 표준 구조를 따릅니다:

```
content_creator/
├── content_creator/   # 메인 패키지
│   ├── __init__.py
│   ├── agent.py        # 메인 에이전트 정의 (ADK Agent 클래스 사용)
│   └── prompt.py       # 프롬프트 정의
├── app.py              # Streamlit 데모 앱
├── pyproject.toml      # 프로젝트 설정 및 의존성
├── .env                # 환경 변수 (API 키 등)
└── README.md
```

### ADK 에이전트 실행

ADK CLI를 사용하여 에이전트를 직접 실행할 수 있습니다:

```bash
# CLI로 실행
adk run content_creator

# 웹 인터페이스로 실행
adk web --port 8000
```

## 설치

1. 저장소 클론
```bash
git clone <repository-url>
cd content_creator
```

2. 의존성 설치 (uv 사용)
```bash
# uv로 의존성 설치 (가상환경 자동 생성)
uv sync

# 또는 개발 의존성 포함
uv sync --extra dev
```

**참고**: `uv`가 없으면 `pip install uv`로 설치하거나, 기존 방식 사용:
```bash
python -m venv venv
source venv/bin/activate
pip install -e .
```

4. 환경 변수 설정
```bash
# .env.example 파일을 복사하여 .env 파일 생성
cp .env.example .env

# .env 파일을 편집하여 실제 API 키 입력
# OPENAI_API_KEY=your_actual_api_key_here
```

또는 직접 생성:
```bash
# .env 파일 생성 및 API 키 설정
echo 'OPENAI_API_KEY="YOUR_API_KEY"' > .env

# 조직 인증이 필요한 경우 (선택사항)
echo 'OPENAI_ORG_ID="YOUR_ORG_ID"' >> .env
```

API 키 발급:
- OpenAI: https://platform.openai.com/api-keys
- Google AI Studio: https://aistudio.google.com/apikey (현재는 OpenAI만 사용)

## 사용 방법

### 방법 1: ADK CLI 사용 (권장)

ADK의 표준 CLI를 사용하여 에이전트를 실행할 수 있습니다:

```bash
# CLI 인터페이스로 실행
adk run content_creator

# 웹 인터페이스로 실행 (개발용, localhost:8000)
adk web --port 8000
```

**참고**: `adk web` 명령은 `content_creator` 폴더의 **상위 디렉토리**에서 실행해야 합니다.

### 방법 2: Streamlit 앱 실행

#### 로컬 개발
```bash
# 로컬 모드 (직접 함수 호출)
streamlit run app.py
```

#### Streamlit Cloud 배포
1. GitHub에 퍼블릭 레포지토리로 푸시
2. [Streamlit Cloud](https://streamlit.io/cloud)에서 레포지토리 연결
3. Secrets 설정:
   ```
   ADK_SERVER_URL = https://your-cloud-run-url.run.app
   USE_ADK_SERVER = true
   ```
4. 배포 완료!

**참고**: Streamlit Cloud는 GitHub 퍼블릭 레포지토리만 지원합니다.

### 사용 흐름
1. 콘텐츠 주제 입력
2. (선택) 참고자료 파일 업로드
3. 콘텐츠 형식 선택 (카드뉴스/뉴스레터/인포그래픽)
4. 생성 버튼 클릭
5. 결과 확인 및 다운로드

## 에이전트 구성

`agent.py` 파일에 정의된 `root_agent`가 모든 기능을 담당합니다:

- **process_reference_file**: 참고자료 파일 처리 도구
- **plan_content_structure**: 콘텐츠 구조 기획 도구
- **format_content_output**: 콘텐츠 포맷팅 도구
- **create_content**: 전체 프로세스 실행 도구

에이전트는 사용자의 요청을 분석하고 적절한 도구를 자동으로 선택하여 사용합니다.

## 라이선스

MIT License

