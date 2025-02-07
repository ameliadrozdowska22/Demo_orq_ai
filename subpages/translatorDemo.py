import streamlit as st
from utils import generate_response, get_variables, set_feedback, post_correction
import time
import json
import base64 
from typing import Optional
from orq_ai_sdk.models import APIError
from streamlit import _bottom
import base64

def give_feedback(api_token, trace_id, feedback_col):
    
    # Render the feedback widget with a dynamic key
    with feedback_col:
        selected = st.feedback("thumbs", key=f"feedback-{st.session_state.feedback_widget_key}")

    if selected is not None:
        st.session_state.feedback = selected
    
    feedback = st.session_state.feedback
    if feedback is not None:
        if feedback == 0:
            set_feedback("bad", api_token, trace_id)

        elif feedback == 1:
            set_feedback("good", api_token, trace_id)

    return


def add_correction(api_token, trace_id, correction_col):

    # Create pills for adding correction
    correction_selected = correction_col.pills(
        label="Add correction",
        key=f"correction_button-{st.session_state.correction_widget_key}",
        options="Add correction",
        selection_mode="single",
        default=None,
        label_visibility="collapsed"
    )

    if correction_selected:
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

def clear_history(reset_col):
    if reset_col.button("Reset Chat", key="reset_button"):
        st.session_state.messages = []  # Clear the chat history immediately
        st.rerun()  # Force the app to rerun

def variable_textfields(variables):
    """
    This function creates a text fields for every variable in the given deployment and places user input, from text fields,
    in the session with a corresponding key.
    
    Param: A list of variables
    Return: None
    """
    if len(variables)>0:
        st.markdown("<p style='font-weight: normal; font-size: 14px;'>Variables</p>", unsafe_allow_html=True)
    
    # creating a text field for every variable in the given deployment
    for index, variable in enumerate(variables):

        variable_input = st.selectbox(
            options=["English", "Dutch", "German", "French", "Spanish"],
            label="variables",
            index=None,
            label_visibility="collapsed",
            disabled=False,
            placeholder=f"{variable.replace("_"," ").capitalize()}",
            key=f"variable_key_{index}" # setting unique key due to streamlit rules
        )

        if variable_input:
            st.session_state.variable_dict[variable]=variable_input
        
    return


def chat_layout(variables):
    """
    This function manages the chat section:
    - chat message text field;
    - the message history;
    
    Param: A list of variables
    Return: None
    """

    chat_col, reset_col = st._bottom.columns([7.7, 1])

    chat_input = chat_col.chat_input("Source text")

    clear_history(reset_col)

    # Display chat messages from history on app rerun
    for message in st.session_state.messages:
        # Check if the message content has a type of 'text'
        for content in message["content"]:
                if content["type"] == "text":
                    with st.chat_message(message["role"]):
                        st.markdown(content["text"])

    # when message is send by user, update the parameters in case of a change
    if chat_input:
        token = st.session_state.get("token")
        key = st.session_state.get("key")
        variable_dict = st.session_state.variable_dict
        
    try:
        # check if the token, key and all variables were given by the user to procede with the invoke
        if token and key and chat_input and (len(variables) == len(variable_dict)):

            # display the user text message
            with st.chat_message("user"):
                st.markdown(chat_input)

            # Add the user message to the chat history
            if chat_input:
                text_message = {
                    "role": "user",
                    "content": [{"type": "text", "text": chat_input}]
                }
                st.session_state.messages.append(text_message)

            # limit the number of past messages given to the model for a reference
            conv_memory = []
            response = None
            messages = st.session_state.messages

            history_num = 20 # number of maximum past messages given to the model !! CUSTOMIZE IF NEEDED !!
            if history_num < len(messages):
                slicer = len(conv_memory) - history_num
                conv_memory = messages[slicer:]
            else:
                conv_memory = messages

            # display the response and a source from a model
            with st.chat_message("assistant"):
                context = {key: value.lower() if isinstance(value, str) else value for key, value in variable_dict.items()}
                try:
                    response, sources, trace_id = generate_response(variable_dict = variable_dict, api_token = token, key_input = key , context_input = context, file_id = None, conv_memory= conv_memory)

                    # reset the feedback state
                    st.session_state.give_feedback = True
                    st.session_state.feedback = None
                    st.session_state.feedback_widget_key += 1
                    st.session_state.trace_id = trace_id

                    # reset the correction state
                    st.session_state.give_correction = True
                    st.session_state.correction_widget_key += 1

                    st.markdown(response)

                    # Append the model response in the message history
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": [{"type": "text", "text": response}]
                    })

                except APIError as e:
                    error_dict = json.loads(e.body)
                    st.info(error_dict["error"])
                    # st.info(e)

        else:
            st.info('Please provide all the necessary parameters')

    except Exception as e:
        # print(e)
        pass

    # display feedback and correction buttons
    try:
        correction_col, feedback_col, empty_col = st.columns([2, 1, 12])
        if st.session_state.give_feedback == True:
            token = st.session_state.get("token")
            trace_id = st.session_state.get("trace_id")
            give_feedback(token, trace_id, feedback_col)

        if st.session_state.give_correction == True:
            token = st.session_state.get("token")
            trace_id = st.session_state.get("trace_id")
            add_correction(token, trace_id, correction_col)


    except Exception as e:
        print(e)
        # pass

    return


def show():
    variables = None

    with st.sidebar:

        token = st.text_input(
            "Access token",
            label_visibility="visible",
            disabled=False,
            placeholder="Access token"
        )
        
        if token:
            st.session_state["token"] = token
            key = st.session_state.get("key")

            try:
                variables = list(get_variables(token, key))
                variable_textfields(variables)

            except APIError as e:
                    print(e)
                    # st.info(e)
                    st.info('Please verify if this token has an access to "orquesta-demos" workspace')
    
    if variables:
        chat_layout(variables) 
