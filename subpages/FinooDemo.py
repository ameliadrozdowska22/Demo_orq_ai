import streamlit as st
from utils import generate_response, convert, get_deployments, set_feedback, post_correction
import json
from orq_ai_sdk.models import APIError
from streamlit import _bottom


def clear_history(reset_col):
    if reset_col.button("Reset Chat", key="reset_button"):
        st.session_state.messages = []  # Clear the chat history immediately
        st.rerun()  # Force the app to rerun


def upload_file():
    """
    This function takes the uploaded file from the session, creates, and adds a list with its ID to the session (ID is later used for the deployment invoke).
    
    Param: None
    Return: None
    """
    file_uploaded_bool = st.session_state.file_uploaded
    uploaded_file = st.session_state.uploaded_file
    file_id = st.session_state.file_id

    if file_uploaded_bool:
        file_id = [convert(uploaded_file, st.session_state.get("token"))]

    st.session_state.file_id = file_id

    return


def context_section():
    """
    This function creates a section with text fields representing keys and values in the context dictionary.
    It creates the context dictionary based on user inputs and adds it to the session.
    It creates buttons that show or hide context rows.
    """
    st.markdown("<p style='font-weight: normal; font-size: 14px;'>Assessment criteria</p>", unsafe_allow_html=True)

    context_input_dict = st.session_state.context_input_dict

    context_value_input = st.selectbox(
        "Assessment criteria number", 
        options=["all"] + [str(i) for i in range(1, 24)],
        label_visibility="collapsed",
        disabled=False,
        placeholder="all",
        key=f"context_value"
    )

    # adding a user context inputs to the session
    if context_value_input:
        context_input_dict["beoordelingscriteria"] = context_value_input

        st.session_state.context_input_dict = context_input_dict
        
    return


def add_correction():

    api_token = st.session_state.get("token")
    trace_id = st.session_state.get("trace_id")
    correction_clicked = st.session_state.get("correction_clicked")


    if correction_clicked:
        # Use form to capture user input on Enter or Submit
        with st.form(key=f"correction_form-{st.session_state.correction_widget_key}"):
            user_correction = st.text_area(
                label="Enter your correction",
                height=None,
                max_chars=None,
                key=f"correction-{st.session_state.correction_widget_key}",
                placeholder="Enter your correction here...",
                label_visibility="collapsed"
            )

            # Submit button inside form
            submitted = st.form_submit_button("Submit Correction")

            if submitted and user_correction:
                print(user_correction)
                post_correction(user_correction, api_token, trace_id)

                # Reset input field after submission
                st.session_state.correction_widget_key += 1

    return


def display_feedback():

    api_token = st.session_state.get("token")
    trace_id = st.session_state.get("trace_id")
    feedback = st.session_state.get("feedback")

    if feedback is not None:
        if int(feedback) == 0:
            set_feedback("bad", api_token, trace_id)

        elif int(feedback) == 1:
            set_feedback("good", api_token, trace_id)

        st.session_state.feedback = None

    return

def manage_chat_history(chat_input, image):

    image_message = None

    # Add the user message to the chat history
    text_message = {
        "role": "user",
        "content": [{"type": "text", "text": chat_input}]
    }
    st.session_state.messages.append(text_message)

    # Append the uploaded image as a separate message
    if image:
        image_message = {
            "role": "user",
            "content": [{"type": "image_url", "image_url": { "url": image}}]
        }
        del st.session_state["uploaded_image"]
    
    # limit the number of past messages given to the model for a reference
    conv_memory = []
    messages = st.session_state.messages

    history_num = 20 # number of maximum past messages given to the model !! CUSTOMIZE IF NEEDED !!
    if history_num < len(messages):
        slicer = len(conv_memory) - history_num
        conv_memory = messages[slicer:]
    else:
        conv_memory = messages

    if image_message:
        conv_memory.append(image_message)

    return conv_memory


