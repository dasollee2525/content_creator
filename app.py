"""
Streamlit 기반 콘텐츠 제작 에이전트 데모 앱
"""
import streamlit as st
import os
import tempfile
import zipfile
import io
from PIL import Image as PILImage

# 환경 변수로 모드 선택 (Streamlit Cloud에서는 secrets 사용)
USE_ADK_SERVER = os.getenv("USE_ADK_SERVER", "false").lower() == "true"
ADK_SERVER_URL = os.getenv("ADK_SERVER_URL", "")

if USE_ADK_SERVER and ADK_SERVER_URL:
    # Cloud Run ADK 서버 사용
    from content_creator.adk_client import create_content_via_adk as create_content
    from content_creator.adk_client import ADK_SERVER_URL as SERVER_URL
    MODE = "cloud"
else:
    # 로컬 직접 호출 (개발용)
    from content_creator.agent import root_agent, create_content
    MODE = "local"

# 페이지 설정
st.set_page_config(
    page_title="콘텐츠 제작 에이전트",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 세션 상태 초기화
if "result" not in st.session_state:
    st.session_state.result = None

# 사이드바
with st.sidebar:
    st.title("📝 콘텐츠 제작 에이전트")
    st.markdown("---")
    
    st.markdown("### ℹ️ 사용 방법")
    st.markdown("""
    1. 콘텐츠 주제를 입력하세요
    2. (선택) 참고자료 파일을 업로드하세요
    3. 콘텐츠 형식을 선택하세요
    4. 생성 버튼을 클릭하세요
    """)
    
    st.markdown("---")
    st.markdown("### 📋 지원 형식")
    st.markdown("""
    **콘텐츠 형식:**
    - 카드뉴스
    - 뉴스레터
    - 인포그래픽
    
    **파일 형식:**
    - PDF
    - 이미지 (PNG, JPG)
    - Excel (XLSX)
    - CSV
    """)
    
    st.markdown("---")
    st.markdown("### ⚙️ 에이전트 정보")
    if MODE == "cloud":
        st.info(f"🔗 모드: Cloud Run\n\n서버: {SERVER_URL}")
    else:
        st.info(f"💻 모드: 로컬\n\n에이전트: {root_agent.name}\n모델: {root_agent.model}")

# 메인 영역
st.title("🎨 콘텐츠 제작 에이전트")
st.markdown("Google ADK를 활용한 AI 기반 콘텐츠 제작 도구")

st.markdown("---")

# 입력 폼
col1, col2 = st.columns([2, 1])

with col1:
    topic = st.text_input(
        "📌 콘텐츠 주제",
        placeholder="예: 인공지능의 미래, 건강한 식습관, 최신 기술 트렌드 등",
        help="제작하고 싶은 콘텐츠의 주제를 입력하세요"
    )

with col2:
    content_format = st.selectbox(
        "📄 콘텐츠 형식",
        options=["카드뉴스", "뉴스레터", "인포그래픽"],
        help="원하는 콘텐츠 형식을 선택하세요"
    )

st.markdown("---")

# 파일 업로드
st.subheader("📎 참고자료 (선택사항)")
uploaded_files = st.file_uploader(
    "파일을 업로드하세요",
    type=["pdf", "png", "jpg", "jpeg", "xlsx", "csv"],
    accept_multiple_files=True,
    help="PDF, 이미지, Excel, CSV 파일을 업로드할 수 있습니다"
)

# 업로드된 파일 정보 표시
if uploaded_files:
    st.info(f"📁 {len(uploaded_files)}개의 파일이 업로드되었습니다.")
    for file in uploaded_files:
        st.text(f"  • {file.name} ({file.size:,} bytes)")

st.markdown("---")

# 생성 버튼
if st.button("🚀 콘텐츠 생성", type="primary", use_container_width=True):
    if not topic:
        st.error("❌ 콘텐츠 주제를 입력해주세요.")
    else:
        with st.spinner("콘텐츠를 생성하는 중입니다..."):
            # 파일 저장
            file_paths = []
            if uploaded_files:
                temp_dir = tempfile.mkdtemp()
                for uploaded_file in uploaded_files:
                    file_path = os.path.join(temp_dir, uploaded_file.name)
                    with open(file_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    file_paths.append(file_path)
            
            # 콘텐츠 생성
            try:
                # ADK 에이전트를 통해 콘텐츠 생성
                result = create_content(
                    topic=topic,
                    content_format=content_format,
                    reference_files=file_paths if file_paths else None
                )
                st.session_state.result = result
                st.success("✅ 콘텐츠가 성공적으로 생성되었습니다!")
            except Exception as e:
                st.error(f"❌ 오류가 발생했습니다: {str(e)}")
                st.exception(e)

# 결과 표시
if st.session_state.result:
    st.markdown("---")
    st.subheader("📝 생성된 콘텐츠")
    
    result_format = st.session_state.result.get("format", "")
    generated_images = st.session_state.result.get("images", [])
    
    # 이미지가 있으면 이미지 탭 추가
    if generated_images:
        tab_names = ["이미지", "포맷팅된 콘텐츠", "원본 데이터", "다운로드"]
    else:
        tab_names = ["포맷팅된 콘텐츠", "원본 데이터", "다운로드"]
    
    tabs = st.tabs(tab_names)
    tab_idx = 0
    
    # 이미지 탭
    if generated_images:
        with tabs[tab_idx]:
            if result_format == "카드뉴스":
                st.markdown("### 🎴 생성된 카드뉴스")
                cols = st.columns(min(2, len(generated_images)))
                for idx, img_path in enumerate(generated_images):
                    with cols[idx % 2]:
                        try:
                            img = PILImage.open(img_path)
                            st.image(img, caption=f"카드 {idx + 1}", use_container_width=True)
                            
                            with open(img_path, "rb") as f:
                                st.download_button(
                                    label=f"📥 카드 {idx + 1} 다운로드",
                                    data=f.read(),
                                    file_name=f"card_{idx + 1:02d}.png",
                                    mime="image/png",
                                    key=f"download_card_{idx}"
                                )
                        except Exception as e:
                            st.error(f"이미지 로드 오류: {e}")
            
            elif result_format == "인포그래픽":
                st.markdown("### 📊 생성된 인포그래픽")
                try:
                    img = PILImage.open(generated_images[0])
                    st.image(img, caption="인포그래픽", use_container_width=True)
                    
                    with open(generated_images[0], "rb") as f:
                        st.download_button(
                            label="📥 인포그래픽 다운로드",
                            data=f.read(),
                            file_name="infographic.png",
                            mime="image/png",
                            use_container_width=True
                        )
                except Exception as e:
                    st.error(f"이미지 로드 오류: {e}")
            
            elif result_format == "뉴스레터":
                st.markdown("### 📰 뉴스레터 이미지")
                for idx, img_path in enumerate(generated_images):
                    try:
                        img = PILImage.open(img_path)
                        caption = "헤더 이미지" if idx == 0 else f"섹션 이미지 {idx}"
                        st.image(img, caption=caption, use_container_width=True)
                        
                        with open(img_path, "rb") as f:
                            file_name = f"newsletter_{idx + 1}.png"
                            st.download_button(
                                label=f"📥 {caption} 다운로드",
                                data=f.read(),
                                file_name=file_name,
                                mime="image/png",
                                key=f"download_newsletter_{idx}"
                            )
                    except Exception as e:
                        st.error(f"이미지 로드 오류: {e}")
        
        tab_idx += 1
    
    # 포맷팅된 콘텐츠 탭
    with tabs[tab_idx]:
        formatted_content = st.session_state.result.get("formatted_content", "")
        st.text_area(
            "생성된 콘텐츠",
            value=formatted_content,
            height=500,
            label_visibility="collapsed"
        )
    
    tab_idx += 1
    
    # 원본 데이터 탭
    with tabs[tab_idx]:
        raw_content = st.session_state.result.get("raw_content", {})
        st.json(raw_content)
    
    tab_idx += 1
    
    # 다운로드 탭
    with tabs[tab_idx]:
        st.markdown("### 📥 콘텐츠 다운로드")
        
        # 텍스트 파일로 다운로드
        formatted_content = st.session_state.result.get("formatted_content", "")
        if formatted_content:
            st.download_button(
                label="📄 텍스트 파일로 다운로드",
                data=formatted_content,
                file_name=f"content_{result_format}_{topic[:20]}.txt",
                mime="text/plain",
                use_container_width=True
            )
        
        # JSON 파일로 다운로드
        import json
        json_content = json.dumps(st.session_state.result.get("raw_content", {}), ensure_ascii=False, indent=2)
        st.download_button(
            label="📋 JSON 파일로 다운로드",
            data=json_content,
            file_name=f"content_{result_format}_{topic[:20]}.json",
            mime="application/json",
            use_container_width=True
        )
        
        # 이미지 ZIP 다운로드 (이미지가 있는 경우)
        if generated_images:
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                for img_path in generated_images:
                    zip_file.write(img_path, os.path.basename(img_path))
            
            st.download_button(
                label="📦 모든 이미지 ZIP 다운로드",
                data=zip_buffer.getvalue(),
                file_name=f"images_{result_format}_{topic[:20]}.zip",
                mime="application/zip",
                use_container_width=True
            )

# 푸터
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: gray;'>"
    "콘텐츠 제작 에이전트 | Powered by Google ADK"
    "</div>",
    unsafe_allow_html=True
)

