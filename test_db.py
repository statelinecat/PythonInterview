from app import app, db, Question

# Проверяем, что контекст Flask работает корректно
with app.app_context():
    all_questions = Question.query.all()
    print(f"Найдено вопросов: {len(all_questions)}")
    for question in all_questions:
        print(f"ID: {question.id}, Text: {question.text}")