"""
카드뉴스 제작 전용 에이전트
"""
from typing import List, Optional
from google.adk.agents.llm_agent import Agent
from google.adk.models.lite_llm import LiteLlm
from google.adk.tools.tool_context import ToolContext
from .prompt import CARD_NEWS_AGENT_INSTRUCTION, CARD_NEWS_AGENT_DESCRIPTION

MODEL = LiteLlm(model="openai/gpt-4o-mini")


def process_reference_file(file_path: str) -> dict:
    """참고자료 파일을 처리합니다."""
    from ...agent import process_reference_file as _process_file
    return _process_file(file_path)


def plan_content_structure(topic: str, content_format: str, reference_info: Optional[str] = None) -> dict:
    """콘텐츠 구조를 기획합니다."""
    from ...agent import plan_content_structure as _plan
    return _plan(topic, content_format, reference_info)


async def create_card_news(tool_context: ToolContext, topic: str, reference_files: Optional[List[str]] = None) -> dict:
    """
    카드뉴스 형식의 텍스트 콘텐츠를 생성하고 state에 저장합니다.
    이미지 생성은 image_builder_agent가 담당합니다.
    
    Args:
        tool_context: 도구 컨텍스트 (state 접근용)
        topic: 콘텐츠 주제
        reference_files: 참고자료 파일 경로 리스트 (선택사항)
        
    Returns:
        생성된 카드뉴스 콘텐츠 (텍스트만, 이미지는 image_builder_agent가 생성)
    """
    from ...agent import create_content_base
    
    # 텍스트 콘텐츠 생성
    result = create_content_base(topic, "카드뉴스", reference_files)
    
    # state에 결과 저장 (image_builder_agent가 사용할 수 있도록)
    tool_context.state["content_creator_output"] = result
    
    # 반환값에 다음 단계 힌트 추가
    result["next_step"] = "이제 image_builder_agent를 호출하여 각 카드마다 이미지를 생성하세요"
    result["requires_image_generation"] = True
    result["message"] = "텍스트 콘텐츠 생성 완료. 다음 단계: image_builder_agent 호출 필수"
    
    return result


# 카드뉴스 전용 에이전트
from google.adk.tools.agent_tool import AgentTool
from ...subagents.image_builder.agent import image_builder_agent

image_builder_tool = AgentTool(agent=image_builder_agent)

card_news_agent = Agent(
    model=MODEL,
    name='card_news_agent',
    description=CARD_NEWS_AGENT_DESCRIPTION,
    instruction=CARD_NEWS_AGENT_INSTRUCTION,
    output_key="card_news_output",
    tools=[
        process_reference_file,
        plan_content_structure,
        create_card_news,
        image_builder_tool,
    ],
)

