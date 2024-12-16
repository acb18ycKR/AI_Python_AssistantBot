from langchain_community.document_loaders import PDFPlumberLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

# PDF 로드 및 텍스트 분할
def load_and_split_pdf(pdf_path, chunk_size=1100, chunk_overlap=100):
    try:
        loader = PDFPlumberLoader(pdf_path)
        docs = loader.load()
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        return text_splitter.split_documents(docs)
    except Exception as e:
        raise ValueError(f"PDF 로드 및 분할 중 오류가 발생했습니다: {str(e)}")

# 임베딩 모델 생성
def create_embeddings():
    return OpenAIEmbeddings()

# 벡터 저장소 생성
def create_vector_store(documents, embeddings):
    try:
        return FAISS.from_documents(documents=documents, embedding=embeddings)
    except Exception as e:
        raise ValueError(f"벡터 저장소 생성 중 오류가 발생했습니다: {str(e)}")

# RAG 체인 생성
def create_rag_chain(vectorstore):
    retriever = vectorstore.as_retriever()
    prompt = PromptTemplate.from_template(
        """너는 용어 사전에 대한 전문가야. 다음 검색된 context를 사용해서 질문에 맞는 용어를 정의해줘.
        답을 모르면, '알 수 없습니다.'라고 대답해.

        # Context : {context}
        # Question : {question}
        # Answer :
        """
    )
    llm = ChatOpenAI(model='gpt-4o-mini', temperature=0)
    return (
        {'context': retriever, 'question': RunnablePassthrough()}  
        | prompt  
        | llm  
        | StrOutputParser()  
    )

# 질문에 대한 답변 생성
def generate_rag_answer(question, rag_chain):
    try:
        return rag_chain.invoke(question)
    except Exception as e:
        return f"오류가 발생했습니다: {str(e)}"

# PDF 문서 기반 RAG 시스템 초기화
def initialize_rag_system(pdf_path):
    try:
        documents = load_and_split_pdf(pdf_path)
        embeddings = create_embeddings()
        vectorstore = create_vector_store(documents, embeddings)
        return create_rag_chain(vectorstore)
    except Exception as e:
        raise ValueError(f"RAG 시스템 초기화 중 오류가 발생했습니다: {str(e)}")


