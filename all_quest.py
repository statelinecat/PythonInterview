from app import app, db, Question

def print_all_questions():
    """
    Выводит все вопросы из базы данных в консоль.
    """
    with app.app_context():
        # Получаем все вопросы из базы данных
        questions = Question.query.all()

        if not questions:
            print("В базе данных нет вопросов.")
            return

        # Выводим каждый вопрос
        for i, question in enumerate(questions, start=1):
            print(f"Вопрос #{i}:")
            print(f"  Текст: {question.text}")
            print(f"  Варианты ответов:")
            print(f"    1. {question.option1}")
            print(f"    2. {question.option2}")
            print(f"    3. {question.option3}")
            print(f"    4. {question.option4}")
            print(f"  Правильный ответ: {question.correct_option}")
            print(f"  Объяснение: {question.explanation}")
            print(f"  Пример: {question.example or 'Нет примера'}")
            print("-" * 50)

if __name__ == '__main__':
    print_all_questions()