import streamlit as st
from subpages import generalDemo, chatDemo, translatorDemo, midasChatDemo, TutorDemo, ExamCheckerDemo, FinooDemo

APP_TITLE = 'Orq.ai Chat'
st.set_page_config(APP_TITLE, page_icon="📈", layout="wide")

st.sidebar.image("assets/orq_logo.png", width=110)

# Initialize session state variables
if "file_uploaded" not in st.session_state: # Initialize the indicator of whether the file was uploaded
    st.session_state.file_uploaded = False
if "uploaded_file" not in st.session_state: # Initialize list with uploaded files
    st.session_state.uploaded_file = None
if "uploaded_image" not in st.session_state: # Initialize uploaded image
    st.session_state.uploaded_image = None
if "file_id" not in st.session_state: # Initialize list with file ids
    st.session_state.file_id = []
if "variable_dict" not in st.session_state: # Initialize variable dictionary
    st.session_state.variable_dict = {}
if "messages" not in st.session_state: # Initialize chat history
    st.session_state.messages = []
if "context_input_dict" not in st.session_state: # Initialize context dictionary
    st.session_state.context_input_dict = {}
if "key" not in st.session_state:
    st.session_state.key = None
if "token" not in st.session_state:
    st.session_state.token = None
if "current_page" not in st.session_state:
    st.session_state.current_page = "Main"
if "feedback" not in st.session_state: # Initialize the feedback value
    st.session_state.feedback = None
if "give_feedback" not in st.session_state: # Initialize the feedback state (shown/ not shown)
   st.session_state.give_feedback = False
if "feedback_widget_key" not in st.session_state: # Dynamically update the feedback widget's key for resetting
    st.session_state.feedback_widget_key = 0
if "trace_id" not in st.session_state:
    st.session_state.trace_id = 0
if "give_correction" not in st.session_state: # Initialize the correction state (shown/ not shown)
   st.session_state.give_correction = False
if "correction_widget_key" not in st.session_state: # Dynamically update the correction widget's key for resetting
    st.session_state.correction_widget_key = 0
if "correction" not in st.session_state: # Initialize the correction value
    st.session_state.correction_clicked = False



def navigate_to(page):
    if st.session_state.current_page != page:
        st.session_state.messages = []
        
    st.session_state.current_page = page

def style():
    """
    This function sets the customized CSS styles of a title, regular expander and side-menu-expander.

    Param: None
    Return: None
    """

    st.markdown(
    """
    <style>
        h1 {
            margin-bottom: 0px;
        }

        /* Expander style in the main content */
        div[data-testid="stExpander"] details summary p {
            font-size: 1rem;
            font-weight: 400;
        }
        /* Expander style in the sidebar */
        section[data-testid="stSidebar"] div[data-testid="stExpander"] details summary p {
            font-size: 1.3rem;
            font-weight: 600;
        }
        </style>
    """,
    unsafe_allow_html=True
    )

    return

# Main page content
st.title(APP_TITLE)
style()

with st.sidebar:
    useCase = st.selectbox("Chose the use case", options=["General", "Chat Deployment","Translator Deployment", "Law Tutor Chat", "Examination Checker", "Midas Chat", "Finoo Thesis Evaluator"], index=None)

    if useCase == "General":
        page = "General"
        navigate_to(page)

    if useCase == "Chat Deployment":
        page = "Chat Deployment"
        navigate_to(page)

    if useCase == "Translator Deployment":
        page = "Translator Deployment"
        navigate_to(page)

    if useCase == "Midas Chat":
        page = "Midas Chat"
        navigate_to(page)

    if useCase == "Law Tutor Chat":
        page = "Law Tutor Chat"
        navigate_to(page)

    if useCase == "Examination Checker":
        page = "Examination Checker"
        navigate_to(page)

    if useCase == "Finoo Thesis Evaluator":
        page = "FinooDemo"
        navigate_to(page)

# Dynamically render content
if st.session_state.current_page == "General":
    generalDemo.show()
elif st.session_state.current_page == "Chat Deployment":
    st.session_state.key = "ChatDemo"
    chatDemo.show()
elif st.session_state.current_page == "Translator Deployment":
    st.session_state.key = "translator-streamlit-demo"
    translatorDemo.show()
elif st.session_state.current_page == "Midas Chat":
    st.session_state.key = "chatbot_example"
    midasChatDemo.show()
elif st.session_state.current_page == "Law Tutor Chat":
    st.session_state.key = "law-tutor"
    TutorDemo.show()
elif st.session_state.current_page == "Examination Checker":
    st.session_state.key = "automatic_examination_check"
    ExamCheckerDemo.show()
elif st.session_state.current_page == "FinooDemo":
    st.session_state.key = "cormick"
    FinooDemo.show()