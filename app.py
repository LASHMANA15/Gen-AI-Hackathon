import streamlit as st
import google.generativeai as genai
import os
import asyncio
import base64
from docx import Document
import edge_tts
from dotenv import load_dotenv

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="EchoVerse",
    page_icon="🎧",
    layout="wide",
)

# --- LOAD API KEY ---
load_dotenv()
try:
    genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
except Exception:
    st.error("Your Google AI API key is not configured. Please create a .env file or set the environment variable.")
    st.stop()


# --- STYLING AND UI SETUP ---
def get_base64_of_bin_file(bin_file):
    """ Reads a binary file and returns its base64 encoded string. """
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

def set_page_styling(png_file):
    """
    Applies custom CSS for background image and all component styling.
    """
    bin_str = get_base64_of_bin_file(png_file)
    
    custom_css = f'''
    <style>
        /* Main background image */
        .stApp {{
            background-image: url("data:image/png;base64,{bin_str}");
            background-size: cover;
            background-repeat: no-repeat;
            background-attachment: fixed;
        }}

        /* --- Main Content Containers --- */
        [data-testid="stVerticalBlock"] > [data-testid="stVerticalBlock"] > [data-testid="stVerticalBlockBorderWrapper"] > div {{
            background-color: rgba(240, 242, 246, 0.75); /* Light grey with 75% opacity */
            backdrop-filter: blur(10px);
            border: 1px solid rgba(0, 0, 0, 0.1);
            border-radius: 15px;
            padding: 2rem;
        }}

        /* --- General Text and Header Styling --- */
        h1, h2, h3, p {{
            color: #31333F; /* Dark text for readability on light containers */
        }}
        
        /* --- Input Widget Styling (Text Area, Text Input, etc.) --- */
        .stTextArea textarea, .stTextInput input, [data-testid="stFileUploader"] section {{
            background-color: rgba(255, 255, 255, 0.80) !important; /* White with 80% opacity */
            color: #000000 !important; /* Black text for input fields */
            border: 1px solid rgba(0, 0, 0, 0.2) !important;
            border-radius: 8px !important;
            backdrop-filter: blur(5px);
        }}
        ::placeholder {{
          color: #555555 !important;
          opacity: 1;
        }}

        /* --- UPDATED: Result Box Styling (Original/Rewritten Text) --- */
        /* Targets the st.info and st.success boxes specifically */
        [data-testid="stInfo"], [data-testid="stSuccess"] {{
            background-color: rgba(40, 40, 40, 0.8) !important; /* Dark semi-transparent background */
            border: 1px solid rgba(255, 255, 255, 0.2) !important;
            border-radius: 8px !important;
        }}
        /* This makes the text inside those specific boxes WHITE */
        [data-testid="stInfo"] p, [data-testid="stSuccess"] p {{
            color: #FFFFFF !important; 
        }}

        /* --- Button Styling --- */
        .stButton>button {{
            background-color: #4C8BF5;
            color: white;
            border-radius: 8px;
            border: none;
        }}

        /* --- Layout Adjustments --- */
         .st-emotion-cache-1y4p8pa {{
            padding-top: 2rem;
        }}
    </style>
    '''
    st.markdown(custom_css, unsafe_allow_html=True)


# --- CORE FUNCTIONS ---
def read_docx(file):
    try:
        doc = Document(file)
        return "\n".join([para.text for para in doc.paragraphs])
    except Exception as e:
        st.error(f"Error reading DOCX file: {e}")
        return ""

def get_rewritten_text(original_text, tone, gender, prompt_addition):
    if not original_text:
        return ""
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = (
            f"Rewrite the following text in a {tone} tone. "
            f"The narration is intended for a {gender} voice. "
            f"{prompt_addition}\n\n"
            f"Original text:\n---\n{original_text}\n---\nRewritten text:"
        )
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        st.error(f"An error occurred with the AI model: {e}")
        return ""

async def generate_audio(text, gender, output_file="narration.mp3"):
    voice_map = { "Male": "en-US-GuyNeural", "Female": "en-US-JennyNeural" }
    voice = voice_map.get(gender, "en-US-JennyNeural")
    try:
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(output_file)
        return output_file
    except Exception as e:
        st.error(f"Failed to generate audio: {e}")
        return None

# --- MAIN APP LAYOUT ---

try:
    set_page_styling('background.jpg')
except FileNotFoundError:
    st.warning("Background image 'background.jpg' not found. The app will use default styling.")

left_spacer, main_col, right_spacer = st.columns([1, 2, 1])

with main_col:
    st.title("🎧 EchoVerse")
    st.markdown("### Your AI-Powered Audiobook Creation Tool")

    if 'original_text' not in st.session_state:
        st.session_state.original_text = ""
    if 'rewritten_text' not in st.session_state:
        st.session_state.rewritten_text = ""
    if 'audio_file' not in st.session_state:
        st.session_state.audio_file = None

    with st.container(border=True):
        st.subheader("Step 1: Provide Your Text")
        tab1, tab2 = st.tabs(["✍️ Paste Text", "📂 Upload File"])
        with tab1:
            text_input = st.text_area("Paste your text here:", height=250, key="pasted_text", label_visibility="collapsed")
        with tab2:
            uploaded_file = st.file_uploader("Upload your file here:", type=["txt", "docx"], label_visibility="collapsed")

    with st.container(border=True):
        st.subheader("Step 2: Customize Your Audiobook")
        col1, col2 = st.columns(2)
        with col1:
            tone = st.selectbox("Choose a Tone", ("Neutral", "Suspenseful", "Inspiring", "Happy", "Sad", "Angry", "Formal", "Casual", "Humorous", "Mysterious"))
        with col2:
            gender = st.radio("Choose a Voice Gender", ("Female", "Male"), horizontal=True)
        prompt_addition = st.text_input("Optional: Add specific instructions for the AI", placeholder="e.g., make it sound more dramatic")

    if st.button("🚀 Generate Audiobook", use_container_width=True):
        if uploaded_file:
            if uploaded_file.type == "text/plain":
                st.session_state.original_text = uploaded_file.read().decode("utf-8")
            elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                st.session_state.original_text = read_docx(uploaded_file)
        else:
            st.session_state.original_text = text_input

        if st.session_state.original_text.strip():
            with st.spinner('EchoVerse AI is warming up... Rewriting text and tuning vocal cords...'):
                st.session_state.rewritten_text = get_rewritten_text(st.session_state.original_text, tone, gender, prompt_addition)
                if st.session_state.rewritten_text:
                    audio_path = asyncio.run(generate_audio(st.session_state.rewritten_text, gender))
                    if audio_path:
                        with open(audio_path, "rb") as audio_file:
                            st.session_state.audio_file = audio_file.read()
                        st.success("Audiobook generated successfully!")
                    else:
                        st.error("Could not generate audio. Please try again.")
                else:
                    st.error("The AI could not rewrite the text. Please check your input or try again.")
        else:
            st.warning("Please enter some text or upload a file to generate an audiobook.")

    if st.session_state.rewritten_text:
        with st.container(border=True):
            st.header("📖 Original vs. Rewritten Text")
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("Original Text")
                st.info(st.session_state.original_text)
            with col2:
                st.subheader("Rewritten Text")
                st.success(st.session_state.rewritten_text)

    if st.session_state.audio_file:
        with st.container(border=True):
            st.header("🔊 Listen to Your Audiobook")
            st.audio(st.session_state.audio_file, format="audio/mp3")
            st.download_button("📥 Download MP3", st.session_state.audio_file, "echoverse_narration.mp3", "audio/mp3", use_container_width=True)