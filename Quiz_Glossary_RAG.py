# 환경 변수 불러오기
from dotenv import load_dotenv
load_dotenv()

# 필요한 모듈 및 클래스 임포트
from langchain_community.document_loaders import JSONLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import FAISS
from langchain.prompts import PromptTemplate
from langchain.chains import RetrievalQA
from langchain_community.vectorstores import FAISS
from langchain_community.llms import OpenAI 
from ragas import TestsetGenerator  
from ragas.llms import LangchainLLMWrapper
from ragas.embeddings import LangchainEmbeddingsWrapper
from ragas.testset.extractor import KeyphraseExtractor
from ragas.testset.docstore import InMemoryDocumentStore
from ragas.metrics import context_recall, faithfulness, answer_relevancy, context_precision
from ragas import evaluate
import pandas as pd
import ast

# 데이터 로드
data_path = "data/combined_keyvalue_form.json"
loader = JSONLoader(data_path, json_key="data")
docs = loader.load()

# 텍스트 분할
splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
split_documents = splitter.split_documents(docs)

# 임베딩 모델 설정
embeddings = OpenAIEmbeddings()
faiss_embeddings = LangchainEmbeddingsWrapper(embeddings)

# 벡터 저장소 생성
vectorstore = FAISS.from_documents(split_documents, embeddings=embeddings)
retriever = vectorstore.as_retriever()

# 프롬프트 템플릿 생성
prompt_template = PromptTemplate.from_template(
    """
    너는 용어집 챗봇이야. 다음 문맥(Context)을 참고하여 질문(Question)에 답을 제공해줘.
    답을 모르면 '알 수 없습니다'라고 대답해줘.

    Context: {context}
    Question: {question}
    Answer:
    """
)

# LLM 설정
llm = OpenAI(model="gpt-4o", temperature=0)

# QA Chain 생성
qa_chain = RetrievalQA.from_chain_type(
    llm=llm, chain_type="stuff", retriever=retriever, return_source_documents=True, prompt=prompt_template
)

# 테스트 데이터셋 생성 및 문서 저장소 설정
generator_llm = LangchainLLMWrapper(OpenAI(model="gpt-4o"))
critic_llm = LangchainLLMWrapper(OpenAI(model="gpt-4o"))
keyphrase_extractor = KeyphraseExtractor(llm=generator_llm)
docstore = InMemoryDocumentStore(splitter=splitter, embeddings=faiss_embeddings, extractor=keyphrase_extractor)

# 생성기 초기화
generator = TestsetGenerator.from_langchain(
    generator_llm=generator_llm,
    critic_llm=critic_llm,
    embeddings=faiss_embeddings,
    docstore=docstore
)

distributions = {"simple": 0.4, "reasoning": 0.2, "multi_context": 0.2, "conditional": 0.2}

testset = generator.generate_with_langchain_docs(
    documents=docs,
    test_size=10,
    distributions=distributions,
    with_debugging_logs=True,
    raise_exceptions=False
)

# 테스트 데이터셋을 DataFrame으로 변환
test_df = testset.to_pandas()
test_df.to_csv("data/ragas_testset.csv", index=False)

# 테스트셋 로드 및 변환
df = pd.read_csv("data/ragas_testset.csv")
test_dataset = Dataset.from_pandas(df)
def convert_to_list(example):
    contexts = ast.literal_eval(example['contexts'])
    return {'contexts': contexts}
test_dataset = test_dataset.map(convert_to_list)

# QA 실행
questions = test_dataset['question']
answers = [qa_chain.run({"context": context, "question": question}) for context, question in zip(test_dataset['contexts'], questions)]

test_dataset = test_dataset.add_column("answer", answers)

# RAG 평가
metrics = [answer_relevancy, faithfulness, context_recall, context_precision]
result = evaluate(dataset=test_dataset, metrics=metrics)
result_df = result.to_pandas()

# 결과 저장
result_df.to_csv("data/ragas_evaluation.csv", index=False)

print("평가 완료. 결과는 'data/ragas_evaluation.csv'에 저장되었습니다.")
