import streamlit as st
import google.generativeai as genai
from voice import record_voice
from gtts import gTTS
from io import BytesIO
import base64
import re

st.set_page_config(page_title="🎙️ Voice Bot", layout="wide")
st.markdown("""
    <style>
    .block-container h1 {
        margin-top: -5rem !important;
    }
    </style>
""", unsafe_allow_html=True)
st.markdown("""
    <h1 style='text-align: center; margin-top: -5rem; color: #fff;'>🎙️ Speech Bot</h1>
""", unsafe_allow_html=True)

st.markdown("""
    <style>
    body, .stApp {
        background-color: #23272b !important;
        color: #fff !important;
    }
    /* Navbar/header area background and text color */
    header[data-testid="stHeader"] {
        background: #23272b !important;
    }
    header[data-testid="stHeader"] * {
        color: #fff !important;
    }
    .stTextInput>div>div>input,
    .stTextArea>div>textarea,
    .stTextInput>div>div>div>input {
        background-color: #23272b !important;
        color: #fff !important;
        border: 2px solid #ff8800 !important;
    }
    .stChatMessage {
        background-color: #23272b !important;
        color: #fff !important;
    }
    .stButton>button {
        color: #fff !important;
        background-color: #23272b !important;
        border: 2px solid #ff8800 !important;
    }
    </style>
""", unsafe_allow_html=True)

# st.set_page_config(page_title="🎙️ Voice Bot", layout="wide")
# st.markdown("""
#     <style>
#     .block-container h1 {
#         margin-top: -5rem !important;
#     }
#     </style>
# """, unsafe_allow_html=True)
# st.markdown("""
#     <h1 style='text-align: center; margin-top: -5rem; color: #fff;'>🎙️ Speech Bot</h1>
# """, unsafe_allow_html=True)

st.sidebar.title("`Mock Interview Bot` \n`in English/Hindi`")

def language_selector():
    with st.sidebar:
        return st.selectbox("Select Language", ["en", "hi"])

def print_txt(text):
    if any("\u0600" <= c <= "\u06FF" for c in text): 
        text = f"<p style='direction: rtl; text-align: right; color: #fff;'>{text}</p>"
    else:
        text = f"<p style='color: #fff;'>{text}</p>"
    st.markdown(text, unsafe_allow_html=True)

def play_text_as_audio(text, lang='en'):
    clean_text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
    clean_text = re.sub(r'\*(.*?)\*', r'\1', clean_text)
    clean_text = re.sub(r'_(.*?)_', r'\1', clean_text)
    clean_text = re.sub(r'`(.*?)`', r'\1', clean_text)
    clean_text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', clean_text)

    tts = gTTS(text=clean_text, lang=lang)
    audio_bytes = BytesIO()
    tts.write_to_fp(audio_bytes)
    audio_bytes.seek(0)

    audio_base64 = base64.b64encode(audio_bytes.read()).decode()
    audio_html = f"""
        <audio autoplay>
            <source src="data:audio/mp3;base64,{audio_base64}" type="audio/mp3">
        </audio>
    """
    st.markdown(audio_html, unsafe_allow_html=True)

def print_chat_message(message):
    text = message["content"]
    if message["role"] == "user":
        with st.chat_message("user"):
            print_txt(text)
    else:
        with st.chat_message("assistant"):
            print_txt(text)


def main():
    with st.sidebar:
        selected_lang = language_selector()
        question = record_voice(language=selected_lang)

    try:
        api_key = st.secrets["GEMINI_API_KEY"]
    except KeyError:
        st.error("Please add your Gemini API key to the Streamlit secrets.")
        st.info(
            "You can add it to your secrets.toml file or directly in the Streamlit Community Cloud settings.")
        st.stop()

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    chat_history = st.session_state.chat_history

    for message in chat_history:
        print_chat_message(message)

    if question:
        user_message = {"role": "user", "content": question}
        print_chat_message(user_message)
        chat_history.append(user_message)

        persona_instruction = {
            "role": "user",
            "parts": ["You are a human participating in an interview. Answer all questions thoughtfully, like a human would. Be natural, conversational, and authentic. Keep your answers concise so they can be spoken in under 30 seconds. Do not give placeholders or templates. Never say things like '[mention a skill]' or '[mention a field]'. Instead, answer as yourself with complete sentences."]
        }

        gemini_history = [persona_instruction] + [
            {"role": "user" if msg["role"] == "user" else "model", "parts": [msg["content"]]}
            for msg in chat_history
        ]

        gemini_history.pop()


        chat_session = model.start_chat(history=gemini_history)
        response = chat_session.send_message(question)
        answer = response.text

        ai_message = {"role": "assistant", "content": answer}
        print_chat_message(ai_message)
        play_text_as_audio(answer, lang=selected_lang) 
        chat_history.append(ai_message)

        if len(chat_history) > 20:
            chat_history = chat_history[-20:]

        st.session_state.chat_history = chat_history

if __name__ == "__main__":
    main()
