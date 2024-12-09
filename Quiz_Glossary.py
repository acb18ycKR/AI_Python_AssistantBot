import os
import numpy as np
import openai  # openai 모듈을 임포트
from dotenv import load_dotenv
import json

# .env 파일 로드
load_dotenv()
OPENAI_API_KEY = os.environ['OPENAI_API_KEY']

# OpenAI API 초기화
openai.api_key = OPENAI_API_KEY

# 임베딩 생성 함수
def get_embedding(text, model='text-embedding-ada-002'):
    response = openai.Embedding.create(
        input=text,
        model=model,
        api_key=OPENAI_API_KEY
    )
    return response['data'][0]['embedding']

def get_embeddings(texts, model='text-embedding-ada-002'):
    response = openai.Embedding.create(
        input=texts,
        model=model,
        api_key=OPENAI_API_KEY
    )
    return [item['embedding'] for item in response['data']]

# 코사인 유사도 계산 함수
def cosine_similarity(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

# OpenAI API를 사용하여 응답 생성 함수
def call_openai(prompt, temperature=0.0, model='gpt-3.5-turbo'):
    response = openai.ChatCompletion.create(
        model=model,
        messages=[{'role': 'user', 'content': prompt}],
        temperature=temperature,
        api_key=OPENAI_API_KEY
    )
    return response['choices'][0]['message']['content']

# 가장 관련성 높은 컨텍스트 검색 함수
def retrieve_context(question, contexts, context_embeddings):
    question_embedding = get_embedding(question)
    similarities = [cosine_similarity(question_embedding, context_embedding) for context_embedding in context_embeddings]
    most_relevant_index = np.argmax(similarities)
    return contexts[most_relevant_index]

# 용어 사전 생성 함수
def load_glossary(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        glossary = json.load(f)
    return glossary

# 용어 설명 함수
def explain_term(term, glossary):
    if term in glossary:
        return glossary[term]
    else:
        return f"용어 '{term}'는 사전에 없습니다."

# 퀴즈 생성 함수
def generate_quiz(glossary, num_questions=5):
    terms = list(glossary.keys())
    np.random.shuffle(terms)
    quiz = []
    for term in terms[:num_questions]:
        question = f"다음 용어의 정의는 무엇인가요? '{term}'"
        answer = glossary[term]
        quiz.append({"question": question, "answer": answer})
    return quiz

# 퀴즈 테스트 함수
def test_quiz(quiz):
    score = 0
    for q in quiz:
        print(q["question"])
        user_answer = input("답변: ")
        if user_answer.strip().lower() == q["answer"].strip().lower():
            print("정답입니다!")
            score += 1
        else:
            print(f"틀렸습니다. 정답은: {q['answer']}")
    print(f"테스트 완료! 점수: {score}/{len(quiz)}")

# 메인 챗봇 함수
def chatbot():
    # 데이터 로드
    with open(r'C:\Users\RMARKET\Desktop\AI-SERVICE\assistant-question-answering\res\guidebook_full.txt', 'r', encoding='utf-8') as f:
        contexts = f.read().split('\n\n')
    context_embeddings = get_embeddings(contexts)

    # 용어 사전 로드
    glossary = load_glossary(r'C:\Users\RMARKET\Desktop\AI-SERVICE\assistant-question-answering\res\glossary.json')

    while True:
        user_input = input("You: ")
        if user_input.lower() in ['exit', 'quit', '종료', '나가기']:
            print("Goodbye!")
            break

        if user_input.startswith("용어 "):
            term = user_input.split(" ", 1)[1]
            explanation = explain_term(term, glossary)
            print(f"Bot: {explanation}")

        elif user_input.startswith("퀴즈 "):
            num_questions = int(user_input.split(" ", 1)[1]) if " " in user_input else 5
            quiz = generate_quiz(glossary, num_questions)
            test_quiz(quiz)

        else:
            # 가장 관련성 높은 컨텍스트 검색
            context = retrieve_context(user_input, contexts, context_embeddings)
            # 컨텍스트와 함께 질문을 OpenAI API에 전달
            prompt = f"Context: {context}\nQuestion: {user_input}"
            response = call_openai(prompt)
            print(f"Bot: {response}")

# 챗봇 실행
chatbot()