import json
import logging
import random

from dbHandler import DBHandler
from convDBHandler import ConvDBHandler

try:
    from telegram import __version_info__
except ImportError:
    __version_info__ = (0, 0, 0, 0, 0)  # type: ignore[assignment]

from telegram import (
    ReplyKeyboardMarkup,
    Update
)
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
    ConversationHandler, PicklePersistence
)

logger = logging.getLogger(__name__)
theory = dict()
topic_to_id = dict()
questions = dict()
MENU, THEORY, QUIZ = range(3)
options = 'ABCD'
db_handler = DBHandler('results.db')
conv_db_handler = ConvDBHandler('conv.db')


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Inform user about what this bot can do"""
    await conv_db_handler.create_table()
    await db_handler.create_table()
    user = update.message.from_user
    logger.info('''
        User_id: {}
        Username: {}
    '''.format(user.id, user.username))
    await conv_db_handler.insert_user({'user_id': user.id})
    await update.message.reply_text('Чтобы перейти к темам нажмите /choose_theory.')
    return THEORY


async def choose_theory(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Choosing a topic"""
    keyboard = []
    for topic in theory.keys():
        keyboard.append([topic])
    await update.message.reply_text(
        'Пожалуйста, выберете тему, которую вы хотите пройти.', reply_markup=ReplyKeyboardMarkup(
            keyboard,
            one_time_keyboard=True)
    )
    return THEORY


async def print_theory(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Getting information about chosen topic"""
    global current_topic
    user_id = str(update.message.from_user.id)
    cur_topic = update.message.text
    await update_user_info(
        user_id, cur_topic,
        cur_set_of_questions=json.dumps(
            {user_id: random.sample(questions[cur_topic], min(len(questions[cur_topic]), 5))}
        )
    )
    logger.info('Current topic for {} is {}'.format(update.message.from_user.username, cur_topic))
    message = theory[cur_topic]
    keyboard = [[
        'Тестирование',
        'Пропустить тест'
    ]]
    await update.message.reply_text(message, reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True))

    return QUIZ


async def quiz(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Quiz with questions from json file"""
    user_id = str(update.message.from_user.id)
    user_info = await conv_db_handler.get_user_info({'user_id': user_id})
    cur_topic = user_info[1]
    cur_question = user_info[2]
    cur_set_of_questions = json.loads(user_info[3])
    quiz_result = user_info[4]
    keyboard = []
    n = len(cur_set_of_questions[user_id][cur_question]['options'])  # Количество ответов
    m = 2  # Количество ответов на одной строке
    cur_set_of_questions[user_id][cur_question]['options'] = \
        random.sample(cur_set_of_questions[user_id][cur_question]['options'], n)
    for idx, question in enumerate(cur_set_of_questions[user_id][cur_question]['options']):
        keyboard.append('{}. {}'.format(chr(ord('A') + idx), question['text']))
    keyboard = keyboard_separation(keyboard, n, m)
    keyboard.append(['Выход'])
    await update_user_info(
        user_id,
        cur_topic=cur_topic,
        cur_question=cur_question,
        cur_set_of_questions=json.dumps(cur_set_of_questions),
        quiz_result=quiz_result
    )
    await update.message.reply_text(cur_set_of_questions[user_id][cur_question]['text'],
                                    reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True))
    return QUIZ


async def update_user_info(user_id, cur_topic='', cur_question=0, cur_set_of_questions='{}', quiz_result=0):
    await conv_db_handler.update_cur_topic({'user_id': user_id, 'current_topic': cur_topic})
    await conv_db_handler.update_cur_question({'user_id': user_id, 'current_question': cur_question})
    await conv_db_handler.update_quiz_result({'user_id': user_id, 'quiz_result': quiz_result})
    await conv_db_handler.update_cur_set_of_question(
        {
            'user_id':
                user_id,
            'current_set_of_questions':
                cur_set_of_questions
        }
    )


def to_digit(char):
    return ord(char) - ord('A')


async def check_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Check quiz result"""
    answer = to_digit(update.message.text[0])
    user_id = str(update.message.from_user.id)
    logger.info('{} chose answer {}'.format(update.message.from_user.username, answer))
    user_info = await conv_db_handler.get_user_info({'user_id': user_id})
    cur_topic = user_info[1]
    cur_topic_id = topic_to_id[cur_topic]
    cur_question = user_info[2]
    quiz_result = user_info[4]
    cur_set_of_questions = json.loads(user_info[3])
    keyboard = [['К следующему вопросу']]
    end_keyboard = [['К темам']]
    if cur_set_of_questions[user_id][cur_question]['options'][answer]['is_correct']:
        reply_text = 'Верно✅. {}'.format(cur_set_of_questions[user_id][cur_question].get('description', ''))
        quiz_result += 1
    else:
        reply_text = 'Неверно❌. {}'.format(cur_set_of_questions[user_id][cur_question].get('description', ''))
    if cur_question == len(cur_set_of_questions[user_id]) - 1:
        await update.message.reply_text(reply_text,
                                        reply_markup=ReplyKeyboardMarkup(end_keyboard, one_time_keyboard=True))
        cur_question = 0
        result = quiz_result
        await save_result_to_db({
            'user_id': user_id,
            'test_id': cur_topic_id,
            'result': result,
            'questions_amount': min(len(questions[cur_topic]), 5)
        })
        await update.message.reply_text('Вы набрали {}/{} баллов.'.format(result, min(len(questions[cur_topic]), 5)))
        await update_user_info(user_id)
        return THEORY
    await update_user_info(
        user_id,
        cur_topic=cur_topic,
        cur_question=cur_question + 1,
        cur_set_of_questions=json.dumps(cur_set_of_questions),
        quiz_result=quiz_result
    )
    await update.message.reply_text(reply_text, reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True))
    return QUIZ


async def save_result_to_db(payload):
    await db_handler.insert_result(payload)


async def skip_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Skip quiz and get back to topics"""
    await update.message.reply_text('Решил пропустить тест? Тогда давай вернёмся к нашим темам.',
                                    reply_markup=ReplyKeyboardMarkup([['К темам']], one_time_keyboard=True))
    return THEORY


