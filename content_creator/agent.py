"""
콘텐츠 제작 에이전트
Google ADK를 사용한 멀티 에이전트 콘텐츠 제작 시스템
"""
import os
import json
import tempfile
import requests
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv
from google.adk.agents.llm_agent import Agent
from pydantic import BaseModel
import pdfplumber
import pandas as pd
from PIL import Image

from .prompt import get_agent_instruction

# 환경 변수 로드 (.env 파일에서)
load_dotenv()

# API 키 확인 (OpenAI 전용)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    OPENAI_CLIENT = None
else:
    try:
        from openai import OpenAI
        # 싱글턴 클라이언트 생성 (모듈 로드 시 1번만)
        OPENAI_CLIENT = OpenAI(api_key=OPENAI_API_KEY)
    except ImportError:
        OPENAI_CLIENT = None


# Pydantic 모델 정의 (JSON 스키마 강제)
class ContentSection(BaseModel):
    title: str
    content: str
    key_points: Optional[List[str]] = []


class GeneratedContent(BaseModel):
    title: str
    introduction: str
    sections: List[ContentSection]
    key_points: List[str]
    conclusion: str
    statistics: Optional[List[Dict[str, str]]] = None
    visual_elements: Optional[List[Dict[str, str]]] = None


# 파일 처리 함수들
def process_pdf(file_path: str) -> Dict[str, Any]:
    """PDF 파일을 처리하여 텍스트를 추출합니다."""
    try:
        text_content = []
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    text_content.append(text)
        return {
            "type": "pdf",
            "content": "\n\n".join(text_content),
            "page_count": len(text_content),
            "status": "success"
        }
    except Exception as e:
        return {"type": "pdf", "content": "", "error": str(e), "status": "error"}


def process_image(file_path: str) -> Dict[str, Any]:
    """이미지 파일을 처리합니다."""
    try:
        with Image.open(file_path) as img:
            return {
                "type": "image",
                "format": img.format,
                "size": img.size,
                "mode": img.mode,
                "status": "success"
            }
    except Exception as e:
        return {"type": "image", "error": str(e), "status": "error"}


def process_excel(file_path: str) -> Dict[str, Any]:
    """Excel 파일을 처리하여 데이터를 추출합니다."""
    try:
        excel_file = pd.ExcelFile(file_path)
        sheets_data = {}
        for sheet_name in excel_file.sheet_names:
            df = pd.read_excel(file_path, sheet_name=sheet_name)
            sheets_data[sheet_name] = {
                "shape": df.shape,
                "columns": df.columns.tolist()
            }
        return {
            "type": "excel",
            "sheets": sheets_data,
            "sheet_names": excel_file.sheet_names,
            "status": "success"
        }
    except Exception as e:
        return {"type": "excel", "error": str(e), "status": "error"}


def process_csv(file_path: str) -> Dict[str, Any]:
    """CSV 파일을 처리하여 데이터를 추출합니다."""
    try:
        df = pd.read_csv(file_path)
        return {
            "type": "csv",
            "shape": df.shape,
            "columns": df.columns.tolist(),
            "status": "success"
        }
    except Exception as e:
        return {"type": "csv", "error": str(e), "status": "error"}


def process_file(file_path: str) -> Dict[str, Any]:
    """파일 확장자를 기반으로 적절한 처리 함수를 호출합니다."""
    if not os.path.exists(file_path):
        return {"error": f"파일을 찾을 수 없습니다: {file_path}", "status": "error"}
    
    file_ext = os.path.splitext(file_path)[1].lower()
    if file_ext == '.pdf':
        return process_pdf(file_path)
    elif file_ext in ['.png', '.jpg', '.jpeg', '.gif', '.bmp']:
        return process_image(file_path)
    elif file_ext in ['.xlsx', '.xls']:
        return process_excel(file_path)
    elif file_ext == '.csv':
        return process_csv(file_path)
    else:
        return {"error": f"지원하지 않는 파일 형식입니다: {file_ext}", "status": "error"}


# 콘텐츠 포맷팅 함수들
def format_card_news(content_data: Dict[str, Any]) -> str:
    """카드뉴스 형식으로 포맷팅합니다."""
    title = content_data.get("title", "제목 없음")
    sections = content_data.get("sections", [])
    key_points = content_data.get("key_points", [])
    
    formatted = f"\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n📌 카드뉴스: {title}\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    
    if key_points:
        formatted += "🔑 핵심 포인트\n\n"
        for i, point in enumerate(key_points[:5], 1):
            formatted += f"{i}. {point}\n"
        formatted += "\n"
    
    for i, section in enumerate(sections, 1):
        section_title = section.get("title", f"섹션 {i}")
        section_content = section.get("content", "")
        formatted += f"\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n카드 {i}: {section_title}\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n{section_content}\n\n"
    
    formatted += "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    return formatted


