import os
import json
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.llms import OpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import RetrievalQA
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# JSON 파일에서 용어집 데이터 로드
def load_glossary(file_path="data/combined_keyvalue_form.json"):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"용어집 파일을 찾을 수 없습니다: {file_path}")
    with open(file_path, "r", encoding="utf-8") as f:
        glossary = json.load(f)
    return glossary

# LangChain QA 검색 시스템 초기화
def initialize_retrieval_qa():
    # 임베딩 모델 정의
    embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)
    
    # FAISS 인덱스 로드
    vectorstore = FAISS.load_local("data/faiss_index", embeddings)

    # 프롬프트 템플릿 정의
    prompt = PromptTemplate(
        template="당신은 Python 학습자를 위한 유용한 도우미입니다. 명확하고 간결한 답변을 제공하세요.\n\n질문: {question}\n답변:",
        input_variables=["question"]
    )
    
    # RetrievalQA 체인 초기화
    qa = RetrievalQA.from_chain_type(
        llm=OpenAI(model="text-davinci-003", temperature=0.0, openai_api_key=OPENAI_API_KEY),
        retriever=vectorstore.as_retriever(),
        chain_type_kwargs={"prompt": prompt}
    )
    return qa

# 용어집에서 정의 검색
def get_glossary_definition(term):
    qa = initialize_retrieval_qa()
    response = qa.run(term)
    return response

# 환경 변수 확인
def check_env():
    if not OPENAI_API_KEY:
        raise EnvironmentError("환경에 OPENAI_API_KEY가 설정되어 있지 않습니다.")
