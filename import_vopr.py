from app import app, db, Question
import json

def import_questions():
    with app.app_context():
        with open('questions1.json', 'r', encoding='utf-8') as f:
            questions = json.load(f)

        for q in questions:
            new_q = Question(
                text=q['text'],
                option1=q['options'][0],
                option2=q['options'][1],
                option3=q['options'][2],
                option4=q['options'][3],
                correct_option=q['correct'] + 1,
                explanation=q['explanation'],
                example=q.get('example', '')
            )
            db.session.add(new_q)

        db.session.commit()
        print(f"Импортировано {len(questions)} вопросов")

if __name__ == '__main__':
    import_questions()