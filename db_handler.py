import logging
import aiosqlite


logger = logging.getLogger(__name__)


class DBHandler:
    INSERT_DATA_REQUEST = '''INSERT INTO results 
        VALUES(:user_id, :test_id, :result, :questions_amount, current_timestamp)'''
    CREATE_TABLE_REQUEST = '''CREATE TABLE 
        IF NOT EXISTS 
        results(user_id INT, test_id INT, result INT, questions_amount INT, timestamp INT)'''
    DELETE_USER_REQUEST = '''DELETE FROM results WHERE user_id=:user_id'''
    DELETE_LAST_REQUEST = '''DELETE FROM results
        WHERE user_id=:user_id
        AND test_id=:test_id
        AND timestamp=(SELECT MIN(timestamp) FROM results WHERE user_id=:user_id AND test_id=:test_id)
        '''
    COUNT_USER_RESULTS = '''SELECT COUNT(*) FROM results WHERE user_id=:user_id AND test_id=:test_id'''
    FIND_BEST_REQUEST = '''SELECT MAX(result) FROM results WHERE user_id=:user_id AND test_id=:test_id'''

    def __init__(self, db_path: str):
        self.db_path = db_path

    async def create_table(self) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            try:
                await db.execute(self.CREATE_TABLE_REQUEST)
                await db.commit()
            except aiosqlite.Error as error:
                logger.info('Error creating table: {}'.format(error))

    async def insert_result(self, payload: dict) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            try:
                best_result = await self.find_best(payload['user_id'], payload['test_id'])
                results_amount = await self.count_user_results(payload['user_id'], payload['test_id'])
                if results_amount > 10 and best_result >= payload['result']:
                    return
                await db.execute(self.INSERT_DATA_REQUEST, payload)
                await db.commit()
                await self.leave_ten_last(payload['user_id'], payload['test_id'], results_amount + 1)
            except aiosqlite.Error as error:
                logger.info('Error inserting data to the database: {}'.format(error))

    async def delete_user(self, user_id: str) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            try:
                await db.execute(self.DELETE_USER_REQUEST, user_id)
                await db.commit()
            except aiosqlite.Error as error:
                logger.info('Error deleting user from the database: {}'.format(error))

    async def count_user_results(self, user_id: str, test_id: str) -> int:
        async with aiosqlite.connect(self.db_path) as db:
            try:
                cur = await db.execute(self.COUNT_USER_RESULTS, {'user_id': user_id, 'test_id': test_id})
                record = (await cur.fetchone())[0]
            except aiosqlite.Error as error:
                logger.info('Error counting user results: {}'.format(error))
        return record

    async def leave_ten_last(self, user_id: str, test_id: int, results_amount: int) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            try:
                while results_amount > 10:
                    await db.execute(self.DELETE_LAST_REQUEST, {'user_id': user_id, 'test_id': test_id})
                    results_amount -= 1
                await db.commit()
            except aiosqlite.Error as error:
                logger.info('Error leaving ten last results: {}'.format(error))

    async def find_best(self, user_id: str, test_id: int) -> int:
        async with aiosqlite.connect(self.db_path) as db:
            try:
                cur = await db.execute(self.FIND_BEST_REQUEST, {'user_id': user_id, 'test_id': test_id})
                record = (await cur.fetchone())[0]
            except aiosqlite.Error as error:
                logger.info('Error finding best result: {}'.format(error))
        return record

    def get_top_three(self) -> None:
        pass
