import os
import json
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.llms import OpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import RetrievalQA
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Load glossary data from JSON file
def load_glossary(file_path="data/combined_keyvalue_form.json"):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Glossary file not found: {file_path}")
    with open(file_path, "r", encoding="utf-8") as f:
        glossary = json.load(f)
    return glossary

# Initialize LangChain QA Retrieval system
def initialize_retrieval_qa():
    # Define the embeddings model
    embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)
    
    # Load the FAISS index
    vectorstore = FAISS.load_local("data/faiss_index", embeddings)

    # Define the prompt template
    prompt = PromptTemplate(
        template="You are a helpful assistant for Python learners. Provide clear, concise answers.\n\nQuestion: {question}\nAnswer:",
        input_variables=["question"]
    )
    
    # Initialize the RetrievalQA chain
    qa = RetrievalQA.from_chain_type(
        llm=OpenAI(model="text-davinci-003", temperature=0.0, openai_api_key=OPENAI_API_KEY),
        retriever=vectorstore.as_retriever(),
        chain_type_kwargs={"prompt": prompt}
    )
    return qa

# Retrieve answer from glossary
def get_glossary_definition(term):
    qa = initialize_retrieval_qa()
    response = qa.run(term)
    return response

# Check environment variables
def check_env():
    if not OPENAI_API_KEY:
        raise EnvironmentError("OPENAI_API_KEY is not set in your environment.")
