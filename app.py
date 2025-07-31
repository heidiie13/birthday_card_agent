import streamlit as st
import requests
from typing import List, Dict

API_URL = "http://localhost:8000"

st.set_page_config(page_title="Card Generator", layout="wide")

def fetch_templates(card_type: str = "birthday", page: int = 1, page_size: int = 4) -> List[Dict]:
    try:
        resp = requests.get(f"{API_URL}/templates/{card_type}", params={"page": page, "page_size": page_size})
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        st.error(f"Lỗi khi lấy mẫu: {e}")
        return []

def fetch_random_template(card_type: str = "birthday") -> Dict:
    try:
        resp = requests.get(f"{API_URL}/random-template/{card_type}")
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        st.error(f"Lỗi khi lấy mẫu ngẫu nhiên: {e}")
        return {}

def fetch_backgrounds(page: int = 1, page_size: int = 4) -> List[Dict]:
    try:
        resp = requests.get(f"{API_URL}/backgrounds", params={"page": page, "page_size": page_size})
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
        
        # Dropdown cho loại thiệp khi chọn "Chọn mẫu" hoặc "Ngẫu nhiên"
        card_type = "birthday"
        if mode in ["Chọn mẫu", "Ngẫu nhiên"]:
            card_type = st.selectbox(
                "Loại thiệp:",
                ["birthday", "graduation"],
                format_func=lambda x: "Sinh nhật" if x == "birthday" else "Tốt nghiệp",
                help="Chọn loại thiệp bạn muốn tạo"
            )
        
        st.divider()
        
        # Yêu cầu nội dung thiệp (bắt buộc)
        greeting_text = st.text_area(
            "Yêu cầu nội dung thiệp *",
            placeholder="VD: Thiệp chúc mừng sinh nhật cho bé gái tên Linh",
        )
        
        # Nút tạo thiệp
        generate_btn = st.button("🎨 Tạo thiệp", type="primary", use_container_width=True)

    # Xử lý logic cho từng mode
    selected_template = None
    
    # Phần giữa: Hiển thị mẫu và chức năng chọn
    with center_col:
        if mode == "Chọn mẫu":
            st.markdown("<h3 style='text-align:center;'>Mẫu thiệp</h3>", unsafe_allow_html=True)
            
            # Khởi tạo pagination
            if "templates_page" not in st.session_state:
                st.session_state.templates_page = 1
            if "templates_card_type" not in st.session_state or st.session_state.templates_card_type != card_type:
                st.session_state.templates_page = 1
                st.session_state.templates_card_type = card_type
            
            # Lấy templates
            templates = fetch_templates(card_type, st.session_state.templates_page, 4)
            
            # Hiển thị grid 1 hàng 4 cột
            cols = st.columns(4)
            has_templates = bool(templates)
            for idx in range(4):
                with cols[idx]:
                    if has_templates and idx < len(templates):
                        template = templates[idx]
                        img_url = template.get('merged_image_url', f"{API_URL}/{template['merged_image_path']}")
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

            # Pagination luôn hiển thị
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
            # Thông báo chỉ khi trang 1 và không có mẫu
            if not has_templates and st.session_state.templates_page == 1:
                st.info("Không có mẫu nào")
            
            if "selected_template" in st.session_state:
                selected_template = st.session_state.selected_template
            
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
                    img_url = template.get("merged_image_url", f"{API_URL}/{template['merged_image_path']}")
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
            # Center the file uploader
            upload_col1, upload_col2, upload_col3 = st.columns([0.2, 0.6, 0.2])
            with upload_col2:
                st.info("Chọn ảnh để upload")
                uploaded_file = st.file_uploader(
                    "Chọn ảnh foreground:",
                    type=["png", "jpg", "jpeg", "webp"],
                    help="Upload ảnh để làm foreground cho thiệp"
                )
                if uploaded_file:
                    # Upload foreground
                    files = {"file": uploaded_file}
                    try:
                        upload_resp = requests.post(f"{API_URL}/upload_foreground", files=files)
                        upload_resp.raise_for_status()
                        upload_data = upload_resp.json()
                        if "error" not in upload_data:
                            # st.success("✅ Upload thành công!")
                            # col1, col2, col3 = st.columns([0.2, 0.6, 0.2])
                            # with col2:
                            #     st.image(upload_data["foreground_url"], caption="Ảnh đã upload", width=150)
                            selected_template = {
                                "foreground_path": upload_data["foreground_path"],
                                "background_path": None,
                                "merged_image_path": None
                            }
                        else:
                            st.error(f"Lỗi upload: {upload_data['error']}")
                    except Exception as e:
                        st.error(f"Lỗi khi upload: {e}")
    
    # Xử lý tạo thiệp
    with left_col:
        if generate_btn:
            if not greeting_text:
                st.error("Vui lòng nhập yêu cầu nội dung thiệp!")
            else:
                # Lấy selected_template từ session_state nếu có (ưu tiên random_template nếu mode là Ngẫu nhiên)
                selected_template_gen = selected_template
                if mode == "Ngẫu nhiên" and "random_template" in st.session_state:
                    selected_template_gen = st.session_state.random_template
                elif mode == "Chọn mẫu" and "selected_template" in st.session_state:
                    selected_template_gen = st.session_state.selected_template
                payload = {"greeting_text_instructions": greeting_text}
                if selected_template_gen:
                    if selected_template_gen.get("background_path"):
                        payload["background_path"] = selected_template_gen["background_path"]
                    if selected_template_gen.get("foreground_path"):
                        payload["foreground_path"] = selected_template_gen["foreground_path"]
                    if selected_template_gen.get("merged_image_path"):
                        payload["merged_image_path"] = selected_template_gen["merged_image_path"]
                # Gọi API tạo thiệp
                with st.status("Đang tạo thiệp...", expanded=True):
                    try:
                        resp = requests.post(f"{API_URL}/generate-card", json=payload)
                        resp.raise_for_status()
                        result = resp.json()
                        st.session_state.generated_card = result
                        st.success("✅ Tạo thiệp thành công!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Lỗi khi tạo thiệp: {e}")
    
    with right_col:
        # Spacer to align with "Lấy mẫu ngẫu nhiên" button
        st.markdown(
            "<div style='height: 60px;'></div>",  # Adjust height as needed
            unsafe_allow_html=True
        )
        
        # Existing right_col content
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
                        f"{API_URL}/{st.session_state.selected_template['merged_image_path']}")
                img_col1, img_col2, img_col3 = st.columns([0.2, 0.6, 0.2])
                with img_col2:
                    st.image(img_url, width=200)
            elif mode == "Ngẫu nhiên" and "random_template" in st.session_state:
                st.success("Mẫu ngẫu nhiên")
                template = st.session_state.random_template
                img_url = template.get("merged_image_url", f"{API_URL}/{template['merged_image_path']}")
                img_col1, img_col2, img_col3 = st.columns([0.2, 0.6, 0.2])
                with img_col2:
                    st.image(img_url, width=200)
            elif mode == "Tải ảnh lên" and uploaded_file:
                st.success("Ảnh đã upload")
                img_col1, img_col2, img_col3 = st.columns([0.2, 0.6, 0.2])
                with img_col2:
                    # Hiển thị ảnh đã upload bằng URL trả về từ API nếu có
                    if 'upload_data' in locals() and 'foreground_url' in upload_data:
                        st.image(upload_data['foreground_url'], width=200)
                    else:
                        st.image(uploaded_file, width=200)
            else:
                if mode == "Chọn mẫu" and "selected_template" not in st.session_state:
                    st.info("Chọn mẫu để xem preview")
                elif mode == "Ngẫu nhiên" and "random_template" not in st.session_state:
                    st.info("Nhấn nút để lấy mẫu ngẫu nhiên")
                elif mode == "Tải ảnh lên" and not uploaded_file:
                    st.info("Upload ảnh để xem preview")
                else:
                    st.info("Thiệp sẽ hiển thị ở đây sau khi tạo")

if __name__ == "__main__":
    main()