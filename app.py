import streamlit as st
import requests
from typing import List, Dict
from datetime import datetime, timedelta

API_URL = "http://localhost:8000"

st.set_page_config(page_title="Birthday Card Generator", layout="centered")

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
        horizontal=True,
    )

    selected_template = None
    uploaded_foreground = None
    merged_preview_url = None
    templates = []

    if mode == "Tải ảnh lên":
        uploaded_foreground = st.file_uploader(label="Chọn mẫu", accept_multiple_files=False, type=["png", "jpg", "jpeg", "webp"])
        if uploaded_foreground:
            files = {"file": uploaded_foreground}
            merge_resp = requests.post(f"{API_URL}/upload-template", files=files, params={"merge_aspect_ratio": aspect_ratio_val})
            merge_resp.raise_for_status()
            merge_data = merge_resp.json()
            merged_preview_url = merge_data.get("merged_image_path")
            if merged_preview_url:
                merged_preview_url = f"{API_URL}/{merged_preview_url}"
            st.image(merged_preview_url, caption="Xem trước (ảnh ghép)", width=240)
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
        if st.button("Làm mới mẫu"):
            st.session_state["templates"] = fetch_templates(aspect_ratio_val)
            st.session_state["templates_aspect_ratio"] = aspect_ratio_val
            if "selected_template" in st.session_state:
                del st.session_state["selected_template"]

        if "templates" not in st.session_state or st.session_state.get("templates_aspect_ratio") != aspect_ratio_val:
            st.session_state["templates"] = fetch_templates(aspect_ratio_val)
            st.session_state["templates_aspect_ratio"] = aspect_ratio_val
        templates = st.session_state["templates"][:8] if st.session_state["templates"] else []

        if templates:
            st.subheader("Chọn mẫu thiệp")
            cols = st.columns(4)
            for idx, template in enumerate(templates):
                col = cols[idx % 4]
                with col:
                    img_url = template['merged_image_url']
                    if st.button("Chọn", key=f"select_{idx}"):
                        st.session_state["selected_template"] = template
                    st.image(img_url, width=180, caption=f"Mẫu {idx+1}")
            selected_template = st.session_state.get("selected_template", None)

    elif mode == "Ngẫu nhiên":
        if st.button("Chọn mẫu ngẫu nhiên") or "random_template" not in st.session_state:
            resp = requests.get(f"{API_URL}/templates", params={"n":1, "merge_aspect_ratio": aspect_ratio_val})
            resp.raise_for_status()
            st.session_state["random_template"] = resp.json()[0]
        selected_template = st.session_state["random_template"]
        img_url = selected_template["merged_image_path"]
        img_url = f"{API_URL}/{img_url}"
        st.image(img_url, width=220, caption="Mẫu ngẫu nhiên")

    with st.form("generate_form"):
        full_name = st.text_input("Họ và tên", placeholder="Nguyễn Văn A")
        gender = st.selectbox("Giới tính", ["Nam", "Nữ"])
        today = datetime.today()
        min_date = today - timedelta(days=100*365)
        birthday = st.date_input(
            "Ngày sinh",
            min_value=min_date,
            max_value=today,
            value=today - timedelta(days=20*365),
            format="DD/MM/YYYY",
            help="Chọn ngày sinh theo định dạng ngày/tháng/năm (VD: 28/07/2000)"
        )
        greeting_text_instructions = st.text_area("Hướng dẫn sinh nội dung thiệp")
        submitted = st.form_submit_button("Tạo thiệp")

        if submitted:
            if not full_name or not gender or not birthday:
                st.warning("Vui lòng nhập đầy đủ họ tên, giới tính và ngày sinh.")
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
                "full_name": full_name,
                "gender": gender,
                "birthday": birthday.isoformat(),
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

    if "card_state" in st.session_state:
        state = st.session_state["card_state"]
        image_url = state.get("image_url")
        if image_url:
            st.image(image_url, caption="Thiệp sinh nhật", width=300)
            st.download_button(
                "Tải thiệp",
                data=requests.get(image_url).content,
                file_name="thiep_sinh_nhat.png",
            )

if __name__ == "__main__":
    main()