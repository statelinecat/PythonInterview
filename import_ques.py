from app import app, db, Question
import json
import os

def import_questions_from_folder(folder_path):
    """
    Импортирует вопросы из всех JSON-файлов в указанной папке.
    :param folder_path: Путь к папке с JSON-файлами.
    """
    with app.app_context():
        # Проверяем, существует ли указанная папка
        if not os.path.exists(folder_path):
            print(f"Ошибка: Папка '{folder_path}' не существует.")
            return

        # Получаем список всех файлов в указанной папке
        json_files = [f for f in os.listdir(folder_path) if f.endswith('.json')]

        if not json_files:
            print(f"Ошибка: В папке '{folder_path}' нет JSON-файлов.")
            return

        total_questions_imported = 0

        for json_file in json_files:
            file_path = os.path.join(folder_path, json_file)
            print(f"Обработка файла: {file_path}")

            try:
                # Читаем данные из JSON-файла
                with open(file_path, 'r', encoding='utf-8') as f:
                    questions = json.load(f)

                # Добавляем вопросы в базу данных
                for q in questions:
                    new_q = Question(
                        text=q['text'],
                        option1=q['options'][0],
                        option2=q['options'][1],
                        option3=q['options'][2],
                        option4=q['options'][3],
                        correct_option=q['correct'] + 1,  # Преобразуем индекс в 1-based
                        explanation=q['explanation'],
                        example=q.get('example', '')  # Пример может отсутствовать
                    )
                    db.session.add(new_q)

                total_questions_imported += len(questions)
                print(f"Из файла {json_file} импортировано {len(questions)} вопросов.")

            except Exception as e:
                print(f"Ошибка при обработке файла {json_file}: {e}")

        # Сохраняем изменения в базе данных
        db.session.commit()
        print(f"Всего импортировано {total_questions_imported} вопросов из {len(json_files)} файлов.")

if __name__ == '__main__':
    # Укажите путь к папке с JSON-файлами
    folder_path = r'D:\Stateline\Documents\GitHub\PythonInterview'  # Укажите реальный путь
    import_questions_from_folder(folder_path)