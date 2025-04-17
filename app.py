from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, UTC  # Импортируем UTC для timezone-aware времени
import random

# Настройка приложения Flask
app = Flask(__name__)
app.secret_key = 'your_secret_key_here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///quiz.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


# Модель вопроса
class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(500), nullable=False)
    option1 = db.Column(db.String(200), nullable=False)
    option2 = db.Column(db.String(200), nullable=False)
    option3 = db.Column(db.String(200), nullable=False)
    option4 = db.Column(db.String(200), nullable=False)
    correct_option = db.Column(db.Integer, nullable=False)  # Индекс правильного ответа (1-based)
    explanation = db.Column(db.Text, nullable=False)
    example = db.Column(db.Text)  # Пример может отсутствовать


# Модель истории игр
class GameHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False)
    score = db.Column(db.Integer, nullable=False)
    total_questions = db.Column(db.Integer, nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(UTC))  # Timezone-aware время


# Создание таблиц в базе данных
with app.app_context():
    db.create_all()


# Главная страница
@app.route('/')
def index():
    session.clear()  # Очищаем сессию при переходе на главную страницу
    return render_template('index.html')


# Начало викторины
@app.route('/start_quiz', methods=['POST'])
def start_quiz():
    session['username'] = request.form['username']
    session['score'] = 0

    # Получаем все доступные вопросы из базы данных
    all_question_ids = [q.id for q in Question.query.all()]

    # Проверяем, что в базе данных достаточно вопросов для формирования набора из 10
    if len(all_question_ids) < 10:
        return "Недостаточно вопросов в базе данных для начала игры."

    # Выбираем случайным образом 10 уникальных вопросов
    selected_question_ids = random.sample(all_question_ids, 10)
    session['question_ids'] = selected_question_ids
    session['current_question_index'] = 0

    return redirect(url_for('show_question'))


# Показ текущего вопроса
@app.route('/quiz')
def show_question():
    if 'question_ids' not in session:
        return redirect(url_for('index'))

    question_index = session['current_question_index']
    if question_index >= len(session['question_ids']):
        return redirect(url_for('show_results'))

    question_id = session['question_ids'][question_index]
    question = Question.query.get(question_id)

    return render_template(
        'quiz.html',
        question=question,
        question_num=question_index + 1,
        total_questions=len(session['question_ids'])
    )


# Обработка ответа пользователя
@app.route('/submit_answer', methods=['POST'])
def submit_answer():
    question_id = session['question_ids'][session['current_question_index']]
    question = Question.query.get(question_id)

    selected_option = int(request.form['option'])
    is_correct = selected_option == question.correct_option

    if is_correct:
        session['score'] += 1

    # Сохраняем данные о последнем вопросе в сессии
    session['last_question'] = {
        'text': question.text,
        'selected': selected_option,
        'correct': question.correct_option,
        'explanation': question.explanation,
        'example': question.example,
        'is_correct': is_correct,
        'options': [
            question.option1,
            question.option2,
            question.option3,
            question.option4
        ]
    }

    session['current_question_index'] += 1
    return redirect(url_for('show_explanation'))


# Показ объяснения к ответу
@app.route('/explanation')
def show_explanation():
    if 'last_question' not in session:
        return redirect(url_for('index'))

    return render_template(
        'explanation.html',
        question=session['last_question'],
        question_num=session['current_question_index'],
        total_questions=len(session['question_ids'])
    )


# Переход к следующему вопросу
@app.route('/next_question')
def next_question():
    if session['current_question_index'] >= len(session['question_ids']):
        return redirect(url_for('show_results'))
    return redirect(url_for('show_question'))


# Показ результатов
@app.route('/results')
def show_results():
    if 'username' not in session:
        return redirect(url_for('index'))

    # Сохраняем результаты игры в базу данных
    history = GameHistory(
        username=session['username'],
        score=session['score'],
        total_questions=len(session['question_ids']),
        date=datetime.now(UTC)  # Timezone-aware время
    )
    db.session.add(history)
    db.session.commit()

    # Получаем историю игр пользователя
    user_history = GameHistory.query.filter_by(username=session['username']).order_by(GameHistory.date.desc()).all()
    session.clear()  # Очищаем сессию после завершения игры

    return render_template(
        'results.html',
        score=history.score,
        total_questions=history.total_questions,
        history=user_history
    )


if __name__ == '__main__':
    app.run(debug=True)