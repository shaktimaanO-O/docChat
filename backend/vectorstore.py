import os
import time
from pinecone import Pinecone,ServerlessSpec
from langchain_pinecone import PineconeVectorStore
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from config import PINECONE_API_KEY, PINECONE_ENVIRONMENT, PINECONE_INDEX_NAME
os.environ["PINECONE_API_KEY"]= PINECONE_API_KEY

#pinecone client
pc = Pinecone(api_key=PINECONE_API_KEY)
embeddings = HuggingFaceEmbeddings(model_name = "sentence-transformers/all-MiniLM-L6-v2")

INDEX_NAME = PINECONE_INDEX_NAME or "rag-index"

def ensure_index_exists():
    """Create the Pinecone index if it does not already exist."""
    if INDEX_NAME not in pc.list_indexes().names():
        print(f"Creating new Pinecone index: {INDEX_NAME}")
        pc.create_index(
            name=INDEX_NAME,
            dimension=384,
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region=PINECONE_ENVIRONMENT)
        )

        while not pc.describe_index(INDEX_NAME).status["ready"]:
            time.sleep(1)

        print(f"Created Pinecone index: {INDEX_NAME}")

def get_retriever():
    """Initalizes and returns the Pinecone vector store retriever"""
    ensure_index_exists()
    
    vectorstore = PineconeVectorStore(index_name= INDEX_NAME,embedding=embeddings)

    return vectorstore.as_retriever()

def add_document(text_content:str):
    """add a single document to the pinecone vector store 
    Splits the  text into chunks before embedding and upserting """

    if not text_content:
        raise ValueError("Document cannot be empty.")
    
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size = 1000,
        chunk_overlap = 200,
        add_start_index = True
    )
    documents = text_splitter.create_documents([text_content])

    print("Splitting the document into chunks for indexing ... ")
    ensure_index_exists()
    vectorstore= PineconeVectorStore(index_name=INDEX_NAME,embedding= embeddings)
    vectorstore.add_documents(documents)