def format_newsletter(content_data: Dict[str, Any]) -> str:
    """뉴스레터 형식으로 포맷팅합니다."""
    title = content_data.get("title", "뉴스레터 제목")
    introduction = content_data.get("introduction", "")
    sections = content_data.get("sections", [])
    conclusion = content_data.get("conclusion", "")
    
    formatted = f"\n╔════════════════════════════════════════╗\n║          {title:^30}          ║\n╚════════════════════════════════════════╝\n\n"
    
    if introduction:
        formatted += f"📬 인사말\n\n{introduction}\n\n"
    
    for section in sections:
        section_title = section.get("title", "")
        section_content = section.get("content", "")
        formatted += f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n📰 {section_title}\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n{section_content}\n\n"
    
    if conclusion:
        formatted += f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n💭 마무리\n\n{conclusion}\n\n"
    
    formatted += "\n" + "="*50 + "\n이 뉴스레터가 유용하셨나요? 피드백을 남겨주세요!\n"
    return formatted


def format_infographic(content_data: Dict[str, Any]) -> str:
    """인포그래픽 형식으로 포맷팅합니다."""
    title = content_data.get("title", "인포그래픽 제목")
    stats = content_data.get("statistics", [])
    sections = content_data.get("sections", [])
    visual_elements = content_data.get("visual_elements", [])
    
    formatted = f"\n┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓\n┃                                          ┃\n┃        📊 {title:^30}        ┃\n┃                                          ┃\n┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛\n\n"
    
    if stats:
        formatted += "📈 주요 통계\n\n"
        for stat in stats:
            formatted += f"  • {stat.get('label', '')}: {stat.get('value', '')}\n"
        formatted += "\n"
    
    if visual_elements:
        formatted += "🎨 시각적 요소\n\n"
        for element in visual_elements:
            formatted += f"  [{element.get('type', '')}] {element.get('description', '')}\n"
        formatted += "\n"
    
    for i, section in enumerate(sections, 1):
        section_title = section.get("title", f"섹션 {i}")
        section_content = section.get("content", "")
        formatted += f"\n┌──────────────────────────────────────────┐\n│ {i}. {section_title:<35} │\n├──────────────────────────────────────────┤\n│                                          │\n│ {section_content[:200]:<40} │\n│                                          │\n└──────────────────────────────────────────┘\n\n"
    
    formatted += "\n" + "━"*50 + "\n💡 인포그래픽은 시각적 요소와 함께 보시면 더 효과적입니다.\n"
    return formatted


def process_reference_file(file_path: str) -> dict:
    """
    참고자료 파일을 처리하고 핵심 정보를 추출합니다.
    
    Args:
        file_path: 처리할 파일 경로
        
    Returns:
        파일에서 추출한 정보를 담은 딕셔너리
    """
    try:
        result = process_file(file_path)
        
        if result.get("status") == "success":
            file_type = result.get("type", "")
            
            # 파일 타입별 정보 추출
            if file_type == "pdf":
                content = result.get("content", "")
                return {
                    "status": "success",
                    "type": "pdf",
                    "summary": content[:1000] + "..." if len(content) > 1000 else content,
                    "page_count": result.get("page_count", 0)
                }
            elif file_type in ["excel", "csv"]:
                columns = result.get("columns", [])
                shape = result.get("shape", (0, 0))
                return {
                    "status": "success",
                    "type": file_type,
                    "columns": columns[:10],  # 최대 10개 컬럼만
                    "row_count": shape[0],
                    "column_count": shape[1]
                }
            elif file_type == "image":
                return {
                    "status": "success",
                    "type": "image",
                    "format": result.get("format", ""),
                    "size": result.get("size", "")
                }
        
        return {
            "status": "error",
            "message": result.get("error", "파일 처리 실패")
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }


def plan_content_structure(topic: str, content_format: str, reference_info: Optional[str] = None) -> dict:
    """
    콘텐츠 구조를 기획합니다.
    
    Args:
        topic: 콘텐츠 주제
        content_format: 콘텐츠 형식 (카드뉴스/뉴스레터/인포그래픽)
        reference_info: 참고자료에서 추출한 정보 (선택사항)
        
    Returns:
        기획된 콘텐츠 구조
    """
    base_structure = {
        "title": f"{topic}에 대한 {content_format}",
        "introduction": f"{topic}에 대해 자세히 알아보겠습니다.",
        "sections": [],
        "key_points": [],
        "conclusion": ""
    }
    
    # 참고자료 정보가 있으면 추가
    if reference_info:
        base_structure["reference_info"] = reference_info
    
    # 형식별 기본 구조
    if content_format == "카드뉴스":
        base_structure["sections"] = [
            {"title": "핵심 내용 1", "content": "", "key_points": []},
            {"title": "핵심 내용 2", "content": "", "key_points": []},
            {"title": "핵심 내용 3", "content": "", "key_points": []}
        ]
    elif content_format == "뉴스레터":
        base_structure["sections"] = [
            {"title": "주요 소식", "content": "", "key_points": []},
            {"title": "상세 내용", "content": "", "key_points": []}
        ]
    elif content_format == "인포그래픽":
        base_structure["sections"] = [
            {"title": "주요 통계", "content": "", "key_points": []},
            {"title": "핵심 정보", "content": "", "key_points": []}
        ]
        base_structure["statistics"] = []
        base_structure["visual_elements"] = []
    
    return base_structure


