#This file contains all the functions that are needed for the FBLA Streamlit code to run. 
import os
from dotenv import load_dotenv
import openai
import logging

#Application to load the OpenAI and other keys. 
load_dotenv()

#Function to return the Open AI Client. 
def get_openai_client():
    client = openai.OpenAI()
    return client

#Function to get the Open AI Model
def get_openai_model():
    return "gpt-4o-mini"

#Function to return the Open AI Assistant ID
def get_assistant_id():
    return "asst_A3XOjQiGb0wxlWnvXH1BDLy4"

#Function to return the Vector Store ID
def get_vector_store_id():
    return "vs_iZ5WSjRU4Mq2izbJYIrrCgWb"

#Write a function that checks if the Assitant with the given name already exists.
#If it exists, simply return the ID for that Assistant so we can use it in our code. 
#But if it does not exist, Create that Assistant and return Assistant 
#This way, we will avoid having to create a whole new Assistant again. 
# Input: Name of Assistant, OpenAI client, OpenAI model to use
def check_and_get_assistant(assistant_name, client):
    #Get a list of existing assistants in descenidng order of dates. 
    my_assistants = client.beta.assistants.list(
        order="desc",
        limit="20",
    )
    for assistant in my_assistants:
        if assistant.name == assistant_name:
            return assistant
    #Assistant not found. Create one. 
    # If it does exist, update the instructions for that Assistant with the latest instructions above.  
    assistant = client.beta.assistants.create(
            name=assistant_name,
            model=get_openai_model(),
            tools=[{"type": "file_search"}], 
    )
    return assistant

# Write a function that updates the  instructions for that Assistant
# Input: OpenAI client, Assistant ID, Instructions for Assistant, 
# Output: Assistant
def updated_assistant_instruction(client, assistant_id, assiatant_instruction):
    #Update the instructions for this assistant. 
    assistant = client.beta.assistants.update(
        assistant_id,
        instructions= assiatant_instruction
    )
    return assistant

# #Check if the vectore store by this name exists. 
# And if not, create such a vectore store. 
# Input: Open AI Client, Vector Store Name
# Output: Vector Store
def check_and_get_vector_store(client, vs_name):
    vs_list = client.vector_stores.list()
    for vs in vs_list:
        if vs.name == vs_name:
            return vs
    # # Vector Store does not exist. Create one. 
    vs = client.vector_stores.create(vs_name)
    return vs

# # Function to check if a file exists in the vector store.
# Input: Open AI Client, Vectore Store ID, Filename
# Output: File object in vector store (if file exists); False if file does not exist in vectore store
def file_exists_in_vector_store(client, vector_store_id, filename):
    # List all files in the vector store
    response = client.vector_stores.files.list(vector_store_id=vector_store_id)
    files = response.data
    
    # Check if any file has the same name as the target filename
    for file in files:
        # Retrieve file details to get the filename
        file_details = client.files.retrieve(file_id=file.id)
        if file_details.filename == filename:
            return file_details
    # File does not exist. Return False. 
    return False 

#Upload File.
# Input: Open AI Client, Vectore Store ID, Filename
#Output: Return Vector Sore ID
def upload_file_to_vector_store(client, vector_store_id, filename):
    ##Check if the file with that filename exists
    file_object = file_exists_in_vector_store(client, vector_store_id, filename)
    if not file_object:
        #File does not exist. Upload file and attach to VS
        # Ready the files for upload to OpenAI
        #Add all the files in an array called file_paths
        file_paths = [filename]
        #Append these files to file_streams
        file_streams = [open(path, "rb") for path in file_paths]
        # # Use the upload and poll SDK helper to upload the files, add them to the vector store,
        # # and poll the status of the file batch for completion.
        file_batch = client.vector_stores.file_batches.upload_and_poll(
            vector_store_id=vector_store_id, files=file_streams
        )
        #Get the File that was uploaded. 
        file_object = file_exists_in_vector_store(client, vector_store_id, filename)
    #Return the File ID of the file that was uploaded to the Vectore Store. 
    return file_object

# Function: Update_assistant_vector_store
# This function will ensure the OpenAI assistant uses the updated Vector Store
# The Vector store contains the uploaded notes of various students.  
# Input: Open AI Client, Assistant_ID, Vector_Store_ID
# Output: Open AI Assistant object
def update_assistant_vector_store(client, assistant_id, vs_id):
    assistant = client.beta.assistants.update(
        assistant_id=assistant_id,
        tool_resources={"file_search": {"vector_store_ids": [vs_id]}},
    )
    return assistant
