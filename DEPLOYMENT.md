# 배포 가이드

이 문서는 콘텐츠 제작 에이전트를 Streamlit Cloud와 Cloud Run에 배포하는 방법을 설명합니다.

## 아키텍처

```
┌─────────────────┐         HTTP API         ┌──────────────┐
│ Streamlit Cloud │ ────────────────────────> │ Cloud Run    │
│  (GitHub Repo)  │                           │ (ADK Server) │
└─────────────────┘                           └──────────────┘
```

- **Streamlit Cloud**: GitHub 퍼블릭 레포지토리를 참조하여 웹 인터페이스 제공
- **Cloud Run**: ADK API Server를 실행하여 에이전트 처리

## 1. Cloud Run에 ADK 서버 배포

### 1.1 ADK 서버 준비

ADK 서버는 `content_creator` 패키지의 `root_agent`를 사용합니다.

### 1.2 Cloud Run 배포

```bash
# ADK 서버를 Cloud Run에 배포
# (ADK 공식 문서 참조: https://google.github.io/adk-docs/run-agents/deployment/agent-engine/)
```

**주요 설정:**
- 서비스 이름: `content-creator-adk`
- 리전: `asia-northeast3` (서울) 또는 원하는 리전
- 포트: `8080` (Cloud Run 기본)
- 환경 변수:
  - `GOOGLE_API_KEY` 또는 `OPENAI_API_KEY`

### 1.3 배포 후 URL 확인

배포 완료 후 Cloud Run 서비스 URL을 확인합니다:
```
https://content-creator-adk-xxx.run.app
```

## 2. Streamlit Cloud 배포

### 2.1 GitHub 레포지토리 준비

1. 프로젝트를 GitHub 퍼블릭 레포지토리로 푸시
2. `.env` 파일은 `.gitignore`에 포함되어 있어 커밋되지 않음 (안전)

### 2.2 Streamlit Cloud 설정

1. [Streamlit Cloud](https://streamlit.io/cloud)에 로그인
2. "New app" 클릭
3. GitHub 레포지토리 선택
4. 설정:
   - **Main file path**: `app.py`
   - **Python version**: `3.10` 이상

### 2.3 Secrets 설정

Streamlit Cloud 대시보드에서 "Secrets" 탭으로 이동하여 다음 설정:

```toml
ADK_SERVER_URL = "https://content-creator-adk-xxx.run.app"
USE_ADK_SERVER = "true"
```

또는 `.streamlit/secrets.toml.example` 파일을 참조하세요.

### 2.4 배포

"Deploy" 버튼을 클릭하여 배포를 시작합니다.

## 3. 로컬 개발 설정

로컬에서 개발할 때는 직접 함수 호출 모드를 사용합니다:

```bash
# .env 파일 (로컬 개발용)
USE_ADK_SERVER=false
```

또는 환경 변수 없이 실행하면 자동으로 로컬 모드로 동작합니다.

## 4. 환경 변수 요약

### Streamlit Cloud (Secrets)
```toml
ADK_SERVER_URL = "https://your-cloud-run-url.run.app"
USE_ADK_SERVER = "true"
```

### Cloud Run (환경 변수)
```bash
GOOGLE_API_KEY=your_key
# 또는
OPENAI_API_KEY=your_key
```

### 로컬 개발 (.env)
```bash
USE_ADK_SERVER=false
GOOGLE_API_KEY=your_key
# 또는
OPENAI_API_KEY=your_key
```

## 5. 트러블슈팅

### 문제: Streamlit에서 "ADK_SERVER_URL이 설정되지 않았습니다" 오류

**해결**: Streamlit Cloud Secrets에 `ADK_SERVER_URL`이 올바르게 설정되었는지 확인하세요.

### 문제: Cloud Run 서버 연결 실패

**해결**: 
1. Cloud Run 서비스가 실행 중인지 확인
2. URL이 올바른지 확인 (HTTPS 사용)
3. Cloud Run의 인증 설정 확인 (인증 필요 시)

### 문제: 타임아웃 오류

**해결**: 
- `adk_client.py`의 `timeout` 값을 증가시키세요 (현재 120초)
- Cloud Run의 타임아웃 설정도 확인하세요

## 6. 모니터링

- **Streamlit Cloud**: Streamlit Cloud 대시보드에서 로그 확인
- **Cloud Run**: Google Cloud Console에서 로그 및 메트릭 확인

## 참고 자료

- [ADK 배포 가이드](https://google.github.io/adk-docs/run-agents/deployment/)
- [Streamlit Cloud 문서](https://docs.streamlit.io/streamlit-community-cloud)
- [Cloud Run 문서](https://cloud.google.com/run/docs)

