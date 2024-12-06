import os
import numpy as np
import openai  # openai 모듈을 임포트
from dotenv import load_dotenv

load_dotenv()
OPENAI_API_KEY = os.environ['OPENAI_API_KEY']


def get_embedding(text, model='text-embedding-ada-002'):  # 모델 이름 수정
    response = openai.Embedding.create(  # openai.Embedding.create()로 수정
        input=text,
        model=model,
        api_key=OPENAI_API_KEY  # API 키를 직접 전달
    )
    return response['data'][0]['embedding']  # 수정된 응답 형식에 맞춰 접근


def get_embeddings(text, model='text-embedding-ada-002'):  # 모델 이름 수정
    response = openai.Embedding.create(  # openai.Embedding.create()로 수정
        input=text,
        model=model,
        api_key=OPENAI_API_KEY  # API 키를 직접 전달
    )
    output = []
    for item in response['data']:  # 응답 형식에 맞춰 수정
        output.append(item['embedding'])
    return output


def cosine_similarity(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))


def call_openai(prompt, temperature=0.0, model='gpt-3.5-turbo'):
    response = openai.ChatCompletion.create(  # openai.ChatCompletion.create()로 수정
        model=model,
        messages=[{'role': 'user', 'content': prompt}],
        temperature=temperature,
        api_key=OPENAI_API_KEY  # API 키를 직접 전달
    )
    return response['choices'][0]['message']['content']


def retrieve_context(question):
    with open(r'C:\Users\RMARKET\Desktop\AI-SERVICE\assistant-question-answering\res\guidebook_full.txt', 'r', encoding='utf-8') as f:  # encoding='utf-8' 추가
        contexts = f.read().split('\n\n')

    # 질문과 문서 내용에 대한 임베딩 계산
    question_embedding = get_embeddings([question], model='text-embedding-ada-002')[0]
    context_embeddings = get_embeddings(contexts, model='text-embedding-ada-002')

    # 유사도 계산
    similarities = [cosine_similarity(question_embedding, context_embedding) for context_embedding in context_embeddings]

    # 가장 유사한 컨텍스트 선택
    most_relevant_index = np.argmax(similarities)
    print(contexts[most_relevant_index])  # 가장 관련성 높은 텍스트 출력
    return contexts[most_relevant_index]  # 가장 관련성 높은 텍스트 반환

