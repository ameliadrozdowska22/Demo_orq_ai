import streamlit as st
from utils import generate_response, get_variables, convert, get_deployments
import time
import base64
from typing import Optional
from orq_ai_sdk import OrqAI    
from orq_ai_sdk.exceptions import OrqAIException
from streamlit import _bottom
import base64


# Set up page config
APP_TITLE = 'Orq.ai Chat'

st.set_page_config(APP_TITLE, page_icon="📈", layout="wide")
st.title(APP_TITLE)


# Initialize session state variables if they don't exist

# if "file_id" not in st.session_state:
#     st.session_state.file_id = None
if "file_uploaded" not in st.session_state:
    st.session_state.file_uploaded = False
if "uploaded_files" not in st.session_state:
    st.session_state.uploaded_files = None
if "uploaded_image" not in st.session_state:
    st.session_state.uploaded_image = None
if "file_ids" not in st.session_state:
    st.session_state.file_ids = []
if "variable_dict" not in st.session_state:  
    st.session_state.variable_dict = {}
if "messages" not in st.session_state: # Initialize chat history
    st.session_state.messages = []
if "context_input_dict" not in st.session_state:
    st.session_state.context_input_dict = {}


def style():

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


def get_response(variable_dict, token, key, context, file_id, chat_input):
    """
    This function gets the response and displays it word by word
    """
    response, sources = generate_response(variable_dict, token, key, context, file_id, chat_input)

    return response, sources
    


def variable_textfields(variables):

    if len(variables)>0:
        st.markdown("<p style='font-weight: normal; font-size: 14px;'>Variables</p>", unsafe_allow_html=True)
    
    # creating a text field for every variable in the given deployment
    for index, variable in enumerate(variables):
        if f"variable_disabled_{index}" not in st.session_state:
            st.session_state[f"variable_disabled_{index}"] = False

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

    file_uploaded_bool = st.session_state.file_uploaded
    uploaded_files = st.session_state.uploaded_files
    file_ids = st.session_state.file_ids

    if file_uploaded_bool:
        for file in uploaded_files:
            file_id = convert(file, st.session_state.get("token"))
            file_ids.append(file_id)

    return


def context_section():

    st.markdown("<p style='font-weight: normal; font-size: 14px;'>Context</p>", unsafe_allow_html=True)
    key_col, val_col, plus_col, min_col = st.columns([2, 2, 1, 1])

    context_input_dict = st.session_state.context_input_dict

    # creating dynamicly initialized text fields for context
    if "context_rows" not in st.session_state:
        st.session_state.context_rows = [1]  # keeping track of context rows in the session

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

        if context_key_input:
            if context_value_input == '':
                context_input_dict[context_key_input] = []
            else:
                context_input_dict[context_key_input] = context_value_input.split(",")

            st.session_state.context_input_dict = context_input_dict

        with plus_col:
            if i == 0:
                add_button = st.button("➕", key=f"add_button_{unique_id}")
            
                if add_button:
                    if len(st.session_state.context_rows) + 1 <= 10: # setting a limit of context rows to 10
                        st.session_state.context_rows.append(len(st.session_state.context_rows) + 1) # adding a new unique_id
                    else:
                        pass

        with min_col:
            if i == 0:
                hide_button = st.button("➖", key=f"hide_button_{unique_id}")

                if hide_button:
                    if len(st.session_state.context_rows) > 1:  # at least 1 row remains
                        st.session_state.context_rows.pop()
                        last_key = list(st.session_state.context_input_dict)[-1]
                        st.session_state.context_input_dict.pop(last_key)
        
    return

def image_uploader():
    # Accept a single file
    image = st.file_uploader("Upload an image", type=["PNG", "JPG", "JPEG"], label_visibility="collapsed", accept_multiple_files=False)

    if image:
        base64_string = base64.b64encode(image.read()).decode('utf-8')
        data_uri = f"data:{image.type};base64,{base64_string}"
    
        st.session_state.uploaded_image = data_uri

    return
    

