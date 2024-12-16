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
def load_and_split_pdf(pdf_path, chunk_size=1000, chunk_overlap=100):
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
            local_index = FAISS.load_local(DB_INDEX, embd)
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
        """You are an expert at summarizing complex information. Use the given context to answer the question.
        Context: {context}
        Question: {question}
        Answer:"""
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
    
# RAG 성능 테스트 함수
def ragas_test(question, answer, retrieved_context):
    """
    질문, 답변, 검색된 컨텍스트를 기반으로 성능 평가를 실행합니다.
    Args:
        question (str): 질문
        answer (str): 모델의 답변
        retrieved_context (list): 검색된 컨텍스트
    Returns:
        dict: 평가 결과
    """
    # 데이터셋 생성
    dataset = [{
        "question": question,
        "answer": answer,
        "retrieved_context": "\n\n".join(retrieved_context)
    }]

    # 평가 지표 정의
    def answer_relevancy(dataset):
        relevancies = [1 if d["answer"] in d["retrieved_context"] else 0 for d in dataset]
        return sum(relevancies) / len(relevancies)

    def faithfulness(dataset):
        faithfulness_scores = [1 if d["answer"] == d["retrieved_context"] else 0 for d in dataset]
        return sum(faithfulness_scores) / len(faithfulness_scores)

    def context_recall(dataset):
        recalls = [1 if d["answer"] in d["retrieved_context"] else 0 for d in dataset]
        return sum(recalls) / len(recalls)

    def context_precision(dataset):
        precisions = [1 if d["answer"] in d["retrieved_context"] else 0 for d in dataset]
        return sum(precisions) / len(precisions)

    # 평가 실행
    metrics = [
        answer_relevancy,
        faithfulness,
        context_recall,
        context_precision
    ]
    results = {metric.__name__: metric(dataset) for metric in metrics}
    return results

# 테스트 실행
if __name__ == "__main__":
    # 예시 데이터
    question = "파이썬의 for문의 정의를 알려줘"
    answer = "for문은 반복문으로, 리스트나 튜플 등의 항목을 반복적으로 실행할 수 있게 한다."
    retrieved_context = [
        "for문은 반복문으로, 리스트나 튜플 등의 항목을 반복적으로 실행할 수 있게 한다.",
        "파이썬의 반복문에는 for문과 while문이 있다."
    ]
    
    # RAG 성능 평가 실행
    result = ragas_test(question, answer, retrieved_context)
    print("RAG 성능 평가 결과:", result)
