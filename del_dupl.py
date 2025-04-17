from app import app, db, Question

def remove_duplicate_questions():
    """
    Удаляет дубликаты вопросов из базы данных, оставляя только уникальные.
    Дубликаты определяются по полю 'text'.
    """
    with app.app_context():
        # Получаем все вопросы из базы данных
        questions = Question.query.all()

        if not questions:
            print("В базе данных нет вопросов.")
            return

        # Словарь для хранения уникальных вопросов
        unique_questions = {}
        duplicates_removed = 0

        for question in questions:
            # Используем текст вопроса как ключ для проверки уникальности
            if question.text not in unique_questions:
                unique_questions[question.text] = question
            else:
                # Если вопрос уже существует, удаляем его из базы данных
                db.session.delete(question)
                duplicates_removed += 1

        # Сохраняем изменения в базе данных
        db.session.commit()

        print(f"Удалено дубликатов: {duplicates_removed}")
        print(f"Осталось уникальных вопросов: {len(unique_questions)}")

if __name__ == '__main__':
    remove_duplicate_questions()