async def quit_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Quit quiz"""

    user_id = str(update.message.from_user.id)
    user_info = await conv_db_handler.get_user_info({'user_id': user_id})
    cur_topic = user_info[1]
    cur_topic_id = topic_to_id[cur_topic]
    result = user_info[4]
    keyboard = [['К тесту', 'Всё равно выйти']]
    await update.message.reply_text('Ваш текущий результат - {}/{}. Если вы выйдите из теста, '
                                    'то он будет записан в базу. Действительно желаеете выйти?'
                                    .format(result, min(len(questions[cur_topic]), 5)),
                                    reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True))
    return QUIZ


async def confirm_quit_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = str(update.message.from_user.id)
    user_info = await conv_db_handler.get_user_info({'user_id': user_id})
    cur_topic = user_info[1]
    cur_topic_id = topic_to_id[cur_topic]
    result = user_info[4]
    await save_result_to_db({
        'user_id': user_id,
        'test_id': cur_topic_id,
        'result': result,
        'questions_amount': min(len(questions[cur_topic]), 5)
    })
    await update.message.reply_text('Желаете вернуться к темам?',
                                    reply_markup=ReplyKeyboardMarkup([['К темам']], one_time_keyboard=True))
    return THEORY


async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """When bot get unknown command"""
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Sorry, I didn't understand that command.")


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """End working"""
    await update.message.reply_text('Надеюсь, вы что-нибудь запомнили из пройденного материала. Всего хорошего!')

    return ConversationHandler.END


async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Display a help message"""
    await update.message.reply_text('Use /start to start bot')


def input_json(path):
    """Parse json file"""
    with open(path, 'r') as f:
        json_file = json.loads(f.read())
    for topic in json_file.keys():
        topic_id = json_file[topic].get('id', -1)
        topic_to_id[topic] = topic_id
        theory[topic] = json_file[topic].get('theory', '')
        questions[topic] = json_file[topic].get('questions', [])


def keyboard_separation(keyboard: list, size: int, quantity: int):
    return [[keyboard[i] for i in range(quantity * j, min(size, quantity * (j + 1)))]
            for j in range(size // quantity + (1 if size % quantity != 0 else 0))]

path_ = None
def start_bot(token: str, path: str) -> None:
    path_ = path
    """Run bot."""
    persistence = PicklePersistence(filepath="conversation1")
    application = Application.builder().token(token).persistence(persistence).build()
    application.add_handler(CommandHandler('help', help_handler))
    input_json(path)
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            # MENU: [
            #     CommandHandler('menu', menu),
            #     MessageHandler(filters.Regex('^(Темы)$'), choose_theory),
            #     MessageHandler(filters.Regex('^(Выход)$'), cancel),
            #     CommandHandler('start', start)
            # ],
            THEORY: [
                CommandHandler('choose_theory', choose_theory),
                MessageHandler(filters.Regex('^(К темам)$'), choose_theory),
                MessageHandler(filters.Regex('^({})$'.format('|'.join(theory.keys()))), print_theory),
                # MessageHandler(filters.Regex('^(Меню)$'), menu),
                CommandHandler('start', start)
            ],
            QUIZ: [
                MessageHandler(filters.Regex('^(Тестирование|К следующему вопросу|К тесту)$'), quiz),
                MessageHandler(filters.Regex('^(Пропустить тест)$'), skip_quiz),
                MessageHandler(filters.Regex('^(A\.|B\.|C\.|D\.).*$'), check_quiz),
                MessageHandler(filters.Regex('^(Выход)$'), quit_quiz),
                MessageHandler(filters.Regex('^(Всё равно выйти)$'), confirm_quit_quiz),
                CommandHandler('start', start)
            ]
        },
        fallbacks=[CommandHandler('cancel', cancel)],
        name='conv',
        persistent=True,
    )
    application.add_handler(conv_handler)
    application.add_handler(MessageHandler(filters.COMMAND, unknown))
    input_json(path)

    application.run_polling()