def chat_layout(variables):
    """
    This function arranges the chat layout and it manages chat history 
    """

    chat_input = st.chat_input("Your question")

    with _bottom.expander("Upload image as an input"):
        image_uploader()

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
        context = st.session_state.context_input_dict
        variable_dict = st.session_state.variable_dict
        image = st.session_state.get("uploaded_image")
        
    try:
        # if the token and key was set, display user input and the response

        if token and key and chat_input and (len(variables) == len(variable_dict)):
            
            if st.session_state.file_uploaded:
                upload_file()

            file_ids = st.session_state.file_ids

            with st.chat_message("user"):
                st.markdown(chat_input)

            image_message = None

            # Add user message to chat history
            if chat_input:
                # Append text message
                text_message = {
                    "role": "user",
                    "content": [{"type": "text", "text": chat_input}]
                }
                st.session_state.messages.append(text_message)

                # Append each uploaded image as a separate message
                if image:
                    image_message = {
                        "role": "user",
                        "content": [{"type": "image_url", "image_url": { "url": image}}]
                    }
                    del st.session_state["uploaded_image"]

            conv_memory = []
            response = None

            messages = st.session_state.messages

            history_num = 10 # number of maximum messages given to the model for a reference
            if history_num < len(messages):
                slicer = len(conv_memory) - history_num
                conv_memory = messages[slicer:]
            else:
                conv_memory = messages

            if image_message:
                conv_memory.append(image_message)


            with st.chat_message("assistant"):
                try:
                    
                    response, sources = get_response(variable_dict, token, key, context, file_ids, conv_memory)

                    st.markdown(response)

                    #####################################################################################################################

                    with st.expander(label= "Sources", expanded=False, icon="📖"):
                        if not sources:
                            st.text("No sources available.")
                        else:
                            counter = 0
                            for source in sources:
                                counter += 1
                                file_name = source["file_name"]
                                page_number = source["page_number"]
                                chunk_text = source["chunk"]
                                st.markdown(f"**{counter}. {file_name} - {page_number} page:**")
                                st.markdown(chunk_text) 

                    #####################################################################################################################

                     # Append assistant response as a single text object
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": [{"type": "text", "text": response}]  # content is a single dictionary
                    })

                except:
                    pass

        else:
            st.info('Please provide all the necessary parameters')

    except:
        pass

    return


def additional_parameters_layout(variables):
    """
    This function arranges the second part of the sidebar layout, it allows to dynamicly generate text fields for context key and value, it also sets the context dict in the session
    """

    with st.sidebar.expander(label="Set additional parameters", expanded=True):
        variable_textfields(variables)

        uploaded_files = st.file_uploader("Upload a file", type=["pdf", "txt", "docx", "csv", "xls"], accept_multiple_files=False)

        if st.session_state.uploaded_files != uploaded_files:
            st.session_state.uploaded_files = uploaded_files
        
        if uploaded_files:
            st.session_state.file_uploaded = True
            
        context_section()

    return


def sidebar_layout():
    """
    This function arranges sidebar layout, and sets the values of API token and deployment key in the session
    """

    # st.sidebar.image("assets/orqai_logo.png", width=150)

    with st.sidebar.expander(label="Set parameters", expanded=True):

        with st.form("parameters", border=False):

            token_input = st.text_input(
                "Access token",
                label_visibility="visible",
                disabled=False,
                placeholder="Access token"
            )

            if token_input:
                try:
                    depl_list = get_deployments(token_input)
                    key_input = st.selectbox(
                        "Deployment key",
                        options= [i.replace("_", " ") for i in depl_list],
                        label_visibility="visible",
                        disabled=False,
                        placeholder="Deployment key",
                        index=None
                    )

                    if key_input:
                        key_input = key_input.replace(" ","_")
                        st.session_state["key"] = key_input
                except:
                    st.info("Invalid or missing token. Please verify the token and try again.")
                
            set_button = st.form_submit_button("Set parameters")

    if set_button:
        st.session_state["token"] = token_input

    # getting variables for a given deployment
    try:
        if key_input and token_input:
                variables = list(get_variables(token_input, key_input))

                CHAT_SUBTITLE = f"{key_input.
                            replace("-"," ")
                            .replace("_"," ")
                            .capitalize()}"
                
                st.markdown(f"<p margin-top: 0px; margin-botton:0px; style='font-weight: 600; font-size: 22px; color:#BDBDC1;'>{CHAT_SUBTITLE}</p>", unsafe_allow_html=True)

                additional_parameters_layout(variables)
                chat_layout(variables) 

    except:
        pass

    return



if __name__ == "__main__":
    sidebar_layout()
    style()
