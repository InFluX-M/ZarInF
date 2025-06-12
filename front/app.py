import streamlit as st
import pvporcupine
import sounddevice as sd
import struct
import requests
from audio_recorder_streamlit import audio_recorder
import os

from dotenv import load_dotenv
load_dotenv()

API_BASE = "http://localhost:8000"

# -----------------------
# Initialize session state
# -----------------------
if "wake_detected" not in st.session_state:
    st.session_state.wake_detected = False

# -----------------------
# Wake word detection logic
# -----------------------
def listen_for_wake_word():
    porcupine = pvporcupine.create(
        keyword_paths=[os.getenv('KEYWORD_PATHS_WAKE_WORD')],
        access_key=os.getenv('ACCESS_KEY_WAKE_WORD')
    )
    stream = sd.RawInputStream(
        samplerate=porcupine.sample_rate,
        channels=1,
        dtype="int16",
        blocksize=porcupine.frame_length
    )
    st.info("Listening for wake word... Say 'Hey Assistant'")
    with stream:
        while True:
            audio = stream.read(porcupine.frame_length)[0]
            pcm = struct.unpack_from("h" * porcupine.frame_length, audio)
            result = porcupine.process(pcm)
            if result >= 0:
                st.session_state.wake_detected = True
                st.success("Wake word detected! You can now use the assistant.")
                break

# -----------------------
# Wake word start button
# -----------------------
st.title("🏠 Smart Home Assistant")
if st.session_state.wake_detected:
    if st.button("👋 Bye / Deactivate Assistant"):
        st.session_state.wake_detected = False
        st.rerun()

if not st.session_state.wake_detected:
    if st.button("🎤 Start Listening for Wake Word"):
        listen_for_wake_word()
        st.rerun()
    st.warning("Please say 'Hey Assistant' to unlock the assistant features.")
else:
    st.success("Assistant is active! You can use all features below.")


    # --- Show some status and button here ---
    st.subheader("Device Status Overview")

    if st.button("Refresh Status"):
        with st.spinner("Fetching statuses..."):
            res = requests.get(f"{API_BASE}/device-statuses/")
            if res.status_code == 200:
                statuses = res.json()
                st.success("Device statuses:")
                for device, status in statuses.items():
                    st.markdown(f"- **{device}**: `{status}`")
            else:
                st.error("Failed to get device statuses.")

    # -----------------------
    # Tabs become available
    # -----------------------
    tab1, tab2, tab3 = st.tabs(["💬 Text Command", "🎙️ Audio Upload", "🎤 Record Audio"])

    # --- Text Command Tab ---
    with tab1:
        st.subheader("Send Text Command")
        command_text = st.text_input("Type your command")
        response_type = st.radio("Response type", ["text", "voice"], horizontal=True)

        if st.button("Send Command"):
            if command_text.strip():
                with st.spinner("Processing..."):
                    res = requests.post(f"{API_BASE}/send-command/", json={
                        "command": command_text,
                        "response_type": response_type
                    })

                    if response_type == "voice":
                        if res.status_code == 200:
                            st.success("Audio response received:")
                            st.audio(res.content, format="audio/mpeg")
                        else:
                            st.error("Failed to get voice response.")
                    else:
                        result = res.json()
                        st.success("Response:")
                        st.write(result.get("response", "No response"))

    # --- Audio Upload Tab ---
    with tab2:
        st.subheader("Upload Audio Command")
        audio_file = st.file_uploader("Upload a voice command", type=["wav", "mp3", "m4a"])
        response_type_audio = st.radio("Response type", ["text", "voice"], horizontal=True, key="audio_radio")

        if audio_file and st.button("Submit Audio"):
            with st.spinner("Uploading and processing audio..."):
                files = {"file": (audio_file.name, audio_file, "audio/mpeg")}
                params = {"response_type": response_type_audio}
                res = requests.post(f"{API_BASE}/upload-audio/", files=files, params=params)

                if response_type_audio == "voice":
                    if res.status_code == 200:
                        st.success("Audio response received:")
                        st.audio(res.content, format="audio/mpeg")
                    else:
                        st.error("Failed to get voice response.")
                else:
                    result = res.json()
                    st.success("Response:")
                    st.write(result.get("response", "No response"))

    with tab3:
        st.subheader("Record Your Command")
        st.write("Click the button below and speak your command. Recording will stop automatically after pause.")

        # Response type selector like other tabs
        response_type_record = st.radio("Response type", ["text", "voice"], horizontal=True, key="record_audio_radio")

        # Record audio in wav format (default)
        audio_bytes = audio_recorder(pause_threshold=2.0, sample_rate=41000)  # your preferred params

        if audio_bytes:
            st.audio(audio_bytes, format="audio/wav")
            if st.button("Submit Recorded Audio"):
                with st.spinner("Uploading and processing recorded audio..."):
                    files = {
                        "file": ("recorded_command.wav", audio_bytes, "audio/wav")
                    }
                    params = {"response_type": response_type_record}
                    res = requests.post(f"{API_BASE}/upload-audio/", files=files, params=params)

                    if res.status_code == 200:
                        if response_type_record == "voice":
                            st.success("Audio response received:")
                            st.audio(res.content, format="audio/mpeg")
                        else:
                            result = res.json()
                            st.success("Response:")
                            st.write(result.get("response", "No response"))
                    else:
                        st.error("Failed to get response from the server.")
