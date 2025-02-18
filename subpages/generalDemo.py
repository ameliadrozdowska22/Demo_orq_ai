import streamlit as st
from utils import generate_response, get_variables, convert, get_deployments, set_feedback, post_correction
import time
import json
import base64
from typing import Optional
from orq_ai_sdk.models import APIError
from streamlit import _bottom
import base64


def clear_history(reset_col):
    if reset_col.button("Reset Chat", key="reset_button"):
        st.session_state.messages = []  # Clear the chat history immediately
        st.rerun()  # Force the app to rerun


def variable_textfields():
    """
    This function creates a text fields for every variable in the given deployment and places user input, from text fields,
    in the session with a corresponding key.
    
    Param: A list of variables
    Return: None
    """
    token = st.session_state.get("token")
    key = st.session_state.get("key")

    variables = list(get_variables(token, key))
    
    if len(variables)>0:
        st.markdown("<p style='font-weight: normal; font-size: 14px;'>Variables</p>", unsafe_allow_html=True)
    
    # creating a text field for every variable in the given deployment
    for index, variable in enumerate(variables):

        variable_input = st.text_input(
            "variable",
            label_visibility="collapsed",
            disabled=False,
            placeholder=f"{variable.replace("_"," ").capitalize()}",
            key=f"variable_key_{index}" # setting unique key due to streamlit rules
        )

        if variable_input:
            st.session_state.variable_dict[variable]=variable_input
        
    return


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
    
    Param: None
    Return: None
    """
    st.markdown("<p style='font-weight: normal; font-size: 14px;'>Context</p>", unsafe_allow_html=True)
    key_col, val_col, plus_col, min_col = st.columns([2, 2, 1, 1])

    context_input_dict = st.session_state.context_input_dict

    if "context_rows" not in st.session_state:
        st.session_state.context_rows = [1]  # keeping track of context rows in the session

    # creating dynamicly initialized text fields for context
    for i, unique_id in enumerate(st.session_state.context_rows):

        context_key_input = key_col.text_input(
            "context key",
            label_visibility="collapsed",
            disabled=False,
            placeholder="Context key",
            key=f"context_key_{unique_id}" # setting unique key due to streamlit rules
        )

        context_value_input = val_col.text_input(
            "context value",
            label_visibility="collapsed",
            disabled=False,
            placeholder="Context value",
            key=f"context_value_{unique_id}" # setting unique key due to streamlit rules
        )

        # adding a user context inputs to the session
        if context_key_input:
            if context_value_input == '':
                context_input_dict[context_key_input] = []
            else:
                context_input_dict[context_key_input] = context_value_input.split(",")

            st.session_state.context_input_dict = context_input_dict

        # creating "+" buttons
        with plus_col:
            if i == 0: # only for the first row
                add_button = st.button("➕", key=f"add_button_{unique_id}")
            
                if add_button:
                    if len(st.session_state.context_rows) + 1 <= 10: # setting a limit of context rows to 10
                        st.session_state.context_rows.append(len(st.session_state.context_rows) + 1) # adding a new row with a unique id
                    else:
                        pass

        # creating "-" buttons
        with min_col:
            if i == 0: # only for the first row
                hide_button = st.button("➖", key=f"hide_button_{unique_id}")

                if hide_button:
                    if len(st.session_state.context_rows) > 1:  # at least 1 row remains
                        st.session_state.context_rows.pop() # removing the last row from the page
                        last_key = list(st.session_state.context_input_dict)[-1]
                        st.session_state.context_input_dict.pop(last_key) # removing the value of the last row from the session
        
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


def image_uploader():
    """
    This function displays an image uploader, enclodes the uploaded immage with base 64 encoding, and adds it to the session in the URI format
    
    Param: None
    Return: None
    """
    # Accept a single file
    image = st.file_uploader("Upload an image", type=["PNG", "JPG", "JPEG"], label_visibility="collapsed", accept_multiple_files=False)

    if image:
        base64_string = base64.b64encode(image.read()).decode('utf-8')
        data_uri = f"data:{image.type};base64,{base64_string}"
    
        st.session_state.uploaded_image = data_uri

    return


def display_sources(sources):

    with st.expander(label= "Sources", expanded=False, icon="📖"):
                    counter = 0
                    for source in sources:
                        counter += 1
                        file_name = source["file_name"]
                        page_number = source["page_number"]
                        chunk_text = source["chunk"]
                        st.markdown(f"**{counter}. {file_name} - page {int(page_number)}:**")
                        st.markdown(chunk_text) 
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

            if sources:
                display_sources(sources)

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

    with _bottom.expander("Upload image as an input"):
        image_uploader()

    clear_history(reset_col)
    
    chat_manager(chat_input)
    
    return


def upload_file_section():
    """
    Shows the file uploader.
    Updates the file in the session when changed.
    """
    # display the file uploader
    uploaded_file = st.file_uploader("Upload a file", type=["pdf", "txt", "docx", "csv", "xls"], accept_multiple_files=False)

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
        # display variable text fields
        variable_textfields()

        # display the upload file feature
        upload_file_section()
            
        # display the context section
        context_section()

    return


def take_depl_key(token_input):
    """
    Shows the dropdown with the deployment keys.
    Saves the key in the session when it's chosen.
    """
    # create a dropdown for all deployment keys
    depl_list = get_deployments(token_input)
    depl_list.sort()
    key_input = st.selectbox(
        "Deployment key",
        options= [i.replace("_", " ") for i in depl_list],
        label_visibility="visible",
        disabled=False,
        placeholder="Deployment key",
        index=None
    )

    # add a chosen deployment key to the session
    if key_input:
        key_input = key_input.replace(" ","_")
        st.session_state["key"] = key_input
    
    return


def take_key_and_token():
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

            if token_input:
                # manage deployment keys dropdown
                try:
                    take_depl_key(token_input)

                except:
                    st.info("Invalid or missing token. Please verify the token and try again.")
                
            set_button = st.form_submit_button("Set parameters")

    if set_button:
        st.session_state["token"] = token_input

    return


def sidebar_layout():
    """
    Manages the sidebar.
    """
    # get the kay and the token
    take_key_and_token()
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