import os
from dotenv import load_dotenv
import openai
import requests
import json
import time
from datetime import datetime
import streamlit as st

import utils


#Application to load the OpenAI and other keys. 
load_dotenv()

#Get the OpenAI Model parameters
#Set the OpenAI API key from Streamlit Secrets Key
openai.api_key = st.secrets["OPENAI_API_KEY"]
client = openai.OpenAI()
model = utils.get_openai_model() #Get the OpenAI model (e.g: GPT 4o mini)

# Initialize all the sessions in Steamlit. States are used so that code is not called each time the page is refreshed.
if "file_id_list" not in st.session_state:
    st.session_state.file_id_list = [] #List of file ids uploaded by the user

if "start_chat" not in st.session_state:
    st.session_state.start_chat = False #Set the chat session to False. This will be set to True when the user starts chatting.

if "thread_id" not in st.session_state:
    st.session_state.thread_id = None #Set the thread_id to None. This will be set to the thread_id when the user starts chatting.

if "assistant_id" not in st.session_state:
    st.session_state.assistant_id = utils.get_assistant_id() #Get the OpenAI Assistant ID

if "vector_store_id" not in st.session_state:
    st.session_state.vector_store_id = utils.get_vector_store_id() #Get the OpenAI Vector Store ID

if "openai_model" not in st.session_state:
    st.session_state.openai_model = model #Set the OpenAI model to the model that we have initialized.

# Set up our front end page
st.set_page_config(page_title="FBLA Interactive Story Teller", page_icon=":books:")

# ==== Function definitions etc ===== #
# Function to upload the file to OpenAI
# This function will upload the file to OpenAI and return the file ID
# This file ID will be used to create the story
# input: filepath - the path of the file to be uploaded, client - the OpenAI client
# output: response.id - the file ID of the uploaded file   
def upload_to_openai(filepath, client):
    file_upload_status = utils.upload_file_to_vector_store(client, st.session_state.vector_store_id, filepath)
    return file_upload_status

# === Sidebar - where users can upload files
file_uploaded = st.sidebar.file_uploader(
    "Upload the notes from your science class.", 
    key="file_upload"
)

# Upload file button - store the file ID
if st.sidebar.button("Upload File"):
    if file_uploaded:
        with open(f"{file_uploaded.name}", "wb") as f:
            f.write(file_uploaded.getbuffer())
        st.sidebar.write(f"Notes uploaded: {file_uploaded.name}")
        #Upload the file to OpenAI and get the file ID 
        file_upload_status = upload_to_openai(f"{file_uploaded.name}", client)
        #Append the file ID to the session state.
        st.session_state.file_id_list.append(file_upload_status)
        # st.sidebar.write(f"file_upload_status:: {file_upload_status}")

# Display those file ids
if st.session_state.file_id_list:
    st.sidebar.write("Uploaded File IDs:")
    #Check if these files exist in the flie list.
    file_objects = client.files.list()
    if file_objects == None:
        st.sidebar.warning("No files found in Open AI.")
    else:
        for file_id in st.session_state.file_id_list:
            for file in file_objects:
                if file.id == file_id:
                    st.sidebar.write(f"File.id in Client: {file.id, file.filename}")
    # #Print the files in the st.session_state.file_id_list. 
    # # These should be the ones that are also attached to the OpenAI Client
    # for file_id in st.session_state.file_id_list:
    #      st.sidebar.write(file_id)

#Set the streamlit session for chatting and add create the Open AI Thread. 
# Create a new thread for this chat session if one does not exist already.
# If it exists, then use the existing thread. 
if not st.session_state.thread_id: 
    chat_thread = client.beta.threads.create()
    st.session_state.thread_id = chat_thread.id

#Set the Streamlit state for Chat Session to True to indicate that the chat has started.
st.session_state.start_chat = True

# The main interface ...
st.title("SuperNote Taker")
st.write("Get the complete notes on what your teacher has taught in class. This is crowdsourced from all the student's notes.")
st.write("You can get a summary of the notes, ask for explanations on topics covered in the notes, get flashcards or quizlets or event translate the notes into your preferred language")

# Check sessions
if st.session_state.start_chat:
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Show existing messages if any. 
    # Note that the streamlit runs this file each time. So this line will display all the messages so far.
    # It will display the message  
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # chat input for the user
    prompt = st.chat_input("Type...")
    if prompt:
        # Add user message to the state and display on the screen
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # add the user's message to the existing Open AI Assistant's Thread of Messages. 
        client.beta.threads.messages.create(
            thread_id=st.session_state.thread_id, role="user", content=prompt
        )

        # Create a run with additioal instructions
        run = client.beta.threads.runs.create(
            thread_id=st.session_state.thread_id,
            assistant_id=st.session_state.assistant_id  
        )

        # Show a spinner while the assistant is thinking...
        with st.spinner("Wait... Generating response..."):
            while run.status != "completed":
                time.sleep(1)
                run = client.beta.threads.runs.retrieve(
                    thread_id=st.session_state.thread_id, run_id=run.id
                )
            # Retrieve messages added by the openAI Assistant to the current Thread
            messages = client.beta.threads.messages.list(
                thread_id=st.session_state.thread_id
            )
            # Go through all the messages and append the assistant message to assistant_messages
            assistant_messages_for_run = []
            for message in messages:
                if message.run_id == run.id and message.role == "assistant":
                    assistant_messages_for_run.append(message)

            # assistant_messages_for_run = [
            #     message
            #     for message in messages
            #     if message.run_id == run.id and message.role == "assistant"
            # ]

            for message in assistant_messages_for_run:
                # full_response = process_message_with_citations(message=message)
                full_response = message.content[0].text.value
                st.session_state.messages.append(
                    {"role": "assistant", "content": full_response}
                )
                with st.chat_message("assistant"):
                    st.markdown(full_response, unsafe_allow_html=True)





