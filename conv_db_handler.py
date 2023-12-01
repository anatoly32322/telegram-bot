import logging
import aiosqlite


logger = logging.getLogger(__name__)


class ConvDBHandler:
    db_path: str
    CREATE_TABLE_REQUEST = '''CREATE TABLE 
        IF NOT EXISTS conversation_data(
            user_id TEXT, 
            current_topic TEXT, 
            current_question INT, 
            current_set_of_questions TEXT, 
            quiz_result INT
        )'''
    INSERT_NEW_USER_REQUEST = '''INSERT INTO conversation_data (
        user_id, 
        current_topic, 
        current_question, 
        current_set_of_questions,
        quiz_result
        )
        VALUES (:user_id, NULL, NULL, NULL, NULL)'''
    UPDATE_CURRENT_TOPIC_REQUEST = '''UPDATE conversation_data
        SET current_topic=:current_topic
        WHERE user_id=:user_id'''
    UPDATE_CURRENT_QUESTION_REQUEST = '''UPDATE conversation_data
        SET current_question=:current_question
        WHERE user_id=:user_id'''
    UPDATE_CURRENT_SET_OF_QUESTIONS_REQUEST = '''UPDATE conversation_data
        SET current_set_of_questions=:current_set_of_questions
        WHERE user_id=:user_id'''
    UPDATE_QUIZ_RESULT_REQUEST = '''UPDATE conversation_data
        SET quiz_result=:quiz_result
        WHERE user_id=:user_id'''
    GET_USER_INFORMATION_REQUEST = '''SELECT * FROM conversation_data WHERE user_id=:user_id'''
    COUNT_DUPLICATE_REQUEST = '''SELECT COUNT(*) FROM conversation_data WHERE user_id=:user_id'''

    def __init__(self, db_path):
        self.db_path = db_path

    async def create_table(self) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            try:
                await db.execute(self.CREATE_TABLE_REQUEST)
                await db.commit()
            except aiosqlite.Error as error:
                logger.info('Error creating table: {}'.format(error))

    async def get_user_info(self, criteria) -> tuple:
        async with aiosqlite.connect(self.db_path) as db:
            try:
                cur = await db.execute(self.GET_USER_INFORMATION_REQUEST, criteria)
                record = await cur.fetchone()
            except aiosqlite.Error as error:
                logger.info('Error getting user info: {}'.format(error))
        return record

    async def is_user_exist(self, criteria) -> bool:
        async with aiosqlite.connect(self.db_path) as db:
            try:
                cur = await db.execute(self.COUNT_DUPLICATE_REQUEST, criteria)
                record = (await cur.fetchone())[0]
            except aiosqlite.Error as error:
                logger.info('Error finding out is user exist: {}'.format(error))
        return record != 0

    async def insert_user(self, payload):
        async with aiosqlite.connect(self.db_path) as db:
            try:
                if not await self.is_user_exist({'user_id': payload['user_id']}):
                    await db.execute(self.INSERT_NEW_USER_REQUEST, payload)
                    await db.commit()
            except aiosqlite.Error as error:
                logger.info('Error inserting new user: {}'.format(error))

    async def update_cur_topic(self, payload):
        async with aiosqlite.connect(self.db_path) as db:
            try:
                await db.execute(self.UPDATE_CURRENT_TOPIC_REQUEST, payload)
                await db.commit()
            except aiosqlite.Error as error:
                logger.info('Error during update current topic: {}'.format(error))

    async def update_cur_question(self, payload):
        async with aiosqlite.connect(self.db_path) as db:
            try:
                await db.execute(self.UPDATE_CURRENT_QUESTION_REQUEST, payload)
                await db.commit()
            except aiosqlite.Error as error:
                logger.info('Error during update current question: {}'.format(error))

    async def update_cur_set_of_question(self, payload):
        async with aiosqlite.connect(self.db_path) as db:
            try:
                await db.execute(self.UPDATE_CURRENT_SET_OF_QUESTIONS_REQUEST, payload)
                await db.commit()
            except aiosqlite.Error as error:
                logger.info('Error during update current set of questions: {}'.format(error))

    async def update_quiz_result(self, payload):
        async with aiosqlite.connect(self.db_path) as db:
            try:
                await db.execute(self.UPDATE_QUIZ_RESULT_REQUEST, payload)
                await db.commit()
            except aiosqlite.Error as error:
                logger.info('Error during update quiz result: {}'.format(error))
