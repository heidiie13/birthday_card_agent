import streamlit as st
import requests
from typing import List, Dict
from streamlit_image_select import image_select

BACKEND_URL = "http://localhost:8030"

st.set_page_config(page_title="Birthday Card Generator", layout="centered")


@st.cache_data(show_spinner=False)
def fetch_samples() -> List[Dict]:
    try:
        resp = requests.get(f"{BACKEND_URL}/samples")
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        st.error(f"Failed to fetch samples: {e}")
        return []


def show_samples(samples):
    st.subheader("Chọn mẫu ảnh (tùy chọn)")
    cols = st.columns(5)
    selected_index = st.session_state.get("selected_sample", None)
    for idx, sample in enumerate(samples):
        col = cols[idx % 5]
        with col:
            st.image(
                f"{BACKEND_URL}/{sample['merged_image_path']}",
                use_container_width=True,
            )
            # Hiển thị radio để chọn
            if st.button("Chọn", key=f"choose_{idx}"):
                st.session_state["selected_sample"] = idx
                selected_index = idx
    return selected_index


def main():
    st.title("🎂 Birthday Card Generator")

    # Fetch samples once
    if "samples" not in st.session_state:
        st.session_state["samples"] = fetch_samples()

    samples = st.session_state["samples"]

    # Chọn mẫu ảnh trước (bên ngoài form)
    if samples:
        img_urls = [f"{BACKEND_URL}/{s['merged_image_path']}" for s in samples]
        captions = [f"Mẫu {i+1}" for i in range(len(samples))]
        selected_idx = image_select(
            label="Chọn mẫu thiệp (click vào ảnh)",
            images=img_urls,
            captions=captions,
            index=st.session_state.get("selected_sample", 0) if "selected_sample" in st.session_state else 0,
        )
        st.session_state["selected_sample"] = selected_idx
    else:
        selected_idx = None

    with st.form("generate_form"):
        full_name = st.text_input("Họ và tên", placeholder="Nguyễn Văn A")
        gender = st.selectbox("Giới tính", ["male", "female", "other"])
        birthday = st.date_input("Ngày sinh")
        style = st.text_input("Phong cách (ví dụ: thơ, hài hước, trang trọng...)")
        recipient = st.text_input("Người nhận (ví dụ: bạn, mẹ...)")

        submitted = st.form_submit_button("Tạo thiệp")

    if submitted:
        if not full_name or not gender or not birthday:
            st.warning("Vui lòng nhập đầy đủ họ tên, giới tính và ngày sinh")
            st.stop()

        thread_id = st.session_state.get("thread_id")
        if thread_id is None:
            import uuid

            thread_id = uuid.uuid4().hex
            st.session_state["thread_id"] = thread_id

        payload = {
            "full_name": full_name,
            "gender": gender,
            "birthday": birthday.isoformat(),
            "thread_id": thread_id,
            "style": style or None,
            "recipient": recipient or None,
        }

        if selected_idx is not None:
            sample = samples[selected_idx]
            payload.update(
                {
                    "background_path": sample["background_path"],
                    "foreground_path": sample["foreground_path"],
                    "merged_image_path": sample["merged_image_path"],
                }
            )

        with st.status("Đang tạo thiệp, vui lòng chờ...", expanded=False):
            try:
                resp = requests.post(f"{BACKEND_URL}/generate", json=payload)
                resp.raise_for_status()
                data = resp.json()
                st.session_state["current_image_url"] = data["image_url"]
                st.session_state["current_background"] = data["background_path"]
                st.session_state["current_foreground"] = data["foreground_path"]
                st.session_state["current_merged"] = data["merged_image_path"]
            except Exception as e:
                st.error(f"Lỗi tạo thiệp: {e}")
                st.stop()

    # Display generated image
    if "current_image_url" in st.session_state:
        st.image(
            st.session_state["current_image_url"], caption="Thiệp sinh nhật", use_container_width=True
        )
        st.download_button(
            "Tải ảnh",
            data=requests.get(st.session_state["current_image_url"]).content,
            file_name="birthday_card.png",
        )
        st.markdown("### Phản hồi (nếu muốn chỉnh sửa)")
        feedback_txt = st.text_area("Nhập phản hồi (ví dụ: tôi muốn đổi màu chữ sang xanh...) ")
        if st.button("Gửi phản hồi") and feedback_txt:
            thread_id = st.session_state.get("thread_id")
            if not thread_id:
                st.error("Không tìm thấy thread_id. Vui lòng tạo thiệp trước.")
            else:
                payload = {"thread_id": thread_id, "feedback": feedback_txt}
                # include paths so backend has enough context
                payload.update(
                    {
                        "background_path": st.session_state.get("current_background"),
                        "foreground_path": st.session_state.get("current_foreground"),
                        "merged_image_path": st.session_state.get("current_merged"),
                    }
                )
                with st.status("Đang xử lý phản hồi..."):
                    try:
                        resp = requests.post(f"{BACKEND_URL}/feedback", json=payload)
                        resp.raise_for_status()
                        data = resp.json()
                        st.session_state["current_image_url"] = data["image_url"]
                        # update paths in session
                        st.session_state["current_background"] = data["background_path"]
                        st.session_state["current_foreground"] = data["foreground_path"]
                        st.session_state["current_merged"] = data["merged_image_path"]
                        st.success("Thiệp đã được cập nhật!")
                    except Exception as e:
                        st.error(f"Lỗi phản hồi: {e}")


if __name__ == "__main__":
    main()
