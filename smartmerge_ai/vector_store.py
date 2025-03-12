# # # Handles vector storage and retrieval (using FAISS, ChromaDB, etc.)
# # #  write logic here and store data into embeddings as seperate open_prs and closed_prs
# # # Or Store data in into Local database.
# # # create a file for local database connection in smartmerge_ai folder name (optional)
# # # for input file you will See in data/raw/closed_pr or data/raw/open_pr after running main.py
# # # Load environment variables

# # # below are just Example for project run purpose you need to modify this accordingly


# import os
# import json
# from dotenv import load_dotenv
# from langchain_community.vectorstores import FAISS
# from langchain_openai import OpenAIEmbeddings
# from langchain.text_splitter import RecursiveCharacterTextSplitter


# load_dotenv()
# OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# # Load PR Data
# def load_pr_data(json_file):
#     with open(json_file, 'r') as file:
#         return json.load(file)

# # Function to truncate long text fields
# def truncate_text(text, max_length=300):
#     return text[:max_length] + "..." if len(text) > max_length else text

# # Convert Closed PR data into text format for indexing with truncation
# def format_closed_prs(closed_prs):
#     formatted_prs = []
#     for pr in closed_prs:
#         file_changes = " | ".join(
#             [f"{fc['Filename']} ({fc['Status']})" for fc in pr.get("File Changes", [])]
#         )
#         comments = " | ".join(
#             [f"{c['User']}: {truncate_text(c['Body'])}" for c in pr.get("New Comments", [])]
#         )
#         formatted_prs.append(
#             f"PR Number: {pr['PR Number']}, Title: {truncate_text(pr['Title'])}, State: {pr['State']}, "
#             f"Author: {pr['Author']}, Created Date: {pr['Created Date']}, Merged Date: {pr['Merged Date']}, "
#             f"Base Branch: {pr['Base Branch']}, Head Branch: {pr['Head Branch']}, Merge Conflict: {pr['Merge Conflict']}, "
#             f"File Changes: {truncate_text(file_changes)}, Comments: {truncate_text(comments)}"
#         )
#     return formatted_prs

# # Split large text into smaller chunks
# def chunk_data(data, chunk_size=500):
#     splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=50)
#     return splitter.split_text("\n".join(data))

# # Initialize RAG-based retrieval system with chunked data
# def initialize_retriever(closed_pr_texts):
#     embeddings = OpenAIEmbeddings(model="text-embedding-3-large", openai_api_key=OPENAI_API_KEY)
#     chunked_texts = chunk_data(closed_pr_texts)
#     vector_store = FAISS.from_texts(chunked_texts, embeddings)
#     return vector_store.as_retriever()
import os
import pandas as pd
import json
import time
import chromadb  # ChromaDB for vector storage
from sentence_transformers import SentenceTransformer
 
# Load embedding model (BERT-based)
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
 
# Define base directory for ChromaDB storage
CHROMA_DB_PATH = "D:\\github 11-03\\SmartMergeAI\\data\\embeddings"
 
# Initialize ChromaDB clients for Open and Closed PRs
open_pr_client = chromadb.PersistentClient(path=os.path.join(CHROMA_DB_PATH, "open_pr"))
closed_pr_client = chromadb.PersistentClient(path=os.path.join(CHROMA_DB_PATH, "closed_pr"))
 
# Create separate collections
open_pr_collection = open_pr_client.get_or_create_collection(name="open_pr_embeddings")
closed_pr_collection = closed_pr_client.get_or_create_collection(name="closed_pr_embeddings")
 
def load_csv_data(csv_file):
    """Load CSV data as a pandas DataFrame."""
    if not os.path.isfile(csv_file):
        raise FileNotFoundError(f"File not found: {csv_file}")
    return pd.read_csv(csv_file, dtype=str).fillna("")
 
def chunk_text(text, max_chunk_size=512):
    """
    Splits long text into smaller chunks before embedding.
    """
    words = text.split()
    chunks = [" ".join(words[i:i + max_chunk_size]) for i in range(0, len(words), max_chunk_size)]
    return chunks
 
def generate_embeddings(text_list):
    """Generate embeddings for each text chunk."""
    embeddings = []
    for i, text in enumerate(text_list):
        try:
            text_chunks = chunk_text(text)  # Split long text into chunks
            for chunk in text_chunks:
                embedding_vector = embedding_model.encode(chunk).tolist()  # Generate embedding
                embeddings.append((chunk, embedding_vector))  # Store with chunk
            time.sleep(0.1)  # Small delay to prevent overloading
        except Exception as e:
            print(f"Error embedding text {i}: {e}")
    return embeddings
 
def store_embeddings_in_chroma(embeddings, csv_file, collection):
    """Store embeddings in the appropriate ChromaDB collection."""
    for i, (text, vector) in enumerate(embeddings):
        doc_id = f"{os.path.basename(csv_file)}_{i}"
        collection.add(
            ids=[doc_id],
            embeddings=[vector],
            metadatas=[{"source": csv_file, "chunk": text}]
        )
    print(f"Stored {len(embeddings)} embeddings in ChromaDB from {csv_file}")
 
def process_csv_to_vectors(csv_file, collection):
    """Process CSV file: convert to text, chunk, generate embeddings, and store in ChromaDB."""
    try:
        df = load_csv_data(csv_file)
        text_data = df.astype(str).apply(lambda x: ' '.join(x), axis=1).tolist()
        vector_data = generate_embeddings(text_data)
        store_embeddings_in_chroma(vector_data, csv_file, collection)
    except Exception as e:
        print(f"Error processing file {csv_file}: {e}")
 
if __name__ == "__main__":
    # Process Open PRs
    open_pr_csv = "D:\\github 11-03\\SmartMergeAI\\smartmerge_ai\\data\\raw\\open_pr\\wheel_all_open_prs.csv"
    process_csv_to_vectors(open_pr_csv, open_pr_collection)
 
    # Process Closed PRs
    closed_pr_csv = "D:\\github 11-03\\SmartMergeAI\\smartmerge_ai\\data\\raw\\closed_pr\\wheel_all_closed_prs.csv"
    process_csv_to_vectors(closed_pr_csv, closed_pr_collection)