def format_content_output(content_data: dict, content_format: str) -> str:
    """
    콘텐츠를 선택한 형식에 맞게 포맷팅합니다.
    
    Args:
        content_data: 콘텐츠 데이터
        content_format: 콘텐츠 형식
        
    Returns:
        포맷팅된 콘텐츠 문자열
    """
    if content_format == "카드뉴스":
        return format_card_news(content_data)
    elif content_format == "뉴스레터":
        return format_newsletter(content_data)
    elif content_format == "인포그래픽":
        return format_infographic(content_data)
    else:
        return format_newsletter(content_data)  # 기본값


def generate_image_with_dalle(
    prompt: str,
    output_path: str,
    size: str = "1024x1024",
    quality: str = "standard"
) -> Optional[str]:
    """
    DALL-E를 사용하여 이미지를 생성하고 저장합니다.
    
    Args:
        prompt: 이미지 생성 프롬프트
        output_path: 이미지 저장 경로
        size: 이미지 크기 ("1024x1024", "1024x1792", "1792x1024")
        quality: 이미지 품질 ("standard", "hd")
        
    Returns:
        생성된 이미지 파일 경로 (실패 시 None)
    """
    if not OPENAI_CLIENT:
        return None
    
    try:
        # DALL-E 3로 이미지 생성
        response = OPENAI_CLIENT.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size=size,
            quality=quality,
            n=1,
        )
        
        # 이미지 다운로드 및 저장
        image_url = response.data[0].url
        img_response = requests.get(image_url, timeout=30)
        img_response.raise_for_status()
        
        # 디렉토리 생성
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # 파일 저장
        with open(output_path, "wb") as f:
            f.write(img_response.content)
        
        return output_path
        
    except Exception as e:
        print(f"이미지 생성 오류: {e}")
        return None


def create_content_base(topic: str, content_format: str, reference_files: Optional[List[str]] = None) -> dict:
    """
    기본 콘텐츠 제작 프로세스를 실행합니다 (텍스트만 생성).
    서브 에이전트에서 사용하는 공통 함수입니다.
    
    Args:
        topic: 콘텐츠 주제
        content_format: 콘텐츠 형식
        reference_files: 참고자료 파일 경로 리스트 (선택사항)
        
    Returns:
        생성된 콘텐츠 정보 (텍스트만)
    """
    # 1. 파일 처리 (있는 경우)
    reference_info = None
    if reference_files:
        file_summaries = []
        for file_path in reference_files:
            file_info = process_reference_file(file_path)
            if file_info.get("status") == "success":
                file_summaries.append(json.dumps(file_info, ensure_ascii=False))
        
        if file_summaries:
            reference_info = "\n\n".join(file_summaries)
    
    # 2. 콘텐츠 구조 기획
    plan = plan_content_structure(topic, content_format, reference_info)
    
    # 3. LLM을 사용하여 실제 콘텐츠 생성 (OpenAI 전용)
    if OPENAI_CLIENT:
        try:
            # 형식별 프롬프트 구성
            if content_format == "카드뉴스":
                format_guide = """
카드뉴스 형식으로 작성해주세요:
- 각 카드는 핵심 메시지 하나에 집중
- 간결하고 명확한 문장 (2-3문장)
- 시각적 요소 제안 포함
- 보통 5-10개의 카드로 구성
"""
            elif content_format == "뉴스레터":
                format_guide = """
뉴스레터 형식으로 작성해주세요:
- 전문적이고 깊이 있는 내용
- 각 섹션은 5-10문장으로 구성
- 독자와의 연결감을 주는 톤앤매너
- 명확한 섹션 구분
"""
            elif content_format == "인포그래픽":
                format_guide = """
인포그래픽 형식으로 작성해주세요:
- 통계, 숫자, 비교 데이터 강조
- 시각화 타입 제안 (막대 그래프, 원형 차트 등)
- 간결하고 명확한 정보 전달
- 비교/대조 요소 포함
"""
            else:
                format_guide = ""
            
            # 프롬프트 구성
            prompt = f"""당신은 전문 콘텐츠 작가입니다. 다음 주제와 형식에 맞는 콘텐츠를 생성해주세요.

주제: {topic}
콘텐츠 형식: {content_format}

{format_guide}

{reference_info if reference_info else "참고자료 없음"}

각 섹션의 content는 최소 200자 이상으로 구체적이고 전문적으로 작성해주세요."""
            
            # OpenAI JSON mode 사용 (response_format="json_object" + 스키마)
            response = OPENAI_CLIENT.beta.chat.completions.parse(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "당신은 전문 콘텐츠 작가입니다. 주어진 주제와 형식에 맞는 고품질 콘텐츠를 생성합니다."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                response_format=GeneratedContent,
                temperature=0.7,
            )
            
            # 파싱된 응답을 dict로 변환
            generated = response.choices[0].message.parsed.model_dump()
            
            # plan에 생성된 내용 병합
            plan.update({
                "title": generated.get("title", plan.get("title", "")),
                "introduction": generated.get("introduction", plan.get("introduction", "")),
                "sections": [
                    {
                        "title": section.get("title", ""),
                        "content": section.get("content", ""),
                        "key_points": section.get("key_points", [])
                    }
                    for section in generated.get("sections", [])
                ],
                "key_points": generated.get("key_points", plan.get("key_points", [])),
                "conclusion": generated.get("conclusion", plan.get("conclusion", ""))
            })
            
            # 인포그래픽의 경우 추가 필드
            if content_format == "인포그래픽":
                plan["statistics"] = generated.get("statistics", [])
                plan["visual_elements"] = generated.get("visual_elements", [])
                
        except Exception as e:
            # 오류 발생 시 기본 구조 유지
            pass
    
    # 4. 포맷팅된 콘텐츠 생성
    formatted_content = format_content_output(plan, content_format)
    
    return {
        "topic": topic,
        "format": content_format,
        "raw_content": plan,
        "formatted_content": formatted_content,
        "status": "success"
    }


