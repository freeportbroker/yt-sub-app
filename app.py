import streamlit as st
import streamlit.components.v1 as components
from yt_sub_app import extract_video_id, get_english_subtitles
import json

st.title("Get&Copy YouTube English Subtitles")

url = st.text_input("Paste YouTube link")

col1, col2 = st.columns([1, 4])

with col1:
    get_clicked = st.button("Get subtitles", use_container_width=True)

with col2:
    copy_placeholder = st.empty()

if get_clicked:
    if not url.strip():
        st.warning("Please paste a YouTube link.")
    else:
        try:
            video_id = extract_video_id(url)
            subtitles = get_english_subtitles(video_id)

            if subtitles:
                st.session_state["subtitles"] = subtitles
            else:
                st.session_state["subtitles"] = ""
                st.error("No English subtitles found.")
        except Exception as e:
            st.session_state["subtitles"] = ""
            st.error(f"Error: {e}")

if st.session_state.get("subtitles"):
    subtitles = st.session_state["subtitles"]
    safe_subtitles = json.dumps(subtitles)

    with copy_placeholder:
        components.html(
            f"""
            <style>
                .copy-button {{
                    height: 38px;
                    padding: 0 16px;
                    border-radius: 8px;
                    border: 1px solid rgba(250, 250, 250, 0.2);
                    background-color: #0e1117;
                    color: white;
                    cursor: pointer;
                    font-size: 14px;
                    margin-top: -6px;
                }}

                .copy-button.copied {{
                    box-shadow: 0 0 14px #4ade80;
                    border-color: #4ade80;
                }}
            </style>

            <button id="copyBtn" class="copy-button">
                Copy subtitles
            </button>

            <script>
                const btn = document.getElementById("copyBtn");

                btn.onclick = function() {{
                    navigator.clipboard.writeText({safe_subtitles});
                    btn.classList.add("copied");

                    setTimeout(function() {{
                        btn.classList.remove("copied");
                    }}, 500);
                }};
            </script>
            """,
            height=45,
        )

    st.text_area("Subtitles", subtitles, height=400)