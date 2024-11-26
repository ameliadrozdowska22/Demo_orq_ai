import streamlit as st
from utils import generate_response, get_variables, convert, get_deployments
import time
import base64
from typing import Optional
from orq_ai_sdk import OrqAI    
from orq_ai_sdk.exceptions import OrqAIException
from streamlit import _bottom
import base64

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
    
    chat_input = st.chat_input("Source text")

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
                    response, sources = generate_response(variable_dict = variable_dict, api_token = token, key_input = key , context_input = context, file_id = None, conv_memory= conv_memory)

                    st.markdown(response)

                    # Append the model response in the message history
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": [{"type": "text", "text": response}]
                    })

                except Exception as e:
                    print(e)
                    # pass

        else:
            st.info('Please provide all the necessary parameters')

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

            except OrqAIException:
                st.info('Please verify if this token has an access to "orquesta-demos" workspace')
    
    if variables:
        chat_layout(variables) 
