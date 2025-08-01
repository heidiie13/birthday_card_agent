import os
from dotenv import load_dotenv
import requests
from typing import List, Dict
import streamlit as st

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

def fetch_backgrounds(page: int = 1, page_size: int = 4) -> List[Dict]:
    try:
        resp = requests.get(f"{BACKEND_URL}/backgrounds", params={"page": page, "page_size": page_size})
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
                                st.session_state.pop("generated_card", None)  # Xóa thiệp đã tạo nếu chọn mẫu mới
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
                        st.session_state.pop("generated_card", None)  # Xóa thiệp đã tạo nếu random lại
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
                )
                if uploaded_file:
                    files = {"file": uploaded_file}
                    try:
                        upload_resp = requests.post(f"{BACKEND_URL}/upload_foreground", files=files)
                        upload_resp.raise_for_status()
                        upload_data = upload_resp.json()
                        if "error" not in upload_data:
                            # Ensure correct keys for foreground_path and foreground_url
                            fg_path = upload_data.get("foreground_path") or upload_data.get("file_path")
                            fg_url = upload_data.get("foreground_url") or upload_data.get("file_url")
                            st.session_state.uploaded_foreground = {
                                "foreground_path": fg_path,
                                "foreground_url": fg_url
                            }
                            st.success("✅ Ảnh đã upload thành công!")
                        else:
                            st.error(f"Lỗi upload: {upload_data['error']}")
                    except Exception as e:
                        st.error(f"Lỗi khi upload: {e}")
                
                # Show background selection after upload
                if "uploaded_foreground" in st.session_state:
                    st.divider()
                    st.markdown("**Chọn nền cho thiệp:**")
                    # Background pagination
                    if "bg_page" not in st.session_state:
                        st.session_state.bg_page = 1
                    backgrounds = fetch_backgrounds(st.session_state.bg_page, 4)
                    if backgrounds:
                        bg_cols = st.columns(4)
                        for idx in range(4):
                            if idx < len(backgrounds):
                                with bg_cols[idx]:
                                    bg = backgrounds[idx]
                                    bg_path = bg.get("background_path") or bg.get("file_path")
                                    bg_url = bg.get("background_url") or bg.get("file_url")
                                    st.image(bg_url, caption=f"Nền {idx+1}", width=80)
                                    if st.button("Chọn nền", key=f"select_bg_{idx}_{st.session_state.bg_page}", use_container_width=True):
                                        fg_path = st.session_state.uploaded_foreground.get("foreground_path")
                                        fg_url = st.session_state.uploaded_foreground.get("foreground_url")
                                        st.session_state.uploaded_template = {
                                            "foreground_path": fg_path,
                                            "background_path": bg_path,
                                            "foreground_url": fg_url,
                                            "background_url": bg_url
                                        }
                                        st.success("✅ Đã chọn nền!")
                                        st.rerun()
                        
                        # Background pagination controls
                        bg_pg_col1, bg_pg_col2, bg_pg_col3 = st.columns([1, 1, 1])
                        with bg_pg_col1:
                            if st.button("◀ Nền trước", disabled=(st.session_state.bg_page == 1), use_container_width=True):
                                st.session_state.bg_page -= 1
                                st.rerun()
                        with bg_pg_col2:
                            st.markdown(f"<div style='text-align:center;font-weight:bold;'>Nền {st.session_state.bg_page}</div>", unsafe_allow_html=True)
                        with bg_pg_col3:
                            if st.button("Nền sau ▶", disabled=(len(backgrounds) < 4), use_container_width=True):
                                st.session_state.bg_page += 1
                                st.rerun()
                    else:
                        st.warning("Không có nền nào để chọn")
                else:
                    st.info("Vui lòng upload ảnh trước")
    
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
                st.success("Ảnh và nền đã chọn")
                img_col1, img_col2, img_col3 = st.columns([0.2, 0.6, 0.2])
                with img_col2:
                    uploaded_template = st.session_state.uploaded_template
                    if uploaded_template.get('foreground_url'):
                        st.image(uploaded_template['foreground_url'], caption="Ảnh đã upload", width=200)
                    else:
                        st.info("Ảnh đang được xử lý...")
                    st.divider()
                    if uploaded_template.get('background_url'):
                        st.image(uploaded_template['background_url'], caption="Nền đã chọn", width=200)
            elif mode == "Tải ảnh lên" and "uploaded_foreground" in st.session_state:
                st.info("Đã upload ảnh, vui lòng chọn nền")
                img_col1, img_col2, img_col3 = st.columns([0.2, 0.6, 0.2])
                with img_col2:
                    uploaded_fg = st.session_state.uploaded_foreground
                    if uploaded_fg.get('foreground_url'):
                        st.image(uploaded_fg['foreground_url'], caption="Ảnh đã upload", width=200)
            else:
                if mode == "Chọn mẫu" and "selected_template" not in st.session_state:
                    st.info("Chọn mẫu để xem preview")
                elif mode == "Ngẫu nhiên" and "random_template" not in st.session_state:
                    st.info("Nhấn nút để lấy mẫu ngẫu nhiên")
                elif mode == "Tải ảnh lên" and "uploaded_foreground" not in st.session_state:
                    st.info("Upload ảnh và chọn nền")
                else:
                    st.info("Thiệp sẽ hiển thị ở đây sau khi tạo")

if __name__ == "__main__":
    main()