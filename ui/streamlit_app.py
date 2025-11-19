import sys, os
from utils.summary_utils import generate_summary
from agents.theme_agent import theme_analyzer_node
from agents.refinement_agent import refinement_node
from agents.image_agent import image_generator_node, inject_images_for_preview
from core.state import FlyerState
import streamlit as st
from core.workflow import create_workflow


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.append("/content/drive/MyDrive/Beyond HTML Flyer Generation Project/HTML-Flyer-Generation")


def create_interface(model, api):
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
    st.markdown("<div class='main-subtitle centered'>AI-powered flyer creation with professional layouts</div>",
                unsafe_allow_html=True)

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


# Sidebar
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


# Prompt input section
def render_prompt_section():
    st.markdown("<div class='card'><div class='section-title'>📝 Flyer Instructions</div></div>", unsafe_allow_html=True)
    return st.text_area(
        label="Flyer Input",
        placeholder="Example: Create a premium green tea poster for Gyokuro with 'Refresh Your Soul' slogan",
        height=180,
        label_visibility="collapsed"
    )


# Handle generate button
def handle_generation(user_prompt, api_provider):
    st.markdown("<div class='card'><div class='section-title'>✨ Convert Instructions into Visual</div></div>",
                unsafe_allow_html=True)
    if st.button("🚀 Generate Flyer", type="primary", use_container_width=True):
        st.session_state.generate_clicked = True
        st.session_state.processing_complete = False
        generation_process(user_prompt, api_provider)


# Generation workflow
def generation_process(user_prompt: str, api_provider: str):
    progress_bar = st.progress(0)
    status_text = st.empty()
    try:
        status_text.info("🚀 Initializing workflow...")
        progress_bar.progress(10)

        if not user_prompt or not isinstance(user_prompt, str):
            raise ValueError("Invalid user prompt: must be a non-empty string.")

        state = FlyerState(user_prompt=user_prompt.strip(), api_provider=api_provider)
        progress_bar.progress(20)

        status_text.info("🎨 Extracting instructions & analyzing theme...")
        state = theme_analyzer_node(state)
        progress_bar.progress(30)

        status_text.info("🖼️ Generating images...")
        state = image_generator_node(state)
        progress_bar.progress(60)

        status_text.info("🛠️ Refining the flyer...")
        state = refinement_node(state)
        progress_bar.progress(80)

        status_text.info("📝 Generating flyer summary...")
        state.flyer_summary = generate_summary(state.theme_json)
        progress_bar.progress(90)

        st.session_state.final_state = state
        st.session_state.processing_complete = True
        progress_bar.progress(100)
        status_text.success("✅ Flyer generated successfully!")

    except Exception as e:
        status_text.error(f"❌ Generation failed: {type(e).__name__}: {e}")
        progress_bar.progress(100)
        st.session_state.processing_complete = True


# Flyer tab
def render_flyer_tab(final_state: FlyerState, tab):
    with tab:
        if not final_state or not getattr(final_state, "html_final", None):
            st.info("No flyer generated yet.")
            return

        st.markdown("<div class='card'><div class='section-title'>🏞️ Generated Flyer Preview</div></div>",
                    unsafe_allow_html=True)

        original_html = inject_images_for_preview(final_state.html_final)
        refined_html = inject_images_for_preview(final_state.html_refined or final_state.html_final)

        st.markdown("### 📝 Original Flyer HTML")
        st.components.v1.html(original_html, height=800, scrolling=True)

        st.markdown("### ♻️ Refined Flyer HTML")
        st.components.v1.html(refined_html, height=800, scrolling=True)

        with st.expander("🔍 View Raw HTML"):
            st.code(final_state.html_refined or final_state.html_final, language="html")


# Summary tab
def render_summary_tab(final_state: FlyerState, tab):
    with tab:
        if not final_state or not getattr(final_state, "flyer_summary", None):
            st.info("No summary available.")
            return

        st.markdown("<div class='card'><div class='section-title'>📈 Flyer Summary</div></div>",
                    unsafe_allow_html=True)
        st.markdown(f"""
        <div style="background-color:rgba(255,255,255,0.08);
                    padding:18px;
                    border-radius:10px;
                    color:#f0f0f0;
                    font-size:16px;
                    line-height:1.6;
                    text-align:justify;">
            {final_state.flyer_summary}
        </div>
        """, unsafe_allow_html=True)

        with st.expander("🧩 Theme JSON"):
            st.json(final_state.theme_json)


# Refinement tab
def render_refinement_review_tab(final_state: FlyerState, tab):
    with tab:
        st.markdown("<div class='card'><div class='section-title'>🔍 Refinement Review</div></div>",
                    unsafe_allow_html=True)
        evaluation = getattr(final_state, "evaluation_json", {})
        if evaluation and "judgment" in evaluation:
            st.info(f"**AI Layout Critique:**\n\n{evaluation['judgment']}")
        else:
            st.warning("No refinement review data found.")


# Results overview
def render_results():
    st.divider()
    st.header("📊 Results Overview")
    final_state = st.session_state.get("final_state", None)
    if not final_state:
        st.info("✏️ Write your flyer instructions above and click **Generate** to see the results.")
        return

    tabs = st.tabs(["🏞️ Generated Flyer", "📈 Flyer Summary", "🔍 Refinement Review"])
    render_flyer_tab(final_state, tabs[0])
    render_summary_tab(final_state, tabs[1])
    render_refinement_review_tab(final_state, tabs[2])


# Footer
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
