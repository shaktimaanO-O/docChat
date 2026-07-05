import os
from dotenv import load_dotenv
load_dotenv()

PINECONE_API_KEY= os.getenv("PINECONE_API_KEY")

PINECONE_ENVIRONMENT= os.getenv("PINECONE_ENVIRONMENT","us-east-1")
PINECONE_INDEX_NAME=os.getenv("PINECONE_INDEX_NAME")
TAVILY_API_KEY= os.getenv("TAVILY_API_KEY")
GROQ_API_KEY= os.getenv("GROQ_API_KEY")
GROQ_MODEL=os.getenv("GROQ_MODEL","llama-3.3-70b-versatile")
DOC_SOURCE_DIR=os.getenv("DOC_SOURCE_DIR","data")
EMBED_MODEL=os.getenv("EMBED_MODEL","sentence-transformer/all-MinLM-L6-v2")
