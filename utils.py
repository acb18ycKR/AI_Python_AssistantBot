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
    """
    JSON 파일에서 용어집 데이터를 로드합니다.

    Args:
        file_path (str): JSON 파일 경로.

    Returns:
        dict: 용어집 데이터.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"용어집 파일을 찾을 수 없습니다: {file_path}")
    with open(file_path, "r", encoding="utf-8") as f:
        glossary = json.load(f)
    return glossary

# LangChain QA 검색 시스템 초기화
def initialize_retrieval_qa():
    """
    LangChain Retrieval QA 시스템을 초기화합니다.

    Returns:
        RetrievalQA: 초기화된 RetrievalQA 객체.
    """
    # 임베딩 모델 정의
    embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)
    
    # FAISS 인덱스 로드
    vectorstore = FAISS.load_local("data/faiss_index", embeddings)

    # 프롬프트 템플릿 정의
    prompt = PromptTemplate(
        template=(
            "당신은 Python 학습자를 위한 유용한 도우미입니다. "
            "명확하고 간결한 답변을 제공하세요.\n\n"
            "질문: {question}\n답변:"
        ),
        input_variables=["question"]
    )
    
    # RetrievalQA 체인 초기화
    qa = RetrievalQA.from_chain_type(
        llm=OpenAI(model="text-davinci-003", temperature=0.0, openai_api_key=OPENAI_API_KEY),
        retriever=vectorstore.as_retriever(),
        chain_type_kwargs={"prompt": prompt}
    )
    return qa

# 용어 정의 검색
def search_definition(term):
    """
    주어진 용어의 정의를 검색합니다.

    Args:
        term (str): 검색할 용어.

    Returns:
        str: 검색된 용어 정의.
    """
    qa_system = initialize_retrieval_qa()
    response = qa_system.run(term)
    return response

# 환경 변수 확인
def check_env():
    """
    필수 환경 변수가 설정되었는지 확인합니다.

    Raises:
        EnvironmentError: 필수 환경 변수가 설정되지 않은 경우.
    """
    if not OPENAI_API_KEY:
        raise EnvironmentError("환경에 OPENAI_API_KEY가 설정되어 있지 않습니다.")

# 독립 실행 시 사용자 입력 처리
if __name__ == "__main__":
    try:
        check_env()
    except EnvironmentError as e:
        print(e)
        exit()

    while True:
        term = input("검색할 용어를 입력하세요 (종료: 'exit'): ").strip()
        if term.lower() == "exit":
            print("프로그램을 종료합니다.")
            break
        try:
            definition = search_definition(term)
            print(f"\n'{term}'에 대한 정의:\n{definition}")
        except Exception as e:
            print(f"오류 발생: {e}")


# import os
# import json
# from langchain_community.vectorstores import FAISS
# from langchain_community.embeddings import OpenAIEmbeddings
# from langchain_community.llms import OpenAI
# from langchain.prompts import PromptTemplate
# from langchain.chains import RetrievalQA
# from dotenv import load_dotenv

# # 환경 변수 로드
# load_dotenv()
# OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# # JSON 파일에서 용어집 데이터 로드
# def load_glossary(file_path="data/combined_keyvalue_form.json"):
#     if not os.path.exists(file_path):
#         raise FileNotFoundError(f"용어집 파일을 찾을 수 없습니다: {file_path}")
#     with open(file_path, "r", encoding="utf-8") as f:
#         glossary = json.load(f)
#     return glossary

# # LangChain QA 검색 시스템 초기화
# def initialize_retrieval_qa():
#     # 임베딩 모델 정의
#     embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)
    
#     # FAISS 인덱스 로드
#     vectorstore = FAISS.load_local("data/faiss_index", embeddings)

#     # 프롬프트 템플릿 정의
#     prompt = PromptTemplate(
#         template="당신은 Python 학습자를 위한 유용한 도우미입니다. 명확하고 간결한 답변을 제공하세요.\n\n질문: {question}\n답변:",
#         input_variables=["question"]
#     )
    
#     # RetrievalQA 체인 초기화
#     qa = RetrievalQA.from_chain_type(
#         llm=OpenAI(model="text-davinci-003", temperature=0.0, openai_api_key=OPENAI_API_KEY),
#         retriever=vectorstore.as_retriever(),
#         chain_type_kwargs={"prompt": prompt}
#     )
#     return qa

# # 용어집에서 정의 검색
# def get_glossary_definition(term):
#     qa = initialize_retrieval_qa()
#     response = qa.run(term)
#     return response

# # 환경 변수 확인
# def check_env():
#     if not OPENAI_API_KEY:
#         raise EnvironmentError("환경에 OPENAI_API_KEY가 설정되어 있지 않습니다.")
