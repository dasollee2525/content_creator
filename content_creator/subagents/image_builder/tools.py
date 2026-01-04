import base64
import os
from typing import Dict, Any, List, Optional
from openai import OpenAI
from google.adk.tools.tool_context import ToolContext

# OpenAI 클라이언트 (싱글턴)
_client = None

def get_openai_client():
    """OpenAI 클라이언트를 가져옵니다."""
    global _client
    if _client is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY가 설정되지 않았습니다.")
        _client = OpenAI(api_key=api_key)
    return _client


async def generate_images(tool_context: ToolContext):
    """
    콘텐츠 정보를 바탕으로 이미지를 생성합니다.
    
    state에서 다음 정보를 가져옵니다:
    - content_creator_output: 콘텐츠 생성 결과
      - format: 콘텐츠 형식 ("카드뉴스", "인포그래픽", "뉴스레터")
      - raw_content: 원본 콘텐츠 데이터
        - sections: 섹션 리스트 (카드뉴스/뉴스레터)
        - statistics: 통계 데이터 (인포그래픽)
        - visual_elements: 시각적 요소 (인포그래픽)
    """
    # 1) state에서 입력 꺼내기
    content_creator_output = tool_context.state.get("content_creator_output") or {}
    raw_content = content_creator_output.get("raw_content") or {}
    content_format = content_creator_output.get("format", "")
    
    if not content_format:
        return {
            "status": "error",
            "message": "콘텐츠 형식이 지정되지 않았습니다.",
            "total_images": 0,
            "generated_images": [],
        }
    
    # 2) 기존 artifact 목록 확인
    existing = await tool_context.list_artifacts()
    existing_names = set()
    if isinstance(existing, list):
        for item in existing:
            if isinstance(item, str):
                existing_names.add(item)
            elif isinstance(item, dict) and "filename" in item:
                existing_names.add(item["filename"])
    elif isinstance(existing, dict):
        existing_names = set(existing.keys())
    
    generated_images = []
    errors = []
    client = get_openai_client()
    
    # 3) 콘텐츠 형식에 따라 이미지 생성
    if content_format == "카드뉴스":
        sections = raw_content.get("sections", [])
        if not sections:
            return {
                "status": "error",
                "message": "카드뉴스 섹션이 없습니다.",
                "total_images": 0,
                "generated_images": [],
            }
        
        for idx, section in enumerate(sections, 1):
            card_title = section.get("title", f"카드 {idx}")
            card_content = section.get("content", "")
            total_cards = len(sections)
            
            filename = f"card_{idx:02d}.jpeg"
            
            # 이미 있으면 스킵
            if filename in existing_names:
                generated_images.append({
                    "card_number": idx,
                    "title": card_title,
                    "filename": filename,
                    "cached": True,
                })
                continue
            
            try:
                # 이미지 생성 프롬프트 구성
                enhanced_prompt = f"""Create a modern Korean card news image for social media:

Card {idx}/{total_cards}
Title: {card_title}

Content: {card_content[:200]}

Design requirements:
- Modern, clean design suitable for Instagram/SNS
- Square format (1080x1080)
- Bold, readable Korean text
- Attractive color scheme
- Professional layout
- Card number indicator visible
- Eye-catching visual elements

Style: Modern infographic, clean typography, vibrant colors"""
                
                # OpenAI 이미지 생성
                image = client.images.generate(
                    model="gpt-image-1",
                    prompt=enhanced_prompt,
                    n=1,
                    size="1024x1024",
                    output_format="jpeg",
                    background="opaque",
                )
                
                img_b64 = image.data[0].b64_json
                image_bytes = base64.b64decode(img_b64)
                
                # 4) artifact 저장
                await tool_context.save_artifact(
                    filename=filename,
                    artifact=image_bytes,
                    mime_type="image/jpeg",
                )
                
                generated_images.append({
                    "card_number": idx,
                    "title": card_title,
                    "filename": filename,
                    "cached": False,
                })
                
            except Exception as e:
                errors.append({
                    "card_number": idx,
                    "filename": filename,
                    "error": str(e)
                })
    
    elif content_format == "인포그래픽":
        title = raw_content.get("title", "")
        statistics = raw_content.get("statistics", [])
        visual_elements = raw_content.get("visual_elements", [])
        
        filename = "infographic.jpeg"
        
        if filename in existing_names:
            generated_images.append({
                "title": title,
                "filename": filename,
                "cached": True,
            })
        else:
            try:
                # 통계 데이터 텍스트 구성
                stats_text = "\n".join([
                    f"- {stat.get('label', '')}: {stat.get('value', '')}"
                    for stat in statistics[:10]
                ])
                
                enhanced_prompt = f"""Create a professional infographic image:

Title: {title}

Key Statistics:
{stats_text}

Design requirements:
- Professional infographic design
- Clear data visualization with charts, graphs, and icons
- Modern, clean layout
- Vibrant but professional colors
- Korean text support
- Portrait format (1080x1920)

Style: Data visualization, modern infographic, professional design"""
                
                image = client.images.generate(
                    model="gpt-image-1",
                    prompt=enhanced_prompt,
                    n=1,
                    size="1024x1792",
                    output_format="jpeg",
                    background="opaque",
                    quality="hd",
                )
                
                img_b64 = image.data[0].b64_json
                image_bytes = base64.b64decode(img_b64)
                
                await tool_context.save_artifact(
                    filename=filename,
                    artifact=image_bytes,
                    mime_type="image/jpeg",
                )
                
                generated_images.append({
                    "title": title,
                    "filename": filename,
                    "cached": False,
                })
                
            except Exception as e:
                errors.append({
                    "filename": filename,
                    "error": str(e)
                })
    
    elif content_format == "뉴스레터":
        title = raw_content.get("title", "")
        introduction = raw_content.get("introduction", "")
        sections = raw_content.get("sections", [])
        
        # 헤더 이미지
        header_filename = "newsletter_header.jpeg"
        if header_filename not in existing_names:
            try:
                header_prompt = f"""Create a professional newsletter header image:

Title: {title}
Introduction: {introduction[:150]}

Design requirements:
- Professional newsletter header design
- Elegant and sophisticated style
- Landscape format (1200x600)
- Clean typography
- Subtle, professional color scheme

Style: Modern newsletter header, professional, elegant"""
                
                image = client.images.generate(
                    model="gpt-image-1",
                    prompt=header_prompt,
                    n=1,
                    size="1792x1024",
                    output_format="jpeg",
                    background="opaque",
                )
                
                img_b64 = image.data[0].b64_json
                image_bytes = base64.b64decode(img_b64)
                
                await tool_context.save_artifact(
                    filename=header_filename,
                    artifact=image_bytes,
                    mime_type="image/jpeg",
                )
                
                generated_images.append({
                    "type": "header",
                    "filename": header_filename,
                    "cached": False,
                })
            except Exception as e:
                errors.append({
                    "filename": header_filename,
                    "error": str(e)
                })
        else:
            generated_images.append({
                "type": "header",
                "filename": header_filename,
                "cached": True,
            })
        
        # 섹션 이미지 (첫 번째 섹션만)
        if sections:
            section_filename = "newsletter_section.jpeg"
            if section_filename not in existing_names:
                main_section = sections[0]
                section_title = main_section.get("title", "")
                section_content = main_section.get("content", "")
                
                try:
                    section_prompt = f"""Create an illustration image for newsletter content:

Section Title: {section_title}
Content Summary: {section_content[:150]}

Design requirements:
- Newsletter illustration style
- Professional and engaging
- Landscape format (800x600)
- Clean, modern design

Style: Newsletter illustration, professional, engaging"""
                    
                    image = client.images.generate(
                        model="gpt-image-1",
                        prompt=section_prompt,
                        n=1,
                        size="1024x1024",
                        output_format="jpeg",
                        background="opaque",
                    )
                    
                    img_b64 = image.data[0].b64_json
                    image_bytes = base64.b64decode(img_b64)
                    
                    await tool_context.save_artifact(
                        filename=section_filename,
                        artifact=image_bytes,
                        mime_type="image/jpeg",
                    )
                    
                    generated_images.append({
                        "type": "section",
                        "filename": section_filename,
                        "cached": False,
                    })
                except Exception as e:
                    errors.append({
                        "filename": section_filename,
                        "error": str(e)
                    })
            else:
                generated_images.append({
                    "type": "section",
                    "filename": section_filename,
                    "cached": True,
                })
    
    else:
        return {
            "status": "error",
            "message": f"지원하지 않는 콘텐츠 형식: {content_format}",
            "total_images": 0,
            "generated_images": [],
        }
    
    status = "complete" if not errors else ("partial_success" if generated_images else "error")
    
    return {
        "status": status,
        "total_images": len(generated_images),
        "generated_images": generated_images,
        "errors": errors if errors else None,
    }

