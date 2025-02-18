import os
import orq_ai_sdk
from orq_ai_sdk import Orq
import json
import streamlit as st
import re
import requests


def generate_response(variable_dict, api_token, key_input, context_input, file_id, conv_memory):
    """
    This function invokes the deployment and extracts the text and sources from the response.
    
    Param:
        - variable_dict: Dict[str, str] - where the key is a variable name and the corresponding user input is the value;
        - api_token: str;
        - key_input: str;
        - context_input: Dict[str, List[str]] - where the key is a context key given by the user and the value is a list of corresponding context values given by the user;
        - file_id: List[str]; - List with a file id;
        - conv_memory: List[Dict[str, Any]] - List with past messages, where each message is a dictionary containing a role, and the content.

    Return:
        - response: str - text generated by the model;
        - sources: List[Dict[str, str]] - List of sources, where each source is represented by a dictionary with a file name, a page number and a chunk.
    """
    if not file_id:
        file_id = None
    
    client = Orq(
        api_key=api_token
    )

    print(f"context {context_input}")
    print(f"variabvles {variable_dict}")

    generation = client.deployments.invoke(
        key=key_input,
        context=context_input,
        inputs=variable_dict,
        messages= conv_memory,
        file_ids=file_id,
        invoke_options={"include_retrievals": True}
    )

    # extracting the text from the generation
    response = generation.choices[0].message.content

    trace_id = generation.id

    # collecting the sources' information from generation retrievals
    sources = []
    if generation.retrievals:
        for retrieval in generation.retrievals:
            sources.append({
                "file_name": retrieval.metadata.file_name,
                "page_number": retrieval.metadata.page_number,
                "chunk": retrieval.document
            })

    return response, sources, trace_id


def get_dep_config(api_token, key_input):
    """
    This function gets the configuration of a given deployment.

    Param:
        - api_token: str;
        - key_input: str

    Return: 
        - Dict[] - deployment configuration 
    """
    client = Orq(
        api_key=api_token
    )

    prompt_config = client.deployments.get_config(
        key=key_input,
        context={},
        inputs={},
    )

    # return prompt_config.to_dict()
    return prompt_config.__dict__


def get_variables(api_token, key_input):
    """
    This function gets a set of variables from the deployment configuration.

    Param:
        - api_token: str;
        - key_input: str

    Return: 
        - Set(str)
    """
    configuration = get_dep_config(api_token, key_input)

    variables_all = []
    
    messages = configuration["messages"]

    for message in messages:
        if message.role != 'user': # ignore variables stated in user massages cause we overite it anyway 
            content = message.content

            variables = re.findall(r'\{\{(.*?)\}\}', content) # extract all substrings in {{x}} brackets

            variables_all = variables_all + variables

    # Customized solely for the steel catalog deployment
    if key_input == "steel_catalog_RAG":
        variables_all_2 = [variable for variable in variables_all if variable != "steel_catalog"]
    elif key_input == "ChatDemo":
        variables_all_2 = [variable for variable in variables_all if variable != "EU_AI_ACT"]
    elif key_input == "translator-streamlit-demo":
        variables_all_2 = [variable for variable in variables_all if variable != "sourcetext"]
    elif key_input == "automatic_examination_check":
        variables_all_2 = [variable for variable in variables_all if (variable != "Exam_Questions" and variable != "Student_Answers")]
    else:
        variables_all_2 = variables_all

    variables_set = set([variable.strip() for variable in variables_all_2])

    return variables_set


def convert(uploaded_file, api_token):
    """
    This function takes the uploaded file and returns its ID.

    Param:
        - uploaded_file: UploadedFile | None;
        - key_input: str

    Return: 
        - file_id: str
    """
    headers = {
        'Authorization': f'Bearer {api_token}',
    }

    files = {
        'purpose': (None, 'retrieval'),
        'file': (uploaded_file.name, uploaded_file, uploaded_file.type),
    }

    response = requests.post('https://my.orq.ai/v2/files', headers=headers, files=files)

    result = response.json()
    json.dumps(result, indent=4)

    file_id = result["_id"]

    return file_id 


def get_deployments(api_token):
    """
    This function takes an API token and returns a list with up to 50 deployment keys of a user with this token

    Param:
        - api_token: str

    Return: 
        - depl_key_list: List[str]
    """
    headers = {
        'Authorization': f'Bearer {api_token}'
    }

    params = {
        "limit": 50
    }

    response = requests.get('https://my.orq.ai/v2/deployments', headers=headers, params=params)

    result = response.json()
    json.dumps(result, indent=4)

    depl_key_list = []

    for deployment in result["data"]:
        deployment_name = deployment["key"]
        depl_key_list.append(deployment_name)

    return depl_key_list


def set_feedback(feedback, api_token, trace_id):
    try:
        payload = {
            "property": "rating",
            "value": feedback,
            "trace_id": trace_id
        }
        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            'authorization': f'Bearer {api_token}'
        }

        response = requests.post("https://api.orq.ai/v2/feedback", json=payload, headers=headers)

    except Exception as e:
        print(e)

    return


def post_correction(user_correction, api_token, trace_id):
    try:
        payload = {
            "property": "correction",
            "value": user_correction,
            "trace_id": trace_id
        }
        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            'authorization': f'Bearer {api_token}'
        }

        response = requests.post("https://api.orq.ai/v2/feedback", json=payload, headers=headers)

    except Exception as e:
        print(e)

    return