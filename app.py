import logging
import psycopg2
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters

# Настройка логирования
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)


# Настройка подключения к базе данных
def get_db_connection():
    return psycopg2.connect(
        dbname='dataofuser',
        user='postgres',
        password='1357',
        host='localhost',
        port='5432'
    )


# Функция записи команды в базу данных
def log_command(user_id, command):
    conn = get_db_connection()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO command_stats (user_id, command) VALUES (%s, %s)",
                (user_id, command)
            )


# Функция добавления сообщения пользователя в базу данных
def add_user_message(user_id, message_id, message_text):
    conn = get_db_connection()
    try:
        with conn:
            with conn.cursor() as cursor:
                print(
                    f"Attempting to insert MessageID: {message_id}, UserID: {user_id}, MessageText: {message_text}")  # Логирование
                cursor.execute(
                    "INSERT INTO UserMessages (MessageID, user_id, MessageText) VALUES (%s, %s, %s)",
                    (message_id, user_id, message_text)
                )
    except Exception as e:
        print(f"Error inserting message: {e}")


# Функция для добавления пользователя в базу данных
def add_user(user_id, username, first_name, last_name):
    conn = get_db_connection()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO users (user_id, username, first_name, last_name) VALUES (%s, %s, %s, %s) ON CONFLICT (user_id) DO NOTHING",
                (user_id, username, first_name, last_name)
            )


async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    conn = get_db_connection()

    with conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT command FROM command_stats WHERE user_id = %s", (user_id,))
            commands = cursor.fetchall()

            cursor.execute("SELECT MessageText, sentat FROM UserMessages WHERE user_id = %s", (user_id,))
            messages = cursor.fetchall()

    stats_message = "Ваши статистические данные:\n\n"
    stats_message += "Использованные команды:\n"

    if commands:
        for command in commands:
            stats_message += f"{command[0]}\n"  # Извлекаем первую часть кортежа
    else:
        stats_message += "Нет использованных команд.\n"

    stats_message += "\nОтправленные сообщения:\n"

    for text, created_at in messages:
        stats_message += f"{text} (отправлено: {created_at})\n"

    await update.message.reply_text(stats_message)


# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    add_user(user.id, user.username, user.first_name, user.last_name)
    log_command(user.id, '/start')


    # Создание кнопок для меню
    keyboard = [
        ["/start", "/help"],
        ["/about"],
        ["/stats"]  # Кнопка для статистики
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    await update.message.reply_text('Добро пожаловать ☆*:.｡.o(≧▽≦)o.｡.:*☆ Выберите команду!:', reply_markup=reply_markup)



# Команда /help
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    log_command(user.id, '/help')
    await update.message.reply_text('Вам нужна помощь в работе с ботов? Нажмите на /start, и бот начнет свою работу.')


# Команда /about
async def about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    log_command(user.id, '/about')
    await update.message.reply_text('Этот бот собирает статистику о пользователях. Если хотите узнать, что вы писали, во сколько вы это делали, то нажмите /stats')


# Обработка текстовых сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    add_user_message(user.id, update.message.message_id, update.message.text)


# Основная функция для запуска бота
def main():
    app = ApplicationBuilder().token('7930914754:AAGGuWzdJQHezBtYMxuA4UNNtCCpVRm61y4').build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("about", about))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("Работаем!")
    app.run_polling()


if __name__ == '__main__':
    main()
