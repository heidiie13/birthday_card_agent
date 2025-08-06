import logging
import os
from dotenv import load_dotenv
import requests
from typing import List, Dict
import streamlit as st

logger = logging.getLogger(__name__)

load_dotenv()

BACKEND_URL = os.getenv("BACKEND_URL")

st.set_page_config(page_title="Card Generator", layout="wide")

def fetch_templates(card_type: str = "birthday", aspect_ratio: float = 3/4, page: int = 1, page_size: int = 4) -> List[Dict]:
    try:
        resp = requests.get(f"{BACKEND_URL}/templates/{card_type}", params={"aspect_ratio": aspect_ratio, "page": page, "page_size": page_size})
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        st.error(f"Lỗi khi lấy mẫu: {e}")
        return []

def fetch_random_template(card_type: str = "birthday", aspect_ratio: float = 3/4) -> Dict:
    try:
        resp = requests.get(f"{BACKEND_URL}/random-template/{card_type}", params={"aspect_ratio": aspect_ratio})
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        st.error(f"Lỗi khi lấy mẫu ngẫu nhiên: {e}")
        return {}

def main():
    st.markdown(
        "<h1 style='text-align: center; color: #3495eb;'> 🌟 Tạo Thiệp Chúc Mừng</h1>", 
        unsafe_allow_html=True
    )
    
    left_col, right_col = st.columns([1, 2])
    
    with left_col:
        st.subheader("Tạo thiệp")
        
        if "greeting_text" not in st.session_state:
            st.session_state.greeting_text = ""
    
        greeting_text = st.text_area(
            "Yêu cầu nội dung thiệp *",
            height=100,
            key="greeting_text_input"
        )

        mode = "Ngẫu nhiên"
        aspect_options = {"3:4": 3/4, "4:3": 4/3}
        selected_aspect_label = st.radio(
            "Chọn tỉ lệ khung hình:",
            list(aspect_options.keys()),
            horizontal=True,
            key="aspect_ratio_selection"
        )
        selected_aspect_ratio = aspect_options[selected_aspect_label]

        customize_mode = st.toggle("Mẫu tùy chỉnh")
        
        if "current_customize_mode" not in st.session_state:
            st.session_state.current_customize_mode = customize_mode
        elif st.session_state.current_customize_mode != customize_mode:
            if not customize_mode:
                st.session_state.pop("uploaded_template", None)
                st.session_state.pop("uploaded_foreground", None)
                st.session_state.pop("last_uploaded_file", None)
                st.session_state.pop("selected_template", None)
                st.session_state.pop("random_template", None)
                st.session_state.pop("generated_card", None)
            st.session_state.current_customize_mode = customize_mode
        
        
        
        if customize_mode:
            with st.container(height=500):
                mode = st.radio(
                    "Chọn cách lấy mẫu:",
                    ["Tải ảnh lên", "Chọn mẫu", "Ngẫu nhiên"],
                    horizontal=False,
                    key="mode_selection"
                )
              
                if "current_mode" not in st.session_state:
                    st.session_state.current_mode = mode
                elif st.session_state.current_mode != mode:
                    if st.session_state.current_mode == "Tải ảnh lên":
                        st.session_state.pop("uploaded_template", None)
                        st.session_state.pop("uploaded_foreground", None)
                        st.session_state.pop("last_uploaded_file", None)
                    elif st.session_state.current_mode == "Chọn mẫu":
                        st.session_state.pop("selected_template", None)
                    elif st.session_state.current_mode == "Ngẫu nhiên":
                        st.session_state.pop("random_template", None)
                    
                    st.session_state.current_mode = mode
                    st.session_state.pop("generated_card", None)  
                
                if mode in ["Chọn mẫu", "Ngẫu nhiên"]:
                    card_type = st.selectbox(
                        "Loại thiệp:",
                        [
                            "birthday", 
                            "christmas", 
                            "graduation", 
                            "newyear", 
                            "lunar_newyear", 
                            "mid_autumn_festival", 
                            "valentine", 
                            "vietnam_teacherday", 
                            "vietnam_nationalday", 
                            "vietnam_womenday", 
                            "wedding", 
                            "international_womenday", 
                            "general"
                        ],
                        format_func=lambda x: {
                            "birthday": "Sinh nhật",
                            "christmas": "Giáng sinh",
                            "graduation": "Tốt nghiệp", 
                            "newyear": "Tết Dương lịch",
                            "lunar_newyear": "Tết Nguyên đán",
                            "mid_autumn_festival": "Tết Trung thu",
                            "valentine": "Lễ tình nhân",
                            "vietnam_teacherday": "Ngày Nhà giáo Việt Nam (20/11)",
                            "vietnam_nationalday": "Quốc khánh Việt Nam (2/9)",
                            "vietnam_womenday": "Ngày Phụ nữ Việt Nam (20/10)",
                            "wedding": "Lễ cưới",
                            "international_womenday": "Ngày Quốc tế Phụ nữ (8/3)",
                            "general": "Thiệp chung"
                        }.get(x, x),
                        help="Chọn loại thiệp chúc bạn muốn tạo"
                    )
                
                if "current_aspect_ratio" not in st.session_state:
                    st.session_state.current_aspect_ratio = selected_aspect_ratio
                elif st.session_state.current_aspect_ratio != selected_aspect_ratio:
                    st.session_state.current_aspect_ratio = selected_aspect_ratio
                    st.session_state.pop("generated_card", None)  
                    
                    if mode == "Tải ảnh lên" and "uploaded_template" in st.session_state and "uploaded_foreground" in st.session_state:
                        fg_path = st.session_state.uploaded_foreground.get("foreground_path")
                        fg_url = st.session_state.uploaded_foreground.get("foreground_url")
                        
                        # Get existing background info from uploaded_template
                        current_template = st.session_state.uploaded_template
                        bg_path = current_template.get("background_path")
                        bg_url = current_template.get("background_url")

                        st.session_state.uploaded_template = {
                            "foreground_path": fg_path,
                            "background_path": bg_path,
                            "foreground_url": fg_url,
                            "background_url": bg_url,
                            "aspect_ratio": selected_aspect_ratio
                        }
                
                st.divider()
                
                if mode == "Chọn mẫu":
                    st.markdown("**Mẫu thiệp**")
                    
                    if "templates_page" not in st.session_state:
                        st.session_state.templates_page = 1
                    if "templates_card_type" not in st.session_state or st.session_state.templates_card_type != card_type:
                        st.session_state.templates_page = 1
                        st.session_state.templates_card_type = card_type
                    
                    templates = fetch_templates(card_type, selected_aspect_ratio, st.session_state.templates_page, 4)
                    
                    cols = st.columns(2)
                    has_templates = bool(templates)
                    for idx in range(min(4, len(templates) if templates else 0)):
                        with cols[idx % 2]:
                            if has_templates and idx < len(templates):
                                template = templates[idx]
                                img_url = template.get('merged_image_url', f"{BACKEND_URL}/{template['merged_image_path']}")
                                st.image(img_url, caption=f"Mẫu {idx+1}", use_container_width=True)
                                if st.button(f"Chọn mẫu {idx+1}", key=f"select_template_{idx}_{st.session_state.templates_page}", use_container_width=True):
                                    st.session_state.selected_template = template
                                    st.session_state.pop("generated_card", None)
                                    st.success("✅ Đã chọn mẫu!")
                                    st.rerun()
                    
                    pg_col1, pg_col2, pg_col3 = st.columns([1, 1, 1])
                    with pg_col1:
                        if st.button("◀ Trang trước", disabled=(st.session_state.templates_page == 1), use_container_width=True):
                            st.session_state.templates_page -= 1
                            st.rerun()
                    with pg_col2:
                        st.markdown(f"<div style='text-align:center;font-weight:bold;'>Trang {st.session_state.templates_page}</div>", unsafe_allow_html=True)
                    with pg_col3:
                        if st.button("Trang sau ▶", disabled=(not has_templates or len(templates) < 4), use_container_width=True):
                            st.session_state.templates_page += 1
                            st.rerun()
                    if not has_templates and st.session_state.templates_page == 1:
                        st.info("Không có mẫu nào")
                        
                elif mode == "Ngẫu nhiên":
                    st.markdown("**Mẫu ngẫu nhiên**")
                    if st.button("🎲 Lấy mẫu ngẫu nhiên", use_container_width=True):
                        random_template = fetch_random_template(card_type, selected_aspect_ratio)
                        if random_template:
                            st.session_state.random_template = random_template
                            st.session_state.pop("generated_card", None)
                            st.rerun()
                    if "random_template" in st.session_state:
                        template = st.session_state.random_template
                        img_url = template.get("merged_image_url", f"{BACKEND_URL}/{template['merged_image_path']}")
                        col1, col2, col3 = st.columns([1, 2, 1])
                        with col2:
                            st.image(img_url, caption="Mẫu ngẫu nhiên", use_container_width=True)
                
                elif mode == "Tải ảnh lên":
                    st.markdown("**Upload ảnh**")
                    st.info("Chọn ảnh để upload")
                    uploaded_file = st.file_uploader(
                        "Chọn ảnh cho thiệp:",
                        type=["png", "jpg", "jpeg", "webp"],
                        key="file_uploader"
                    )

                    if "last_uploaded_file" not in st.session_state:
                        st.session_state.last_uploaded_file = None
                    if "uploaded_foreground" not in st.session_state:
                        st.session_state.uploaded_foreground = None
                        
                    if uploaded_file and uploaded_file != st.session_state.last_uploaded_file:
                        st.session_state.pop("uploaded_template", None)
                        st.session_state.pop("generated_card", None)
                        
                        files = {"file": uploaded_file}
                        try:
                            upload_resp = requests.post(f"{BACKEND_URL}/upload-foreground", files=files)
                            upload_resp.raise_for_status()
                            upload_data = upload_resp.json()
                            if "error" not in upload_data:
                                fg_path = upload_data.get("foreground_path")
                                fg_url = upload_data.get("foreground_url")
                                st.session_state.uploaded_foreground = {
                                    "foreground_path": fg_path,
                                    "foreground_url": fg_url
                                }
                                st.session_state.last_uploaded_file = uploaded_file  
                                st.success("✅ Ảnh đã upload thành công!")
                            else:
                                st.error(f"Lỗi upload: {upload_data['error']}")
                        except Exception as e:
                            st.error(f"Lỗi khi upload: {e}")
                        st.rerun()

                    if "uploaded_foreground" in st.session_state and st.session_state.uploaded_foreground:
                        st.divider()
                        if "uploaded_template" not in st.session_state:
                            fg_path = st.session_state.uploaded_foreground.get("foreground_path")
                            fg_url = st.session_state.uploaded_foreground.get("foreground_url")
                            st.session_state.uploaded_template = {
                                "foreground_path": fg_path,
                                "foreground_url": fg_url,
                                "aspect_ratio": selected_aspect_ratio
                            }
                        
                        uploaded_template = st.session_state.uploaded_template
                        if uploaded_template.get('foreground_url'):
                            st.image(uploaded_template['foreground_url'], caption="Ảnh đã upload", width=200)
        
        st.session_state.selected_aspect_ratio = selected_aspect_ratio
        
        st.divider()
        generate_btn = st.button("🎨 Tạo thiệp", type="primary", use_container_width=True)
        
        if generate_btn:
            if not greeting_text:
                st.error("Vui lòng nhập yêu cầu nội dung thiệp!")
            else:
                selected_template_gen = None
                if not customize_mode:
                    selected_template_gen = None  
                elif mode == "Ngẫu nhiên" and "random_template" in st.session_state:
                    selected_template_gen = st.session_state.random_template
                elif mode == "Chọn mẫu" and "selected_template" in st.session_state:
                    selected_template_gen = st.session_state.selected_template
                elif mode == "Tải ảnh lên" and "uploaded_template" in st.session_state:
                    selected_template_gen = st.session_state.uploaded_template

                payload = {"greeting_text_instructions": greeting_text}
                payload["aspect_ratio"] = st.session_state.get("selected_aspect_ratio", 3/4)

                if selected_template_gen:
                    bg_path = selected_template_gen.get("background_path")
                    fg_path = selected_template_gen.get("foreground_path")
                    merged_path = selected_template_gen.get("merged_image_path")
                    if bg_path:
                        payload["background_path"] = bg_path
                    if fg_path:
                        payload["foreground_path"] = fg_path
                    if merged_path:
                        payload["merged_image_path"] = merged_path
                        
                logger.info(f"Payload for card generation: {payload}")
                
                with st.status("Đang tạo thiệp...", expanded=True):
                    try:
                        resp = requests.post(f"{BACKEND_URL}/generate-card", json=payload)
                        resp.raise_for_status()
                        result = resp.json()
                        st.session_state.generated_card = result
                        st.success("✅ Tạo thiệp thành công!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Lỗi khi tạo thiệp: {e}")

    with right_col:
        st.markdown(
            """
            <div style="display: flex; flex-direction: column; align-items: center; text-align: center;">
            """, 
            unsafe_allow_html=True
        )
        
        st.markdown("<h3 style='text-align: center;'>Kết quả</h3>", unsafe_allow_html=True)
        
        if "generated_card" in st.session_state:
            card_data = st.session_state.generated_card
            card_url = card_data.get("card_url")
            
            if card_url:
                col1, col2, col3 = st.columns([2, 2, 2])
                with col2:
                    st.success("✅ Thiệp đã tạo thành công!")
                
                col1, col2, col3 = st.columns([2, 2, 2])
                with col2:
                    st.image(card_url, use_container_width=True)

                col1, col2, col3 = st.columns([2, 2, 2])
                with col2:
                    try:
                        card_response = requests.get(card_url)
                        card_response.raise_for_status()
                        
                        st.download_button(
                            "📥 Tải thiệp về máy",
                            data=card_response.content,
                            file_name="thiep_chuc.png",
                            mime="image/png",
                            use_container_width=True
                        )
                    except Exception as e:
                        st.error(f"Lỗi khi tải ảnh: {e}")
            else:
                st.error("Không thể hiển thị thiệp")
        else:
            col1, col2, col3 = st.columns([3, 2, 3])
            with col2:
                st.info("Thiệp sẽ hiển thị ở đây sau khi tạo")
        
        st.markdown("</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
