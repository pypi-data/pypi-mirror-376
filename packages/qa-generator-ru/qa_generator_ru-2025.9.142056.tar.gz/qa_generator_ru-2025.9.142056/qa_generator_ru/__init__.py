import json
import random

def generate_qa_pairs_ru():
    """
    Generates 2-3 thousand question-answer pairs in Russian.

    The function uses a predefined set of prompts and potential answers
    to create diverse question-answer combinations.

    Returns:
        list: A list of dictionaries, where each dictionary represents a
              question-answer pair with 'question' and 'answer' keys.
    """
    prompts = [
        "Что такое",
        "Объясни, как работает",
        "Каковы основные преимущества",
        "В чем разница между",
        "Приведи пример",
        "Как решить проблему",
        "Почему важно",
        "Опиши процесс",
        "Какие существуют типы",
        "Как использовать"
    ]

    subjects = [
        "Python", "машинное обучение", "глубокое обучение", "нейронные сети",
        "обработка естественного языка", "компьютерное зрение", "анализ данных",
        "облачные вычисления", "веб-разработка", "базы данных", "алгоритмы",
        "структуры данных", "операционные системы", "компьютерные сети",
        "кибербезопасность", "разработка игр", "мобильная разработка",
        "блокчейн", "криптовалюты", "искусственный интеллект"
    ]

    details = [
        "в контексте вашего проекта", "для начинающих", "на практике",
        "с точки зрения производительности", "с точки зрения масштабируемости",
        "и его применение", "и его влияние на индустрию", "и его будущее",
        "в современном мире", "для решения реальных задач"
    ]

    answers = [
        "Это сложная, но интересная тема, требующая глубокого понимания.",
        "Ключевым моментом является понимание базовых принципов и практика.",
        "Существует множество ресурсов для изучения, включая онлайн-курсы и книги.",
        "Важно применять полученные знания на практике для закрепления.",
        "Эффективное решение зависит от контекста и конкретных требований.",
        "Детали реализации могут варьироваться, но общая концепция остается неизменной.",
        "Это динамично развивающаяся область с большим потенциалом.",
        "Практическое применение часто требует адаптации теоретических знаний.",
        "Ключ к успеху - постоянное обучение и эксперименты.",
        "В конечном итоге, понимание приходит через практику и осмысление."
    ]

    qa_pairs = []
    num_pairs = random.randint(2000, 3000)

    for _ in range(num_pairs):
        prompt_template = random.choice(prompts)
        subject = random.choice(subjects)
        detail = random.choice(details)
        answer_template = random.choice(answers)

        question = f"{prompt_template} {subject} {detail}?"
        answer = f"{answer_template} {subject.capitalize()} - это важно."

        qa_pairs.append({"question": question, "answer": answer})

    return qa_pairs

if __name__ == '__main__':
    # Example of how to use the function within the module itself if run directly
    # In a real package, this part would typically not be in __init__.py
    # but for this minimal example, it's included for self-containment.
    generated_qas = generate_qa_pairs_ru()
    print(f"Generated {len(generated_qas)} QA pairs.")
    # print(json.dumps(generated_qas[:5], indent=2, ensure_ascii=False)) # uncomment to see a sample