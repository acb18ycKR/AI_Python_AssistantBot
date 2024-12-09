import random
from utils import load_glossary, get_glossary_definition

# 용어집 데이터 로드
GLOSSARY_FILE = "data/combined_keyvalue_form.json"
GLOSSARY = load_glossary(GLOSSARY_FILE)

# 퀴즈 생성
def generate_quiz():
    # 용어와 해당 정의를 무작위로 선택
    term, definition = random.choice(list(GLOSSARY.items()))
    options = [definition]

    # 일부 잘못된 답변 추가
    while len(options) < 4:
        fake_term, fake_definition = random.choice(list(GLOSSARY.items()))
        if fake_definition not in options:
            options.append(fake_definition)
    
    # 보기 섞기
    random.shuffle(options)

    return {
        "term": term,
        "options": options,
        "correct_answer": definition
    }

# 퀴즈 진행
def take_quiz():
    quiz = generate_quiz()
    print(f"문제: '{quiz['term']}'의 의미는 무엇인가요?")
    for i, option in enumerate(quiz["options"], 1):
        print(f"{i}. {option}")

    # 사용자의 답변 받기
    answer = int(input("정답 번호를 입력하세요: "))
    if quiz["options"][answer - 1] == quiz["correct_answer"]:
        print("정답입니다!")
    else:
        print(f"오답입니다! 정답은: {quiz['correct_answer']}")

# 용어집 항목 검색
def glossary_lookup(term):
    response = get_glossary_definition(term)
    print(f"'{term}'에 대한 정의:\n{response}")