def chat_messages_layout(chat_input):

    token = st.session_state.token
    key = st.session_state.key
    context = st.session_state.context_input_dict
    variable_dict = st.session_state.variable_dict
    image = st.session_state.uploaded_image
            
    if st.session_state.file_uploaded:
        upload_file()

    file_id = st.session_state.file_id

    # display the user text message
    with st.chat_message("user"):
        st.markdown(chat_input)

    # display the response and a source from a model
    with st.chat_message("assistant"):
        try:
            conv_memory = manage_chat_history(chat_input, image)
            # response = None
            response, sources, trace_id = generate_response(variable_dict, token, key, context, file_id, conv_memory)

            st.markdown(response)

            # reset the feedback state
            st.session_state.give_feedback = True
            st.session_state.feedback_widget_key += 1
            st.session_state.feedback = None
            st.session_state.trace_id = trace_id

            # reset the correction state
            st.session_state.give_correction = True
            st.session_state.correction_widget_key += 1

            # Append the model response in the message history
            st.session_state.messages.append({
                "role": "assistant",
                "content": [{"type": "text", "text": response}]
            })

        except APIError as e:
            error_dict = json.loads(e.body)
            st.info(error_dict["error"])
            # pass

        except Exception as e:
            print(e)
            # pass

    return


def chat_manager(chat_input):
    """
    Displays the chat history Manages
    """
    token = st.session_state.token
    key = st.session_state.key

    # Display chat messages from history on app rerun
    for message in st.session_state.messages:
        # Check if the message content has a type of 'text'
        for content in message["content"]:
                if content["type"] == "text":
                    with st.chat_message(message["role"]):
                        st.markdown(content["text"])

    try:
        # check if the token and key were given to procede with the invoke
        if token and key and chat_input:
            chat_messages_layout(chat_input)

    except Exception as e:
        print(e)
        # pass

    if st.session_state.give_feedback and st.session_state.give_correction:
        correction_col, feedback_col, empty_col = st.columns([2, 1, 12]) 
        
        # Create pills for adding correction
        correction_clicked = correction_col.pills(
            label="Add correction",
            key=f"correction_button-{st.session_state.correction_widget_key}",
            options="Add correction",
            selection_mode="single",
            default=None,
            label_visibility="collapsed"
        )

        feedback_selected = feedback_col.feedback("thumbs", key=f"feedback-{st.session_state.feedback_widget_key}")

        if feedback_selected is not None: 
            st.session_state.feedback = str(feedback_selected)

        if correction_clicked == "Add correction": 
            st.session_state.correction_clicked = True

    return 


def chat_input_layout():
    """
    Manages the chat input section
    """
    chat_col, reset_col = st._bottom.columns([7, 1])

    chat_input = chat_col.chat_input("Your question")

    clear_history(reset_col)
    
    chat_manager(chat_input)
    
    return


def upload_file_section():
    """
    Shows the file uploader.
    Updates the file in the session when changed.
    """
    # display the file uploader
    uploaded_file = st.file_uploader("Upload the thesis", type=["pdf", "txt", "docx", "csv", "xls"], accept_multiple_files=False)

    # update the uploaded file in the session
    if st.session_state.uploaded_file != uploaded_file:
        st.session_state.uploaded_file = uploaded_file
    
    if uploaded_file:
        st.session_state.file_uploaded = True # indicates that the new file was uploaded

    return


def additional_parameters_layout():
    """
    Initializes all components of an additional parameters menu.
    """
    with st.sidebar.expander(label="Set additional parameters", expanded=True):
        # display the upload file feature
        upload_file_section()
            
        # display the context section
        context_section()

    return


def take_token():
    """
    Shows the textfield for the API token.
    Saves the token in the session when given.
    """
    with st.sidebar.expander(label="Set parameters", expanded=True):

        # create a text field for a user access Token
        with st.form("parameters", border=False):

            token_input = st.text_input(
                "Access token",
                label_visibility="visible",
                disabled=False,
                placeholder="Access token")
                
            set_button = st.form_submit_button("Set parameters")

    if set_button:
        st.session_state["token"] = token_input

    return


def sidebar_layout():
    """
    Manages the sidebar.
    """
    # get the kay and the token
    take_token()
    key_input = st.session_state.key
    token_input =  st.session_state.token

    # get the list of variables of a chosen deployment
    try:
        if key_input and token_input:

                # if the key and the token are given, initialize the additioanal parameters layout and the chat layout
                additional_parameters_layout()
                chat_input_layout()
    except:
        pass

    return


def show():
    """
    Initializes the flow of the page.
    """
    sidebar_layout()

    # when the feedback and correction buttons are shown it runs their scripts to react to a change
    if st.session_state.give_feedback and st.session_state.give_correction:
        display_feedback()
        add_correction()