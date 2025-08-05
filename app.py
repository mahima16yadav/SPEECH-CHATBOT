import streamlit as st
import google.generativeai as genai
from voice import record_voice

st.set_page_config(page_title="🎙️ Voice Bot", layout="wide")
st.title("🎙️ Speech Bot")
st.sidebar.title("`Speak with LLMs` \n`in any language`")


def language_selector():
    lang_options = ["ar", "de", "en", "es", "fr",
                    "it", "ja", "nl", "pl", "pt", "ru", "zh"]
    with st.sidebar:
        return st.selectbox("Speech Language", ["en"] + lang_options)


def print_txt(text):
    if any("\u0600" <= c <= "\u06FF" for c in text):  # check if text contains Arabic characters
        text = f"<p style='direction: rtl; text-align: right;'>{text}</p>"
    st.markdown(text, unsafe_allow_html=True)


def print_chat_message(message):
    text = message["content"]
    if message["role"] == "user":
        with st.chat_message("user", avatar="🎙️"):
            print_txt(text)
    else:
        with st.chat_message("assistant", avatar="🦙"):
            print_txt(text)


def main():
    with st.sidebar:
        question = record_voice(language=language_selector())

    try:
        api_key = st.secrets["GEMINI_API_KEY"]
    except KeyError:
        st.error("Please add your Gemini API key to the Streamlit secrets.")
        st.info(
            "You can add it to your secrets.toml file or directly in the Streamlit Community Cloud settings.")
        st.stop()

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')

    # init chat history
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    chat_history = st.session_state.chat_history
    # print conversation history
    for message in chat_history:
        print_chat_message(message)

    if question:
        user_message = {"role": "user", "content": question}
        print_chat_message(user_message)
        chat_history.append(user_message)

        # Convert chat history to the format expected by the Gemini API
        gemini_history = [{"role": "user" if msg["role"] == "user" else "model", "parts": [
            msg["content"]]} for msg in chat_history]

        # Remove the last message from the history to send to the model
        gemini_history.pop()

        chat_session = model.start_chat(history=gemini_history)
        response = chat_session.send_message(question)
        answer = response.text

        ai_message = {"role": "assistant", "content": answer}
        print_chat_message(ai_message)
        chat_history.append(ai_message)

        # truncate chat history to keep 20 messages max
        if len(chat_history) > 20:
            chat_history = chat_history[-20:]

        # update chat history
        st.session_state.chat_history = chat_history


if __name__ == "__main__":
    main()
