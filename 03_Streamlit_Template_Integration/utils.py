import os
from orq_ai_sdk import OrqAI
import json
import streamlit as st
import re
import requests

def generate_response(variable_dict, api_token, key_input, context_input, file_ids, conv_memory):

    if not file_ids:
        file_ids = None
    
    client = OrqAI(
        api_key=api_token,
        environment="production"
    )

    generation = client.deployments.invoke(
        key=key_input,
        context=context_input,
        inputs=variable_dict,
        metadata={
            "custom-field-name": "custom-metadata-value"
        },
        messages= conv_memory,
        file_ids=file_ids,
        invoke_options={"include_retrievals": True} # only for steel catalog
    )

    response = generation.choices[0].message.content

    ####################################################################################################################################################

    # For steel catalog

    sources = []

    for retrieval in generation.retrievals:
        sources.append({
            "file_name": retrieval.metadata.file_name,
            "page_number": retrieval.metadata.page_number,
            "chunk": retrieval.document
        })

    ####################################################################################################################################################

    return response, sources # sources only for steel catalog


def get_dep_config(api_token, key_input):

    client = OrqAI(
        api_key=api_token,
        environment="production"
    )

    prompt_config = client.deployments.get_config(
        key=key_input,
        context={},
        inputs={},
        metadata={
            "custom-field-name": "custom-metadata-value"
        }
    )

    return prompt_config.to_dict()


def get_variables(api_token, key_input):

    configuration = get_dep_config(api_token, key_input)

    variables_all = []
    
    messages = configuration["messages"]

    for message in messages:
        if message['role'] != 'user': # ignore variables stated in user massages cause we overite it anyway 
            content = message["content"]

            variables = re.findall(r'\{\{(.*?)\}\}', content)

            variables_all = variables_all + variables

    ####################################################################################################################################################

    # For steel catalog
    variables_all_2 = [variable for variable in variables_all if variable != "steel_catalog"]
    ####################################################################################################################################################

    variables_set = set([variable.strip() for variable in variables_all_2]) # delete _2

    return variables_set


def convert(uploaded_file, api_token):
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

    headers = {
        'Authorization': f'Bearer {api_token}'
    }

    response = requests.get('https://my.orq.ai/v2/deployments', headers=headers)

    result = response.json()
    json.dumps(result, indent=4)

    depl_key_list = []

    for deployment in result["data"]:
        deployment_name = deployment["key"]
        depl_key_list.append(deployment_name)

    return depl_key_list

