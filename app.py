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

def fetch_templates(card_type: str = "birthday", page: int = 1, page_size: int = 4) -> List[Dict]:
    try:
        resp = requests.get(f"{BACKEND_URL}/templates/{card_type}", params={"page": page, "page_size": page_size})
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        st.error(f"Lỗi khi lấy mẫu: {e}")
        return []

def fetch_random_template(card_type: str = "birthday") -> Dict:
    try:
        resp = requests.get(f"{BACKEND_URL}/random-template/{card_type}")
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        st.error(f"Lỗi khi lấy mẫu ngẫu nhiên: {e}")
        return {}

def fetch_random_background() -> dict:
    try:
        resp = requests.get(f"{BACKEND_URL}/random-background")
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        st.error(f"Lỗi khi lấy background: {e}")
        return []

def main():
    st.markdown(
        "<h1 style='text-align: center; color: #3495eb;'> 🌟 Tạo Thiệp Chúc Mừng</h1>", 
        unsafe_allow_html=True
    )
    
    left_col, center_col, right_col = st.columns([1, 1.5, 1])
    
    with left_col:
        st.subheader("Chọn mẫu thiệp")
        
        mode = st.radio(
            "Chọn cách lấy mẫu:",
            ["Tải ảnh lên", "Chọn mẫu", "Ngẫu nhiên"],
            horizontal=False,
        )
        
        card_type = "birthday"
        if mode in ["Chọn mẫu", "Ngẫu nhiên"]:
            card_type = st.selectbox(
                "Loại thiệp:",
                ["birthday", "graduation", "wedding"],
                format_func=lambda x: "Sinh nhật" if x == "birthday" else "Tốt nghiệp" if x == "graduation" else "Cưới",
                help="Chọn loại thiệp chúc bạn muốn tạo"
            )
        
        st.divider()
        
        greeting_text = st.text_area(
            "Yêu cầu nội dung thiệp *",
            placeholder="VD: Thiệp chúc mừng sinh nhật cho bé gái tên Linh",
        )

        aspect_options = {"3:4": 3/4, "4:3": 4/3}
        selected_aspect_label = st.radio(
            "Chọn tỉ lệ khung hình:",
            list(aspect_options.keys()),
            horizontal=True,
        )
        selected_aspect_ratio = aspect_options[selected_aspect_label]
        st.session_state.selected_aspect_ratio = selected_aspect_ratio

        generate_btn = st.button("🎨 Tạo thiệp", type="primary", use_container_width=True)

    with center_col:
        if mode == "Chọn mẫu":
            st.markdown("<h3 style='text-align:center;'>Mẫu thiệp</h3>", unsafe_allow_html=True)
            
            # Khởi tạo pagination
            if "templates_page" not in st.session_state:
                st.session_state.templates_page = 1
            if "templates_card_type" not in st.session_state or st.session_state.templates_card_type != card_type:
                st.session_state.templates_page = 1
                st.session_state.templates_card_type = card_type
            
            templates = fetch_templates(card_type, st.session_state.templates_page, 4)
            
            cols = st.columns(4)
            has_templates = bool(templates)
            for idx in range(4):
                with cols[idx]:
                    if has_templates and idx < len(templates):
                        template = templates[idx]
                        img_url = template.get('merged_image_url', f"{BACKEND_URL}/{template['merged_image_path']}")
                        st.image(img_url, caption=f"Mẫu {idx+1}", width=120)
                        # Căn giữa nút chọn bằng cách chia cột nhỏ hơn
                        btn_col1, btn_col2, btn_col3 = st.columns([0.1, 0.6, 0.3])
                        with btn_col2:
                            if st.button("Chọn", key=f"select_template_{idx}_{st.session_state.templates_page}", use_container_width=True):
                                st.session_state.selected_template = template
                                st.session_state.pop("generated_card", None)
                                st.success("✅ Đã chọn mẫu!")
                                st.rerun()
                    else:
                        st.empty()

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
            st.markdown("<h3 style='text-align:center;'>Mẫu ngẫu nhiên</h3>", unsafe_allow_html=True)
            center_col1, center_col2, center_col3 = st.columns([0.2, 0.6, 0.2])
            with center_col2:
                if st.button("🎲 Lấy mẫu ngẫu nhiên", use_container_width=True):
                    random_template = fetch_random_template(card_type)
                    if random_template:
                        st.session_state.random_template = random_template
                        st.session_state.pop("generated_card", None)
                        st.rerun()
                if "random_template" in st.session_state:
                    template = st.session_state.random_template
                    img_url = template.get("merged_image_url", f"{BACKEND_URL}/{template['merged_image_path']}")
                    st.markdown(
                        f"""
                        <div style="display: flex; justify-content: center;">
                            <img src="{img_url}" alt="Mẫu ngẫu nhiên" style="width: 200px; display: block; margin: 0 auto; border-radius: 0.5rem;">
                        </div>
                        <p style="text-align: center;">Mẫu ngẫu nhiên</p>
                        """,
                        unsafe_allow_html=True
                    )
        
        elif mode == "Tải ảnh lên":
            st.markdown("<h3 style='text-align:center;'>Upload ảnh</h3>", unsafe_allow_html=True)
            upload_col1, upload_col2, upload_col3 = st.columns([0.2, 0.6, 0.2])
            with upload_col2:
                st.info("Chọn ảnh để upload")
                uploaded_file = st.file_uploader(
                    "Chọn ảnh cho thiệp:",
                    type=["png", "jpg", "jpeg", "webp"],
                    key="file_uploader"  # Add a unique key to the uploader
                )

                # Initialize session state for tracking uploaded file
                if "last_uploaded_file" not in st.session_state:
                    st.session_state.last_uploaded_file = None
                if "uploaded_foreground" not in st.session_state:
                    st.session_state.uploaded_foreground = None
                    
                # Only process upload if a new file is uploaded
                if uploaded_file and uploaded_file != st.session_state.last_uploaded_file:
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
                            st.session_state.last_uploaded_file = uploaded_file  # Track the uploaded file
                            st.success("✅ Ảnh đã upload thành công!")
                        else:
                            st.error(f"Lỗi upload: {upload_data['error']}")
                    except Exception as e:
                        st.error(f"Lỗi khi upload: {e}")

                # Show background selection after upload
                if "uploaded_foreground" in st.session_state and st.session_state.uploaded_foreground:
                    st.divider()
                    st.session_state.pop("generated_card", None)
                    # st.rerun()
                    # Initialize uploaded_template if not already set
                    if "uploaded_template" not in st.session_state:
                        background = fetch_random_background()
                        fg_path = st.session_state.uploaded_foreground.get("foreground_path")
                        fg_url = st.session_state.uploaded_foreground.get("foreground_url")
                        st.session_state.uploaded_template = {
                            "foreground_path": fg_path,
                            "background_path": background.get("background_path"),
                            "foreground_url": fg_url,
                            "background_url": background.get("background_url")
                        }
    
    with left_col:
        if generate_btn:
            if not greeting_text:
                st.error("Vui lòng nhập yêu cầu nội dung thiệp!")
            else:
                selected_template_gen = None
                if mode == "Ngẫu nhiên" and "random_template" in st.session_state:
                    selected_template_gen = st.session_state.random_template
                elif mode == "Chọn mẫu" and "selected_template" in st.session_state:
                    selected_template_gen = st.session_state.selected_template
                elif mode == "Tải ảnh lên" and "uploaded_template" in st.session_state:
                    selected_template_gen = st.session_state.uploaded_template

                payload = {"greeting_text_instructions": greeting_text}
                # Thêm tỉ lệ khung hình vào payload
                payload["aspect_ratio"] = st.session_state.get("selected_aspect_ratio", 3/4)

                if selected_template_gen:
                    # Always use the correct keys for API
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
                
                if "selected_template" in st.session_state:
                    del st.session_state["selected_template"]
                if "random_template" in st.session_state:
                    del st.session_state["random_template"]
                if "uploaded_template" in st.session_state:
                    del st.session_state["uploaded_template"]
                if "uploaded_foreground" in st.session_state:
                    del st.session_state["uploaded_foreground"]

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
            "<div style='height: 60px;'></div>",
            unsafe_allow_html=True
        )
        
        if "generated_card" in st.session_state:
            card_data = st.session_state.generated_card
            card_url = card_data.get("card_url")
            
            if card_url:
                st.success("Thiệp đã tạo thành công!")
                img_col1, img_col2, img_col3 = st.columns([0.2, 0.6, 0.2])
                with img_col2:
                    st.image(card_url, width=250)
                
                col1, col2, col3 = st.columns([0.2, 0.6, 0.2])
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
            if mode == "Chọn mẫu" and "selected_template" in st.session_state:
                st.success("Mẫu đã chọn")
                img_url = st.session_state.selected_template.get('merged_image_url', 
                        f"{BACKEND_URL}/{st.session_state.selected_template['merged_image_path']}")
                img_col1, img_col2, img_col3 = st.columns([0.2, 0.6, 0.2])
                with img_col2:
                    st.image(img_url, width=200)
            elif mode == "Ngẫu nhiên" and "random_template" in st.session_state:
                st.success("Mẫu ngẫu nhiên")
                template = st.session_state.random_template
                img_url = template.get("merged_image_url", f"{BACKEND_URL}/{template['merged_image_path']}")
                img_col1, img_col2, img_col3 = st.columns([0.2, 0.6, 0.2])
                with img_col2:
                    st.image(img_url, width=200)
            elif mode == "Tải ảnh lên" and "uploaded_template" in st.session_state:
                st.success("Ảnh đã upload")
                img_col1, img_col2, img_col3 = st.columns([0.2, 0.6, 0.2])
                with img_col2:
                    uploaded_template = st.session_state.uploaded_template
                    if uploaded_template.get('foreground_url'):
                        st.image(uploaded_template['foreground_url'], caption="Ảnh đã upload", width=200)
                    else:
                        st.info("Ảnh đang được xử lý...")
                    st.divider()
                    if uploaded_template.get('background_url'):
                        st.image(uploaded_template['background_url'], caption="Nền ngẫu nhiên", width=200)
                        if st.button("🔄 Đổi nền", key="change_uploaded_bg", use_container_width=True):
                            new_bg = fetch_random_background()
                            fg_path = uploaded_template.get("foreground_path")
                            fg_url = uploaded_template.get("foreground_url")
                            st.session_state.uploaded_template = {
                                "foreground_path": fg_path,
                                "background_path": new_bg.get("background_path"),
                                "foreground_url": fg_url,
                                "background_url": new_bg.get("background_url")
                            }
                            st.rerun()
            elif mode == "Tải ảnh lên" and "uploaded_template" in st.session_state:
                st.success("Ảnh đã upload")
                img_col1, img_col2, img_col3 = st.columns([0.2, 0.6, 0.2])
                with img_col2:
                    uploaded_template = st.session_state.uploaded_template
                    if uploaded_template.get('foreground_url'):
                        st.image(uploaded_template['foreground_url'], caption="Ảnh đã upload", width=200)
                    else:
                        st.info("Ảnh đang được xử lý...")
                    st.divider()
                    if uploaded_template.get('background_url'):
                        st.image(uploaded_template['background_url'], caption="Nền ngẫu nhiên", width=200)
                        if st.button("🔄 Đổi nền", key="change_uploaded_bg", use_container_width=True):
                            new_bg = fetch_random_background()
                            # Update only the background-related fields
                            st.session_state.uploaded_template.update({
                                "background_path": new_bg.get("background_path"),
                                "background_url": new_bg.get("background_url")
                            })
                            st.rerun()
            else:
                if mode == "Chọn mẫu" and "selected_template" not in st.session_state:
                    st.info("Chọn mẫu để xem preview")
                elif mode == "Ngẫu nhiên" and "random_template" not in st.session_state:
                    st.info("Thiệp sẽ hiển thị ở đây sau khi tạo")
                elif mode == "Tải ảnh lên" and "uploaded_foreground" not in st.session_state:
                    pass
                else:
                    st.info("Thiệp sẽ hiển thị ở đây sau khi tạo")

if __name__ == "__main__":
    main()