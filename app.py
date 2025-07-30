import streamlit as st
import requests
from typing import List, Dict

API_URL = "http://localhost:8000"

st.set_page_config(page_title="Birthday Card Generator", layout="wide")

def fetch_templates(aspect_ratio_val) -> List[Dict]:
    try:
        resp = requests.get(f"{API_URL}/templates", params={"n": 8, "merge_aspect_ratio": aspect_ratio_val})
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        st.error(f"Lỗi khi lấy mẫu: {e}")
        return []

def main():
    st.title("🎂 Tạo Thiệp Sinh Nhật")
    
    # Tạo layout 3 cột: form (sát trái), mẫu (giữa), kết quả (phải)
    info_col, template_col, result_col = st.columns([0.6, 1.4, 1])
    
    with info_col:
        st.subheader("Thông tin thiệp")
        
        # Form điền thông tin
        aspect_ratio_label = st.selectbox(
            "Tỉ lệ ảnh (Rộng:Cao)",
            ["1:1", "3:4", "4:3", "9:16", "16:9"],
            index=1,
        )
        aspect_ratio_map = {"1:1": 1.0, "3:4": 3/4, "4:3": 4/3, "9:16": 9/16, "16:9": 16/9}
        aspect_ratio_val = aspect_ratio_map[aspect_ratio_label]

        mode = st.radio(
            "Chọn cách lấy mẫu:",
            ["Tải ảnh lên", "Chọn mẫu", "Ngẫu nhiên"],
            horizontal=False,
        )

        # Nút và controls tương ứng với mode
        uploaded_foreground = None
        if mode == "Tải ảnh lên":
            uploaded_foreground = st.file_uploader(label="Chọn mẫu", accept_multiple_files=False, type=["png", "jpg", "jpeg", "webp"])
        elif mode == "Chọn mẫu":
            if st.button("Làm mới mẫu"):
                st.session_state["templates"] = fetch_templates(aspect_ratio_val)
                st.session_state["templates_aspect_ratio"] = aspect_ratio_val
                if "selected_template" in st.session_state:
                    del st.session_state["selected_template"]
        elif mode == "Ngẫu nhiên":
            if st.button("Chọn mẫu ngẫu nhiên") or "random_template" not in st.session_state:
                resp = requests.get(f"{API_URL}/templates", params={"n":1, "merge_aspect_ratio": aspect_ratio_val})
                resp.raise_for_status()
                st.session_state["random_template"] = resp.json()[0]

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

    if mode == "Tải ảnh lên" and uploaded_foreground:
        files = {"file": uploaded_foreground}
        merge_resp = requests.post(f"{API_URL}/upload-template", files=files, params={"merge_aspect_ratio": aspect_ratio_val})
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

    elif mode == "Chọn mẫu":
        if "templates" not in st.session_state or st.session_state.get("templates_aspect_ratio") != aspect_ratio_val:
            st.session_state["templates"] = fetch_templates(aspect_ratio_val)
            st.session_state["templates_aspect_ratio"] = aspect_ratio_val
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
                st.warning("Vui lòng upload ảnh foreground.")
                st.stop()
            elif mode == "Chọn mẫu" and "selected_template" not in st.session_state:
                st.warning("Vui lòng chọn một mẫu.")
                st.stop()
            elif mode == "Ngẫu nhiên" and "random_template" not in st.session_state:
                st.warning("Vui lòng chọn mẫu ngẫu nhiên.")
                st.stop()

            payload = {
                "aspect_ratio": aspect_ratio_val,
                "greeting_text_instructions": greeting_text_instructions or None,
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
        if mode == "Tải ảnh lên" and merged_preview_url:
            st.subheader("Xem trước mẫu")
            st.image(merged_preview_url, caption="Ảnh ghép từ file upload", width=300)
        
        # Hiển thị các mẫu để chọn
        elif mode == "Chọn mẫu" and templates:
            st.subheader("Chọn mẫu thiệp")
            # Hiển thị template đã chọn nếu có
            if selected_template:
                st.info("✅ Đã chọn mẫu")
                st.image(selected_template.get('merged_image_url', ''), caption="Mẫu đã chọn", width=200)
            
            # Grid các mẫu với 4 cột
            cols = st.columns(4)
            for idx, template in enumerate(templates):
                col = cols[idx % 4]
                with col:
                    img_url = template['merged_image_url']
                    st.image(img_url, width=120, caption=f"Mẫu {idx+1}")
                    if st.button("Chọn", key=f"select_{idx}", use_container_width=True):
                        st.session_state["selected_template"] = template
                        st.rerun()

        # Hiển thị mẫu ngẫu nhiên
        elif mode == "Ngẫu nhiên" and selected_template:
            st.subheader("Mẫu ngẫu nhiên")
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