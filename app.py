import streamlit as st
import requests
from typing import List, Dict

API_URL = "http://localhost:8000"

st.set_page_config(page_title="Birthday Card Generator", layout="wide")

def fetch_templates(card_type: str = "birthday") -> List[Dict]:
    try:
        resp = requests.get(f"{API_URL}/templates/{card_type}", params={"page": 1, "page_size": 8})
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

def fetch_backgrounds(n=8) -> List[Dict]:
    try:
        resp = requests.get(f"{API_URL}/backgrounds", params={"n": n})
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        st.error(f"Lỗi khi lấy background: {e}")
        return []

def main():
    # Căn giữa tiêu đề và đổi màu sky blue
    st.markdown(
        "<h1 style='text-align: center; color: #87CEEB;'>🎂 Tạo Thiệp Sinh Nhật</h1>", 
        unsafe_allow_html=True
    )
    
    # Tạo layout 3 cột: form (sát trái), mẫu (giữa), kết quả (phải)
    info_col, template_col, result_col = st.columns([0.6, 1.4, 1])
    
    with info_col:
        st.subheader("Thông tin thiệp")
        
        # Sử dụng tỉ lệ cố định 3:4
        aspect_ratio_val = 3/4

        mode = st.radio(
            "Chọn cách lấy mẫu:",
            ["Tải ảnh lên", "Chọn mẫu", "Ngẫu nhiên"],
            horizontal=False,
        )

        # Thêm dropdown cho loại thiệp khi chọn "Chọn mẫu" hoặc "Ngẫu nhiên"
        card_type = "birthday"  # Default value
        if mode in ["Chọn mẫu", "Ngẫu nhiên"]:
            card_type = st.selectbox(
                "Loại thiệp:",
                ["birthday", "graduation"],
                format_func=lambda x: "Sinh nhật" if x == "birthday" else "Tốt nghiệp",
                help="Chọn loại thiệp bạn muốn tạo"
            )

        # Nút và controls tương ứng với mode
        uploaded_foreground = None
        if mode == "Tải ảnh lên":
            uploaded_foreground = st.file_uploader(
                label="Chọn mẫu", 
                accept_multiple_files=False, 
                type=["png", "jpg", "jpeg", "webp"],
                help="Ảnh sẽ được tự động làm mờ viền để hòa tan với background"
            )
            
            # Nút làm mới background (giống như nút làm mới mẫu)
            if uploaded_foreground:
                if st.button("Làm mới background", key="refresh_bg_upload"):
                    if "upload_backgrounds" in st.session_state:
                        del st.session_state["upload_backgrounds"]
                    if "selected_upload_background" in st.session_state:
                        del st.session_state["selected_upload_background"]
        elif mode == "Chọn mẫu":
            if st.button("Làm mới mẫu"):
                st.session_state["templates"] = fetch_templates(card_type)
                st.session_state["template_card_type"] = card_type
                if "selected_template" in st.session_state:
                    del st.session_state["selected_template"]
        elif mode == "Ngẫu nhiên":
            if st.button("Chọn mẫu ngẫu nhiên") or "random_template" not in st.session_state or st.session_state.get("random_card_type") != card_type:
                random_template = fetch_random_template(card_type)
                st.session_state["random_template"] = random_template
                st.session_state["random_card_type"] = card_type

        st.divider()  # Thêm đường phân cách

        # Form yêu cầu nội dung thiệp
        greeting_text_instructions = st.text_area(
            "Yêu cầu nội dung thiệp", 
            placeholder="VD: Thiệp chúc mừng sinh nhật cho bé gái tên Linh, 8 tuổi, thích màu hồng và Hello Kitty",
            help="Mô tả chi tiết về người nhận và yêu cầu cho thiệp sinh nhật"
        )

    # Xử lý chọn template
    selected_template = None
    merged_preview_url = None
    templates = []
    selected_background = st.session_state.get("selected_upload_background", None)

    if mode == "Tải ảnh lên" and uploaded_foreground:
        # Chỉ merge khi đã chọn background
        if selected_background:
            files = {"file": uploaded_foreground}
            params = {
                "merge_aspect_ratio": 3/4,
                "background_path": selected_background["path"],
                # Gradient parameters từ AgentState default values
                "gradient_region": 400,
                "gradient_smoothness": 0.6,
                "gradient_top": False,
                "gradient_bottom": True,
                "gradient_left": False,
                "gradient_right": False
            }
                
            merge_resp = requests.post(f"{API_URL}/upload-template", files=files, params=params)
            merge_resp.raise_for_status()
            merge_data = merge_resp.json()
            merged_preview_url = merge_data.get("merged_image_path")
            if merged_preview_url:
                merged_preview_url = f"{API_URL}/{merged_preview_url}"
            
            selected_template = {
                "background_path": merge_data["background_path"],
                "foreground_path": merge_data["foreground_path"],
                "merged_image_path": merge_data["merged_image_path"],
                "aspect_ratio": merge_data["aspect_ratio"],
                "merge_position": merge_data["merge_position"],
                "merge_margin_ratio": merge_data["merge_margin_ratio"],
                "merge_foreground_ratio": merge_data["merge_foreground_ratio"],
            }
        else:
            # Chưa chọn background, set selected_template = None
            selected_template = None

    elif mode == "Chọn mẫu":
        if "templates" not in st.session_state or st.session_state.get("template_card_type") != card_type:
            st.session_state["templates"] = fetch_templates(card_type)
            st.session_state["template_card_type"] = card_type
            # Reset selected template when card type changes
            if "selected_template" in st.session_state:
                del st.session_state["selected_template"]
        templates = st.session_state["templates"][:8] if st.session_state["templates"] else []
        selected_template = st.session_state.get("selected_template", None)

    elif mode == "Ngẫu nhiên":
        selected_template = st.session_state.get("random_template")

    # Nút tạo thiệp ở cột trái
    with info_col:
        submitted = st.button("🎨 Tạo thiệp", type="primary", use_container_width=True)

        if submitted:
            if not greeting_text_instructions:
                st.warning("Vui lòng nhập yêu cầu nội dung thiệp.")
                st.stop()
                
            if mode == "Tải ảnh lên" and not uploaded_foreground:
                st.warning("Vui lòng upload ảnh mặt trước.")
                st.stop()
            elif mode == "Tải ảnh lên" and uploaded_foreground and not selected_background:
                st.warning("Vui lòng chọn ảnh nền.")
                st.stop()
            elif mode == "Chọn mẫu" and "selected_template" not in st.session_state:
                st.warning("Vui lòng chọn một mẫu.")
                st.stop()
            elif mode == "Ngẫu nhiên" and "random_template" not in st.session_state:
                st.warning("Vui lòng chọn mẫu ngẫu nhiên.")
                st.stop()

            payload = {
                "aspect_ratio": 3/4,
                "greeting_text_instructions": greeting_text_instructions or None,
                "card_type": card_type,  # Truyền loại thiệp đã chọn
            }
            if selected_template:
                payload.update({
                    "background_path": selected_template["background_path"],
                    "foreground_path": selected_template["foreground_path"],
                    "merged_image_path": selected_template["merged_image_path"],
                    "aspect_ratio": selected_template["aspect_ratio"],
                    "merge_position": selected_template["merge_position"],
                    "merge_margin_ratio": selected_template["merge_margin_ratio"],
                    "merge_foreground_ratio": selected_template["merge_foreground_ratio"],
                })

            with st.status("Đang tạo thiệp, vui lòng chờ...", expanded=True):
                try:
                    resp = requests.post(f"{API_URL}/generate-card", json=payload)
                    resp.raise_for_status()
                    state = resp.json()
                    st.session_state["card_state"] = state
                except Exception as e:
                    st.error("Lỗi khi tạo thiệp")
                    st.stop()

    # Hiển thị các mẫu ở cột giữa
    with template_col:
        # Hiển thị preview từ upload
        if mode == "Tải ảnh lên":
            if uploaded_foreground:
                # Lấy danh sách background (4 thay vì 8)
                if "upload_backgrounds" not in st.session_state:
                    st.session_state["upload_backgrounds"] = fetch_backgrounds(4)
                
                upload_backgrounds = st.session_state["upload_backgrounds"]
                
                # Preview section - hiển thị trước danh sách background
                if selected_background and merged_preview_url:
                    st.subheader("Xem trước mẫu")
                    st.image(merged_preview_url, caption="Ảnh ghép hoàn thành", width=300)
                    st.divider()
                elif selected_background and not merged_preview_url:
                    st.info("Đang xử lý ảnh ghép...")
                elif not selected_background:
                    st.info("👇 Vui lòng chọn ảnh nền bên dưới để xem trước")
                
                # Phần chọn background
                st.subheader("Chọn ảnh nền")
                
                if upload_backgrounds:
                    # Grid backgrounds với 4 cột (hiển thị 4 backgrounds)
                    bg_cols = st.columns(4)
                    for idx, bg in enumerate(upload_backgrounds):
                        col = bg_cols[idx % 4]
                        with col:
                            st.image(bg['url'], width=120, caption=f"BG {idx+1}")
                            if st.button("Chọn", key=f"select_bg_upload_{idx}", use_container_width=True):
                                st.session_state["selected_upload_background"] = bg
                                st.rerun()
            else:
                st.info("Vui lòng tải lên ảnh mặt trước ở cột bên trái")
        
        # Hiển thị các mẫu để chọn
        elif mode == "Chọn mẫu" and templates:
            st.subheader("Chọn mẫu thiệp")
            # Hiển thị template đã chọn nếu có
            if selected_template:
                st.info("✅ Đã chọn mẫu")
                img_url = selected_template.get('merged_image_url', f"{API_URL}/{selected_template['merged_image_path']}")
                st.image(img_url, caption="Mẫu đã chọn", width=200)
            
            # Grid các mẫu với 4 cột
            cols = st.columns(4)
            for idx, template in enumerate(templates):
                col = cols[idx % 4]
                with col:
                    img_url = template.get('merged_image_url', f"{API_URL}/{template['merged_image_path']}")
                    st.image(img_url, width=120, caption=f"Mẫu {idx+1}")
                    if st.button("Chọn", key=f"select_{idx}", use_container_width=True):
                        st.session_state["selected_template"] = template
                        st.rerun()

        # Hiển thị mẫu ngẫu nhiên
        elif mode == "Ngẫu nhiên" and selected_template:
            st.subheader("Mẫu ngẫu nhiên")
            img_url = selected_template.get("merged_image_url")
            if not img_url:
                img_url = f"{API_URL}/{selected_template['merged_image_path']}"
            st.image(img_url, width=300, caption="Mẫu ngẫu nhiên")

    # Hiển thị kết quả thiệp ở cột phải (giữa màn hình)
    with result_col:
        # Hiển thị kết quả thiệp đã tạo
        if "card_state" in st.session_state:
            state = st.session_state["card_state"]
            image_url = state.get("image_url")
            if image_url:
                # Center everything including title
                col1, col2, col3 = st.columns([0.1, 0.8, 0.1])
                with col2:
                    # Căn giữa tiêu đề
                    st.markdown("<h3 style='text-align: center;'>🎉 Thiệp sinh nhật</h3>", unsafe_allow_html=True)
                    # Căn giữa ảnh thiệp
                    st.markdown(
                        f"""
                        <div style='text-align: center;'>
                            <img src='{image_url}' width='350' style='border-radius: 10px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);'/>
                            <p style='text-align: center; color: #666; margin-top: 10px; font-size: 14px;'>Thiệp sinh nhật hoàn thành</p>
                        </div>
                        """, 
                        unsafe_allow_html=True
                    )
                    # Thu nhỏ nút tải thiệp và căn giữa
                    btn_col1, btn_col2, btn_col3 = st.columns([0.25, 0.5, 0.25])
                    with btn_col2:
                        st.download_button(
                            "📥 Tải thiệp về máy",
                            data=requests.get(image_url).content,
                            file_name="thiep_sinh_nhat.png",
                            mime="image/png",
                            use_container_width=True
                        )

if __name__ == "__main__":
    main()