import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from utils.summary_utils import generate_summary
from agents.theme_agent import *
from agents.refinement_agent import *
from agents.image_agent import *
import streamlit as st

sys.path.append("/content/drive/MyDrive/Beyond HTML Flyer Generation Project/HTML-Flyer-Generation")



def create_interface(model, api):
    # Page config
    st.set_page_config(
        page_title="HTML Flyer Generator",
        page_icon="🏞️",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Styles
    st.markdown("""
    <style>
    body { background-color: #1E1E2F; color: #FFFFFF; font-family: 'Segoe UI', sans-serif; }
    .main-title { font-size: 48px; font-weight: 800; color: #00FFC2; text-align: center; margin-bottom: 5px; }
    .main-subtitle { font-size: 18px; color: #AAAAAA; text-align: center; margin-bottom: 40px; }
    .sidebar-header { font-size: 22px; font-weight: 600; color: #00FFC2; margin-bottom: 10px; }
    .card { background-color: #2B2B3B; border-radius: 15px; padding: 25px; margin-bottom: 25px; box-shadow: 0 8px 25px rgba(0,0,0,0.5); transition: transform 0.2s; }
    .card:hover { transform: translateY(-5px); }
    .section-title { font-size: 22px; font-weight: 600; color: #00FFC2; }
    textarea { background-color: #1E1E2F !important; color: #FFFFFF !important; border: 1px solid #00FFC2 !important; border-radius: 12px !important; padding: 10px !important; }
    .stButton>button { background: linear-gradient(90deg, #00FFC2 0%, #00CFFF 100%); color: #000000; font-weight: 700; border-radius: 14px; height: 55px; font-size: 16px; }
    .tab-content { padding: 20px; }
    .centered { display: flex; flex-direction: column; align-items: center; justify-content: center; }
    </style>
    """, unsafe_allow_html=True)

    # Header
    st.markdown("<div class='main-title centered'>🏞️ HTML Flyer Generator</div>", unsafe_allow_html=True)
    st.markdown("<div class='main-subtitle centered'>AI-powered flyer creation with professional layouts</div>", unsafe_allow_html=True)

    # Session state init
    if "generate_clicked" not in st.session_state:
        st.session_state.generate_clicked = False
    if "processing_complete" not in st.session_state:
        st.session_state.processing_complete = False
    if "final_state" not in st.session_state:
        st.session_state.final_state = None

    # Layout
    col1, col2 = st.columns([1, 3])
    with col1:
        render_sidebar(model)
    with col2:
        user_prompt = render_prompt_section()
        handle_generation(user_prompt, api)
        render_results()
        render_footer()


def render_sidebar(model):
    with st.sidebar:
        st.markdown("<div class='sidebar-header'>⚙️ Settings</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='card'><b>LLM Model:</b> {model}</div>", unsafe_allow_html=True)

        st.markdown("<div class='sidebar-header'>🔖 Quick Guide</div>", unsafe_allow_html=True)
        st.markdown("""
        <div class='card'>
            <ul>
                <li>Describe the flyer concept</li>
                <li>Analyze layout & theme</li>
                <li>Generate texts, images & visual composition</li>
                <li>Preview professional output</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)


def render_prompt_section():
    st.markdown("<div class='card'><div class='section-title'>📝 Flyer Instructions</div></div>", unsafe_allow_html=True)
    user_prompt = st.text_area(
        label="Flyer Input",
        placeholder="Example: Create a premium green tea poster for Gyokuro with 'Refresh Your Soul' slogan",
        height=180,
        label_visibility="collapsed"
    )

    return user_prompt


def handle_generation(user_prompt, api_provider, ):
    st.markdown("<div class='card'><div class='section-title'>✨ Convert Instructions into Visual</div></div>", unsafe_allow_html=True)

    if st.button("🚀 Generate Flyer", type="primary", use_container_width=True):
        st.session_state.generate_clicked = True
        st.session_state.processing_complete = False
        generation_process(user_prompt, api_provider)



def generation_process(user_prompt: str, api_provider: str):
    progress_bar = st.progress(0)
    status_text = st.empty()
    image_path = None

    try:
        status_text.info("🚀 Initializing workflow...")
        progress_bar.progress(10)

        if not user_prompt or not isinstance(user_prompt, str):
            raise ValueError("Invalid user prompt: must be a non-empty string.")

        # Initialize state
        state = FlyerState(user_prompt=user_prompt.strip(), api_provider=api_provider)
        progress_bar.progress(20)

        # Run nodes manually (theme -> image -> refine)
        status_text.info("🎨 Analyzing theme...")
        state = theme_analyzer_node(state)
        progress_bar.progress(35)

        status_text.info("🖼️ Generating images...")
        state = image_generator_node(state)
        progress_bar.progress(60)

        status_text.info("🛠️ Refining HTML...")
        state = refinement_node(state)
        progress_bar.progress(70)

        # Render final HTML → display in Colab
        status_text.info("🖼️ Rendering flyer preview...")
        progress_bar.progress(85)

        # Generate flyer summary
        status_text.info("📝 Generating flyer summary...")
        state.flyer_summary = generate_summary(state.theme_json)
        progress_bar.progress(95)

        # Save to session
        st.session_state.final_state = state
        st.session_state.processing_complete = True
        st.session_state._latest_image = image_path

        progress_bar.progress(100)
        status_text.success("✅ Flyer generated successfully!")

    except Exception as e:
        err_msg = f"{type(e).__name__}: {str(e)}"
        status_text.error(f"❌ Generation failed: {err_msg}")
        progress_bar.progress(100)
        st.session_state.processing_complete = True

    finally:
        st.session_state._latest_image = image_path



def render_flyer_tab(final_state, tab):
    with tab:
        if not final_state or not getattr(final_state, "refined_html", None):
            st.info("No flyer generated yet.")
            return

        st.markdown(
            "<div class='card'><div class='section-title'>🏞️ Generated Flyer Preview</div></div>",
            unsafe_allow_html=True
        )

        # ✅ Always generate or refresh the PNG before displaying
        image_path = display_HTML2Img(final_state.refined_html, "flyer_preview.png")

        if os.path.exists(image_path):
            st.image(image_path, caption="🖼️ Generated Flyer Preview", use_container_width=True)
        else:
            st.warning("⚠️ Flyer image not available, showing HTML preview instead.")
            st.components.v1.html(final_state.refined_html, height=800, scrolling=True)

        with st.expander("🔍 View Raw HTML"):
            st.code(final_state.refined_html, language="html")


def render_summary_tab(final_state, tab):
    with tab:
        if not final_state or not getattr(final_state, "flyer_summary", None):
            st.info("No summary available.")
            return

        st.markdown(
            "<div class='card'><div class='section-title'>📈 Flyer Summary</div></div>",
            unsafe_allow_html=True
        )

        st.markdown(
            f"""
            <div style="
                background-color:rgba(255,255,255,0.08);
                padding:18px;
                border-radius:10px;
                color:#f0f0f0;
                font-size:16px;
                line-height:1.6;
                text-align:justify;">
                {final_state.flyer_summary}
            </div>
            """,
            unsafe_allow_html=True
        )

        # JSON
        with st.expander("🧩 Theme JSON"):
            st.json(final_state.theme_json)


def render_results():
    st.divider()
    st.header("📊 Results Overview")

    final_state = st.session_state.get("final_state", None)
    image_path = st.session_state.get("_latest_image", None)

    if not final_state:
        st.info("✏️ Write your flyer instructions above and click **Generate** to see the results.")
        return

    tabs = st.tabs(["🏞️ Generated Flyer", "📈 Flyer Summary"])
    render_flyer_tab(final_state, tabs[0], image_path)
    render_summary_tab(final_state, tabs[1])


def render_footer():
    st.divider()
    st.markdown(
        """
        <div style='text-align:center;color:#888;padding:15px;font-size:14px;'>
            🏞️ <b>HTML Flyer Generator</b> — Built for high-end AI Flyer Creation.<br>
            All rights reserved (Team 2) • 2025
        </div>
        """,
        unsafe_allow_html=True
    )

