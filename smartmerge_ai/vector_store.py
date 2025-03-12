# # Handles vector storage and retrieval (using FAISS, ChromaDB, etc.)
# #  write logic here and store data into embeddings as seperate open_prs and closed_prs
# # Or Store data in into Local database.
# # create a file for local database connection in smartmerge_ai folder name (optional)
# # for input file you will See in data/raw/closed_pr or data/raw/open_pr after running main.py
# # Load environment variables

# # below are just Example for project run purpose you need to modify this accordingly


import os
import json
from dotenv import load_dotenv
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter


load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Load PR Data
def load_pr_data(json_file):
    with open(json_file, 'r') as file:
        return json.load(file)

# Function to truncate long text fields
def truncate_text(text, max_length=300):
    return text[:max_length] + "..." if len(text) > max_length else text

# Convert Closed PR data into text format for indexing with truncation
def format_closed_prs(closed_prs):
    formatted_prs = []
    for pr in closed_prs:
        file_changes = " | ".join(
            [f"{fc['Filename']} ({fc['Status']})" for fc in pr.get("File Changes", [])]
        )
        comments = " | ".join(
            [f"{c['User']}: {truncate_text(c['Body'])}" for c in pr.get("New Comments", [])]
        )
        formatted_prs.append(
            f"PR Number: {pr['PR Number']}, Title: {truncate_text(pr['Title'])}, State: {pr['State']}, "
            f"Author: {pr['Author']}, Created Date: {pr['Created Date']}, Merged Date: {pr['Merged Date']}, "
            f"Base Branch: {pr['Base Branch']}, Head Branch: {pr['Head Branch']}, Merge Conflict: {pr['Merge Conflict']}, "
            f"File Changes: {truncate_text(file_changes)}, Comments: {truncate_text(comments)}"
        )
    return formatted_prs

# Split large text into smaller chunks
def chunk_data(data, chunk_size=500):
    splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=50)
    return splitter.split_text("\n".join(data))

# Initialize RAG-based retrieval system with chunked data
def initialize_retriever(closed_pr_texts):
    embeddings = OpenAIEmbeddings(model="text-embedding-3-large", openai_api_key=OPENAI_API_KEY)
    chunked_texts = chunk_data(closed_pr_texts)
    vector_store = FAISS.from_texts(chunked_texts, embeddings)
    return vector_store.as_retriever()

