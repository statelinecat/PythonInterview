import logging
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
from app import app, db, Question, GameHistory  # Импортируем модели Question и GameHistory
import random
import html  # Для экранирования специальных символов
from datetime import datetime, UTC  # Импортируем UTC для timezone-aware времени
from dotenv import load_dotenv
import os

# Загружаем переменные окружения из .env
load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Настройка логирования
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("bot.log"),  # Логи будут записываться в файл bot.log
        logging.StreamHandler()         # Логи также будут выводиться в консоль
    ]
)
logger = logging.getLogger(__name__)

# Хранение состояния игры для каждого пользователя
user_states = {}

# Команда /start для начала викторины
async def start(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    username = update.message.from_user.username or update.message.from_user.first_name

    logger.info(f"Пользователь {username} (ID: {user_id}) запустил бота.")

    try:
        with app.app_context():
            all_questions = Question.query.all()
            logger.info(f"Найдено вопросов: {len(all_questions)}")
    except Exception as e:
        logger.error(f"Ошибка при загрузке вопросов: {str(e)}")
        await update.message.reply_text(f"Ошибка при загрузке вопросов: {str(e)}")
        return

    if len(all_questions) < 10:
        await update.message.reply_text("Недостаточно вопросов в базе данных для начала игры.")
        return

    selected_questions = random.sample(all_questions, 10)
    user_states[user_id] = {
        "questions": selected_questions,
        "current_index": 0,
        "score": 0,
        "username": username
    }

    await update.message.reply_text("<b>Добро пожаловать в викторину!</b>\nОтветьте на 10 вопросов.", parse_mode="HTML")
    await show_question(update, context)

# Показ текущего вопроса пользователю
async def show_question(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    state = user_states.get(user_id)

    if not state or state["current_index"] >= len(state["questions"]):
        await end_quiz(update, context)
        return

    question = state["questions"][state["current_index"]]
    options = [question.option1, question.option2, question.option3, question.option4]

    reply_markup = ReplyKeyboardMarkup(
        [[option] for option in options],
        one_time_keyboard=True,
        resize_keyboard=True
    )

    escaped_text = html.escape(question.text)

    await update.message.reply_text(
        f"<b>Вопрос #{state['current_index'] + 1}:</b>\n{escaped_text}",
        reply_markup=reply_markup,
        parse_mode="HTML"
    )

# Обработка ответа пользователя
async def handle_answer(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    state = user_states.get(user_id)

    if not state:
        await update.message.reply_text("Что-то пошло не так. Попробуйте начать заново (/start).")
        return

    user_answer = update.message.text
    current_question = state["questions"][state["current_index"]]

    correct_option = current_question.correct_option
    options = [current_question.option1, current_question.option2, current_question.option3, current_question.option4]
    is_correct = user_answer == options[correct_option - 1]

    result_message = "<b>✅ Правильно!</b>" if is_correct else "<b>❌ Неправильно.</b>"
    explanation = html.escape(current_question.explanation)
    example = html.escape(current_question.example or "Пример отсутствует.")

    if is_correct:
        state["score"] += 1

    await update.message.reply_text(
        f"{result_message}\n"
        f"Правильный ответ: <code>{html.escape(options[correct_option - 1])}</code>\n"
        f"Объяснение: {explanation}\n"
        f"Пример: <pre>{example}</pre>",
        parse_mode="HTML"
    )

    state["current_index"] += 1
    await show_question(update, context)

# Завершение викторины и показ результатов
async def end_quiz(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    state = user_states.pop(user_id, None)

    if not state:
        await update.message.reply_text("Викторина завершена. Начните новую игру (/start).")
        return

    score = state["score"]
    total_questions = len(state["questions"])
    username = state["username"]

    save_game_history(username, score, total_questions)

    await update.message.reply_text(
        f"🎉 <b>Викторина завершена!</b>\n"
        f"Правильных ответов: <code>{score}/{total_questions}</code>\n"
        f"Попробуйте снова (/start).",
        parse_mode="HTML"
    )

# Сохранение результатов игры в базу данных
def save_game_history(username, score, total_questions):
    with app.app_context():
        history = GameHistory(
            username=username,
            score=score,
            total_questions=total_questions,
            date=datetime.now(UTC)  # Timezone-aware время
        )
        db.session.add(history)
        db.session.commit()

# Команда /history для просмотра истории игр
async def history(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    username = update.message.from_user.username or update.message.from_user.first_name

    with app.app_context():
        user_history = GameHistory.query.filter_by(username=username).order_by(GameHistory.date.desc()).all()

    if not user_history:
        await update.message.reply_text("У вас еще нет истории игр. Начните новую игру (/start).")
        return

    best_score = max(entry.score for entry in user_history)
    total_games = len(user_history)

    history_message = f"<b>📊 История игр:</b>\n"
    history_message += f"Всего игр: <code>{total_games}</code>\n"
    history_message += f"Лучший результат: <code>{best_score}</code>\n\n"

    for entry in user_history:
        escaped_date = html.escape(entry.date.strftime('%Y-%m-%d %H:%M'))
        escaped_result = html.escape(f"{entry.score}/{entry.total_questions}")

        history_message += (
            f"Дата: <code>{escaped_date}</code>\n"
            f"Результат: <code>{escaped_result}</code>\n"
            f"{'-' * 20}\n"
        )

    await update.message.reply_text(history_message, parse_mode="HTML")

# Основная функция для запуска бота
def main():
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("history", history))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_answer))

    application.run_polling()

if __name__ == "__main__":
    main()