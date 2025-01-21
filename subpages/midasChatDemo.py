import streamlit as st
from streamlit import _bottom
import base64
from utils import generate_response, get_variables
from orq_ai_sdk.models import APIError

def clear_history(reset_col):
    if reset_col.button("Reset Chat", key="reset_button"):
        st.session_state.messages = []  # Clear the chat history immediately
        st.rerun()  # Force the app to rerun

def image_uploader():
    """
    This function displays an image uploader, enclodes the uploaded immage with base 64 encoding, and adds it to the session in the URI format
    
    Param: None
    Return: None
    """
    image = st.file_uploader("Upload an image", type=["PNG", "JPG", "JPEG"], label_visibility="collapsed", accept_multiple_files=False)

    if image:
        base64_string = base64.b64encode(image.read()).decode('utf-8')
        data_uri = f"data:{image.type};base64,{base64_string}"
    
        st.session_state.uploaded_image = data_uri

    return

def chat_layout():
    """
    This function manages the chat section:
    - chat message text field;
    - the message history;
    - the input from the image uploader;
    - sources.
    
    Param: A list of variables
    Return: None
    """

    chat_col, reset_col = st._bottom.columns([7.7, 1])

    chat_input = chat_col.chat_input("Your question")

    with _bottom.expander("Upload image as an input"):
        image_uploader()

    clear_history(reset_col)

    # Display chat messages from history on app rerun
    for message in st.session_state.messages:
        # Check if the message content has a type of 'text'
        for content in message["content"]:
                if content["type"] == "text":
                    with st.chat_message(message["role"]):
                        st.markdown(content["text"])

    if chat_input:
        image = st.session_state.get("uploaded_image")
        token = st.session_state.get("token")
        key = st.session_state.get("key")
        
    try:
        if chat_input:

            # display the user text message
            with st.chat_message("user"):
                st.markdown(chat_input)

            image_message = None

            # Add the user message to the chat history
            if chat_input:
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
            response = None
            messages = st.session_state.messages

            history_num = 20 # number of maximum past messages given to the model !! CUSTOMIZE IF NEEDED !!
            if history_num < len(messages):
                slicer = len(conv_memory) - history_num
                conv_memory = messages[slicer:]
            else:
                conv_memory = messages

            if image_message:
                conv_memory.append(image_message)

            # display the response and a source from a model
            with st.chat_message("assistant"):
                try:
                    # print(conv_memory)
                    response, sources = generate_response(api_token = token, key_input = key, conv_memory= conv_memory , variable_dict = None, context_input = None, file_id = None)

                    st.markdown(response)

                    if sources:
                        with st.expander(label= "Sources", expanded=False, icon="📖"):
                            counter = 0
                            for source in sources:
                                counter += 1
                                file_name = source["file_name"]
                                page_number = source["page_number"]
                                chunk_text = source["chunk"]
                                st.markdown(f"**{counter}. {file_name} - page {page_number}:**")
                                st.markdown(chunk_text) 

                    # Append the model response in the message history
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": [{"type": "text", "text": response}]
                    })

                except APIError as e:
                    print(e)
                    # st.info(e)

                except Exception as e:
                    print(e)
                    # pass

    except Exception as e:
        print(e)
        # pass

    return


def show():
    token = None
    Key = None

    correct_token = False

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
                correct_token = True
            
            except APIError as e:
                st.info('Please verify if this token has an access to a proper workspace')

    if token and key and correct_token:
        chat_layout()
