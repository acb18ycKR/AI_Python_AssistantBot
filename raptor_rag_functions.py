import os
import numpy as np
import pandas as pd
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from langchain.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain.text_splitter import RecursiveCharacterTextSplitter
from sklearn.mixture import GaussianMixture
import umap
from langchain_community.document_loaders import PDFPlumberLoader

RANDOM_SEED = 42
DB_INDEX = "RAPTOR_DB"

# Embedding Initialization
embd = OpenAIEmbeddings(model="text-embedding-ada-002")

# Chat Model Initialization
model = ChatOpenAI(model="gpt-4o", temperature=0)

# PDF 로드 및 텍스트 분할
def load_and_split_pdf(pdf_path, chunk_size=1100, chunk_overlap=100):
    """
    PDF 문서를 로드하고 텍스트를 분할합니다.
    """
    try:
        loader = PDFPlumberLoader(pdf_path)
        docs = loader.load()
        print(f"✅ PDF에서 로드된 문서 타입: {type(docs)}")
        print(f"✅ PDF에서 로드된 문서 개수: {len(docs)}")
        
        for i, doc in enumerate(docs[:5]):  # 처음 5개 문서 타입과 내용을 출력
            print(f"🔍 문서 {i} 타입: {type(doc)}")
            print(f"🔍 문서 {i} 내용: {doc}")
        
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        split_docs = text_splitter.split_documents(docs)
        print(f"✅ 분할된 문서 개수: {len(split_docs)}")
        
        for i, split_doc in enumerate(split_docs[:5]):  # 분할된 문서 중 5개의 타입과 내용을 출력
            print(f"🔍 분할된 문서 {i} 타입: {type(split_doc)}")
            print(f"🔍 분할된 문서 {i} 내용: {split_doc}")
            
        return split_docs
    except Exception as e:
        raise ValueError(f"PDF 로드 및 분할 중 오류가 발생했습니다: {str(e)}")
    
# Global Clustering
def global_cluster_embeddings(embeddings, dim, n_neighbors=None, metric="cosine"):
    if n_neighbors is None:
        n_neighbors = int((len(embeddings) - 1) ** 0.5)
    return umap.UMAP(n_neighbors=n_neighbors, n_components=dim, metric=metric).fit_transform(embeddings)

# Perform Clustering
def perform_clustering(embeddings, dim, threshold):
    reduced_embeddings_global = global_cluster_embeddings(embeddings, dim)
    gm = GaussianMixture(n_components=5, random_state=RANDOM_SEED).fit(reduced_embeddings_global)
    probs = gm.predict_proba(reduced_embeddings_global)
    labels = [np.where(prob > threshold)[0].tolist() for prob in probs]
    return labels

# Embedding Texts
def embed_texts(texts):
    embeddings = embd.embed_documents(texts)
    return np.array(embeddings)

# Create Vectorstore
def create_vectorstore(documents):
    """
    Vectorstore를 생성합니다.
    """
    try:
        vectorstore = FAISS.from_documents(documents=documents, embedding=embd)
        if os.path.exists(DB_INDEX):
            # Pickle 역직렬화를 허용
            local_index = FAISS.load_local(DB_INDEX, embd, allow_dangerous_deserialization=True)
            local_index.merge_from(vectorstore)
            local_index.save_local(DB_INDEX)
        else:
            vectorstore.save_local(DB_INDEX)
        return vectorstore.as_retriever()
    except Exception as e:
        raise ValueError(f"벡터스토어 생성 중 오류가 발생했습니다: {str(e)}")


# RAG Chain Initialization
def create_raptor_rag_chain(vectorstore):
    prompt = ChatPromptTemplate.from_template(
        """너는 파이썬 용어 사전과 퀴즈 풀기 기능이 있는 AI 학습 비서 챗봇이야. """
    )
    return {
        "context": vectorstore | (lambda docs: "\n\n".join([doc.page_content for doc in docs])),
        "question": RunnablePassthrough()
    } | prompt | model | StrOutputParser()

# RAG 시스템 초기화
def initialize_raptor_rag_system(pdf_path):
    try:
        # 문서 로드 및 분할
        documents = load_and_split_pdf(pdf_path)
        
        # 텍스트 추출 및 확인
        texts = [doc.page_content for doc in documents]
        print(f"✅ 텍스트 추출 완료: {len(texts)} 개 문서")
        print(f"🔍 추출된 텍스트 샘플: {texts[:5]}")  # 추출된 텍스트 중 5개 출력

        # 벡터스토어 생성
        retriever = create_vectorstore(documents)  # 문서 리스트 전달
        print("✅ 벡터스토어 생성 완료")
        
        # RAG 체인 생성
        return create_raptor_rag_chain(retriever)
    except Exception as e:
        raise ValueError(f"RAPTOR RAG 시스템 초기화 중 오류가 발생했습니다: {str(e)}")

# RAG 시스템 초기화
def generate_raptor_rag_answer(question, rag_chain):
    try:
        return rag_chain.invoke(question)
    except Exception as e:
        return f"Error generating answer: {str(e)}" 