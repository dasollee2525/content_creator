"""
ADK API Server 클라이언트
Cloud Run에 배포된 ADK 서버와 통신
"""
import os
import requests
from typing import Optional, Dict, Any
import streamlit as st

# 환경 변수에서 ADK 서버 URL 가져오기
ADK_SERVER_URL = os.getenv(
    "ADK_SERVER_URL", 
    ""  # Streamlit secrets에서 설정
)


def ensure_session(user_id: str = "u_demo", session_id: str = "s_demo") -> tuple:
    """
    세션을 생성하거나 확인합니다.
    
    Args:
        user_id: 사용자 ID
        session_id: 세션 ID
        
    Returns:
        (status_code, response_text) 튜플
    """
    if not ADK_SERVER_URL:
        raise ValueError("ADK_SERVER_URL이 설정되지 않았습니다. Streamlit secrets를 확인하세요.")
    
    try:
        r = requests.post(
            f"{ADK_SERVER_URL}/apps/content_creator_agent/users/{user_id}/sessions/{session_id}",
            json={"state": {}},
            timeout=30
        )
        # 409는 이미 존재하는 세션이므로 OK로 처리
        if r.status_code in [200, 201, 409]:
            return r.status_code, "OK"
        return r.status_code, r.text
    except requests.exceptions.RequestException as e:
        return 500, str(e)


def call_adk_agent(
    message: str,
    user_id: str = "u_demo",
    session_id: Optional[str] = None,
    app_name: str = "content_creator_agent"
) -> Dict[str, Any]:
    """
    ADK API Server에 요청을 보냅니다.
    
    Args:
        message: 사용자 메시지
        user_id: 사용자 ID
        session_id: 세션 ID (없으면 Streamlit 세션 ID 사용)
        app_name: 앱 이름
        
    Returns:
        에이전트 응답
    """
    if not ADK_SERVER_URL:
        raise ValueError("ADK_SERVER_URL이 설정되지 않았습니다. Streamlit secrets를 확인하세요.")
    
    if session_id is None:
        # Streamlit 세션 ID 사용
        if "adk_session_id" not in st.session_state:
            import uuid
            st.session_state["adk_session_id"] = f"s_{uuid.uuid4().hex[:8]}"
        session_id = st.session_state["adk_session_id"]
    
    # 세션 확인/생성
    ensure_session(user_id, session_id)
    
    # 요청 페이로드 (camelCase 버전)
    payload = {
        "appName": app_name,
        "userId": user_id,
        "sessionId": session_id,
        "newMessage": {
            "role": "user",
            "parts": [{"text": message}]
        }
    }
    
    try:
        r = requests.post(
            f"{ADK_SERVER_URL}/run",
            json=payload,
            timeout=120  # 에이전트 응답 대기 시간
        )
        r.raise_for_status()
        return r.json()
    except requests.exceptions.RequestException as e:
        raise Exception(f"ADK 서버 통신 오류: {str(e)}")


def create_content_via_adk(
    topic: str,
    content_format: str,
    reference_files: Optional[list] = None
) -> Dict[str, Any]:
    """
    ADK 에이전트를 통해 콘텐츠를 생성합니다.
    
    Args:
        topic: 콘텐츠 주제
        content_format: 콘텐츠 형식 (카드뉴스/뉴스레터/인포그래픽)
        reference_files: 참고자료 파일 경로 리스트 (선택사항)
        
    Returns:
        생성된 콘텐츠
    """
    # 메시지 구성
    message_parts = [
        f"콘텐츠 주제: {topic}",
        f"콘텐츠 형식: {content_format}",
        "",
        "위 주제와 형식에 맞는 콘텐츠를 생성해주세요."
    ]
    
    if reference_files:
        file_info = "\n".join([f"- {f}" for f in reference_files])
        message_parts.insert(2, f"참고자료 파일:\n{file_info}")
    
    message = "\n".join(message_parts)
    
    # ADK 에이전트 호출
    try:
        response = call_adk_agent(message)
        
        # 응답 파싱 (ADK 응답 형식에 맞게 조정 필요)
        # ADK 응답 구조에 따라 파싱 로직 추가 필요
        return {
            "topic": topic,
            "format": content_format,
            "raw_content": response,
            "formatted_content": str(response),  # 임시: 실제 응답 구조에 맞게 수정 필요
            "status": "success"
        }
    except Exception as e:
        return {
            "topic": topic,
            "format": content_format,
            "error": str(e),
            "status": "error"
        }