def create_content(topic: str, content_format: str, reference_files: Optional[List[str]] = None) -> dict:
    """
    전체 콘텐츠 제작 프로세스를 실행합니다.
    형식에 따라 적절한 서브 에이전트를 호출합니다.
    
    Args:
        topic: 콘텐츠 주제
        content_format: 콘텐츠 형식
        reference_files: 참고자료 파일 경로 리스트 (선택사항)
        
    Returns:
        생성된 콘텐츠 정보 (이미지 포함)
    """
    # 서브 에이전트 함수 import
    from .subagents.card_news.agent import create_card_news
    from .subagents.newsletter.agent import create_newsletter
    from .subagents.infographic.agent import create_infographic
    
    # 형식에 따라 서브 에이전트 호출
    if content_format == "카드뉴스":
        return create_card_news(topic, reference_files)
    elif content_format == "뉴스레터":
        return create_newsletter(topic, reference_files)
    elif content_format == "인포그래픽":
        return create_infographic(topic, reference_files)
    else:
        # 기본값: 뉴스레터
        return create_newsletter(topic, reference_files)


def route_to_subagent(content_format: str, topic: str, reference_files: list = None) -> dict:
    """
    콘텐츠 형식에 따라 적절한 서브 에이전트로 라우팅합니다.
    
    Args:
        content_format: 콘텐츠 형식 (카드뉴스/뉴스레터/인포그래픽)
        topic: 콘텐츠 주제
        reference_files: 참고자료 파일 경로 리스트 (선택사항)
        
    Returns:
        생성된 콘텐츠 (이미지 포함)
    """
    # create_content가 이미 서브 에이전트를 호출하므로 그대로 사용
    return create_content(topic, content_format, reference_files)


# 메인 콘텐츠 제작 에이전트
from google.adk.models.lite_llm import LiteLlm
from google.adk.tools.agent_tool import AgentTool
from .prompt import ROOT_AGENT_DESCRIPTION, ROOT_AGENT_INSTRUCTION

# 서브 에이전트 import
from .subagents.card_news.agent import card_news_agent
from .subagents.newsletter.agent import newsletter_agent
from .subagents.infographic.agent import infographic_agent

ROOT_MODEL = LiteLlm(model="openai/gpt-4o-mini")

# 서브 에이전트를 AgentTool로 감싸기
card_news_tool = AgentTool(agent=card_news_agent)
newsletter_tool = AgentTool(agent=newsletter_agent)
infographic_tool = AgentTool(agent=infographic_agent)

root_agent = Agent(
    model=ROOT_MODEL,
    name='content_creator_agent',
    description=ROOT_AGENT_DESCRIPTION,
    instruction=ROOT_AGENT_INSTRUCTION,
    tools=[
        process_reference_file,  # 파일 처리 도구
        card_news_tool,          # 카드뉴스 제작 서브 에이전트
        newsletter_tool,          # 뉴스레터 제작 서브 에이전트
        infographic_tool,         # 인포그래픽 제작 서브 에이전트
    ],
)

