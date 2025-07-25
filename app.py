import streamlit as st
import requests
from typing import List, Dict

API_URL = "http://localhost:8030"

st.set_page_config(page_title="Birthday Card Generator", layout="centered")


def fetch_samples(aspect_ratio_val) -> List[Dict]:
    try:
        resp = requests.get(f"{API_URL}/samples", params={"n":8, "merge_aspect_ratio": aspect_ratio_val})
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        st.error(f"Error fetching samples: {e}")
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

    selected_sample = None
    uploaded_foreground = None
    merged_preview_url = None
    samples = []

    if mode == "Tải ảnh lên":
        uploaded_foreground = st.file_uploader("Upload foreground image (PNG/JPG)", type=["png", "jpg", "jpeg", "webp"])
        if uploaded_foreground:
            files = {"file": uploaded_foreground}
            merge_resp = requests.post(f"{API_URL}/upload_sample", files=files, params={"merge_aspect_ratio": aspect_ratio_val})
            merge_resp.raise_for_status()
            merge_data = merge_resp.json()
            merged_preview_url = merge_data.get("merged_image_path")
            if merged_preview_url:
                merged_preview_url = f"{API_URL}/{merged_preview_url}"
            st.image(merged_preview_url, caption="Preview (merged)", width=240)
            selected_sample = {
                "background_path": merge_data["background_path"],
                "foreground_path": merge_data["foreground_path"],
                "merged_image_path": merge_data["merged_image_path"],
            }

    elif mode == "Chọn mẫu":
        if "samples" not in st.session_state or st.session_state.get("samples_aspect_ratio") != aspect_ratio_val:
            st.session_state["samples"] = fetch_samples(aspect_ratio_val)
            st.session_state["samples_aspect_ratio"] = aspect_ratio_val
        samples = st.session_state["samples"][:8] if st.session_state["samples"] else []

        selected_idx = None
        if samples:
            st.subheader("Chọn mẫu thiệp")
            cols = st.columns(4)
            for idx, sample in enumerate(samples):
                col = cols[idx % 4]
                with col:
                    img_url = sample['merged_image_url']
                    if st.button("Chọn", key=f"select_{idx}"):
                        st.session_state["selected_sample"] = idx
                        selected_idx = idx
                    st.image(img_url, width=180, caption=f"Mẫu {idx+1}")
            if selected_idx is None:
                selected_idx = st.session_state.get("selected_sample", 0)
        else:
            selected_idx = None

    elif mode == "Ngẫu nhiên":
        if st.button("Chọn mẫu ngẫu nhiên") or "random_sample" not in st.session_state:
            resp = requests.get(f"{API_URL}/samples", params={"n":1, "merge_aspect_ratio": aspect_ratio_val})
            resp.raise_for_status()
            st.session_state["random_sample"] = resp.json()[0]
        selected_sample = st.session_state["random_sample"]
        img_url = selected_sample["merged_image_path"]
        img_url = f"{API_URL}/{img_url}"
        st.image(img_url, width=220, caption="Random Template")

    with st.form("generate_form"):
        full_name = st.text_input("Họ và tên", placeholder="Nguyễn Văn A")
        gender = st.selectbox("Giới tính", ["Nam", "Nữ"])
        birthday = st.date_input("Ngày sinh")
        extra_req = st.text_area("Yêu cầu thêm (tuỳ chọn)")
        submitted = st.form_submit_button("Tạo thiệp")

        if submitted:
            if not full_name or not gender or not birthday:
                st.warning("Vui lòng nhập đầy đủ họ tên, giới tính và ngày sinh.")
                st.stop()

            payload = {
                "full_name": full_name,
                "gender": gender,
                "birthday": birthday.isoformat(),
                "aspect_ratio": aspect_ratio_val,
                "extra_requirements": extra_req or None,
            }
            if selected_sample:
                payload.update({
                        "background_path": selected_sample["background_path"],
                        "foreground_path": selected_sample["foreground_path"],
                        "merged_image_path": selected_sample["merged_image_path"],
                        "aspect_ratio": selected_sample["aspect_ratio"],
                        "merge_position": selected_sample["merge_position"],
                        "merge_margin_ratio": selected_sample["merge_margin_ratio"],
                        "merge_foreground_ratio": selected_sample["merge_foreground_ratio"],
                    })

            with st.status("Đang tạo thiệp, vui lòng chờ...", expanded=True):
                try:
                    resp = requests.post(f"{API_URL}/generate", json=payload)
                    resp.raise_for_status()
                    state = resp.json()
                    st.session_state["card_state"] = state
                except Exception as e:
                    st.error("Error creating card")
                    st.stop()

    # Display generated image and feedback
    if "card_state" in st.session_state:
        state = st.session_state["card_state"]
        image_url = state.get("image_url")
        if image_url:
            st.image(image_url, caption="Birthday Card", use_container_width=True)
            st.download_button(
                "Download Image",
                data=requests.get(image_url).content,
                file_name="birthday_card.png",
            )

if __name__ == "__main__":
    main()