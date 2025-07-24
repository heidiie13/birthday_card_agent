import streamlit as st
import requests
from typing import List, Dict
from streamlit_image_select import image_select

BACKEND_URL = "http://localhost:8030"

st.set_page_config(page_title="Birthday Card Generator", layout="centered")


@st.cache_data(show_spinner=False)
def fetch_samples() -> List[Dict]:
    try:
        resp = requests.get(f"{BACKEND_URL}/samples?n=8")
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        st.error(f"Failed to fetch samples: {e}")
        return []

def main():
    st.title("🎂 Birthday Card Generator")

    # Template selection mode
    mode = st.radio(
        "Select template mode:",
        ["Upload Foreground", "Choose from Samples", "Random"],
        horizontal=True,
    )

    import uuid
    selected_sample = None
    uploaded_foreground = None
    merged_preview_url = None
    samples = []
    thread_id = st.session_state.get("thread_id")
    if not thread_id:
        thread_id = str(uuid.uuid4())
        st.session_state["thread_id"] = thread_id

    if mode == "Upload Foreground":
        uploaded_foreground = st.file_uploader("Upload foreground image (PNG/JPG)", type=["png", "jpg", "jpeg"])
        if uploaded_foreground:
            files = {"file": uploaded_foreground}
            merge_resp = requests.post(f"{BACKEND_URL}/merge", files=files)
            merge_resp.raise_for_status()
            merge_data = merge_resp.json()
            merged_preview_url = merge_data.get("merged_image_path")
            # merged_preview_url là path local, cần chuyển thành URL
            if merged_preview_url:
                merged_preview_url = f"{BACKEND_URL}/{merged_preview_url}"
            st.image(merged_preview_url, caption="Preview (merged)", width=240)
            selected_sample = {
                "background_path": merge_data["background_path"],
                "foreground_path": merge_data["foreground_path"],
                "merged_image_path": merge_data["merged_image_path"],
            }

    elif mode == "Choose from Samples":
        if "samples" not in st.session_state:
            st.session_state["samples"] = fetch_samples()
        samples = st.session_state["samples"][:8] if st.session_state["samples"] else []

        # Display 8 sample images in a grid with fixed thumbnail size
        selected_idx = None
        if samples:
            st.subheader("Choose a card template (click an image)")
            cols = st.columns(4)
            for idx, sample in enumerate(samples):
                col = cols[idx % 4]
                with col:
                    img_url = f"{BACKEND_URL}/{sample['merged_image_path']}"
                    if st.button("Select", key=f"select_{idx}"):
                        st.session_state["selected_sample"] = idx
                        selected_idx = idx
                    st.image(img_url, width=180, caption=f"Sample {idx+1}")
            # Default to previously selected or first
            if selected_idx is None:
                selected_idx = st.session_state.get("selected_sample", 0)
        else:
            selected_idx = None

    elif mode == "Random":
        if st.button("Pick Random Template") or "random_sample" not in st.session_state:
            resp = requests.get(f"{BACKEND_URL}/samples?n=1")
            resp.raise_for_status()
            st.session_state["random_sample"] = resp.json()[0]
        selected_sample = st.session_state["random_sample"]
        img_url = selected_sample["merged_image_path"]
        img_url = f"{BACKEND_URL}/{img_url}"
        st.image(img_url, width=220, caption="Random Template")

    with st.form("generate_form"):
        full_name = st.text_input("Full Name", placeholder="John Doe")
        gender = st.selectbox("Gender", ["male", "female", "other"])
        birthday = st.date_input("Birthday")
        style = st.text_input("Style (e.g. poem, humorous, formal...)")
        recipient = st.text_input("Recipient (e.g. friend, mom...)")
        submitted = st.form_submit_button("Generate Card")

    if submitted:
        if not full_name or not gender or not birthday:
            st.warning("Please enter full name, gender, and birthday.")
            st.stop()

        payload = {
            "full_name": full_name,
            "gender": gender,
            "birthday": birthday.isoformat(),
            "style": style or None,
            "recipient": recipient or None,
            "thread_id": thread_id,
        }
        if selected_sample:
            payload.update({
                "background_path": selected_sample["background_path"],
                "foreground_path": selected_sample["foreground_path"],
                "merged_image_path": selected_sample["merged_image_path"],
            })
        with st.status("Generating card, please wait...", expanded=False):
            try:
                resp = requests.post(f"{BACKEND_URL}/generate", json=payload)
                resp.raise_for_status()
                state = resp.json()
                st.session_state["card_state"] = state
            except Exception as e:
                st.error(f"Error generating card: {e}")
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
        st.markdown("### Feedback (to edit card)")
        feedback_txt = st.text_area("Enter feedback (e.g. change text, background, ...)")
        if st.button("Send Feedback") and feedback_txt:
            feedback_payload = {
                "thread_id": thread_id,
                "feedback": feedback_txt,
                "background_path": state.get("background_path"),
                "foreground_path": state.get("foreground_path"),
                "merged_image_path": state.get("merged_image_path"),
            }
            with st.status("Processing feedback..."):
                try:
                    resp = requests.post(f"{BACKEND_URL}/feedback", json=feedback_payload)
                    resp.raise_for_status()
                    st.session_state["card_state"] = resp.json()
                    st.success("Card updated!")
                except Exception as e:
                    st.error(f"Error processing feedback: {e}")

if __name__ == "__main__":
    main()
