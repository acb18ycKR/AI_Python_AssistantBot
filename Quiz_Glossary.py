import random
from utils import load_glossary, get_glossary_definition

# Load glossary data
GLOSSARY_FILE = "data/combined_keyvalue_form.json"
GLOSSARY = load_glossary(GLOSSARY_FILE)

# Quiz generation
def generate_quiz():
    # Randomly select a term and its definition
    term, definition = random.choice(list(GLOSSARY.items()))
    options = [definition]

    # Add some fake answers
    while len(options) < 4:
        fake_term, fake_definition = random.choice(list(GLOSSARY.items()))
        if fake_definition not in options:
            options.append(fake_definition)
    
    # Shuffle the options
    random.shuffle(options)

    return {
        "term": term,
        "options": options,
        "correct_answer": definition
    }

# Quiz interaction
def take_quiz():
    quiz = generate_quiz()
    print(f"Question: What does '{quiz['term']}' mean?")
    for i, option in enumerate(quiz["options"], 1):
        print(f"{i}. {option}")

    # Get user's answer
    answer = int(input("Enter the number of your answer: "))
    if quiz["options"][answer - 1] == quiz["correct_answer"]:
        print("Correct!")
    else:
        print(f"Wrong! The correct answer was: {quiz['correct_answer']}")

# Retrieve glossary entry
def glossary_lookup(term):
    response = get_glossary_definition(term)
    print(f"Definition for '{term}':\n{response}")
