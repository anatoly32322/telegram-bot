import ydb
import configparser

config = configparser.ConfigParser()
config.read('settings.ini')
ydb_config = config['ydb']
topic_url = f'{ydb_config["database"]}{ydb_config["topic"]}'


async def connect() -> ydb.aio.Driver:
    db = ydb.aio.Driver(
        connection_string=f'{ydb_config["ydb_url"]}?database={ydb_config["database"]}',
        credentials=ydb.credentials.AnonymousCredentials(),
    )
    return db


async def consumer(db: ydb.aio.Driver) -> ydb.TopicReaderAsyncIO:
    reader = db.topic_client.reader(topic_url, consumer=ydb_config['consumer'])
    return reader


async def producer(db: ydb.aio.Driver) -> ydb.TopicWriterAsyncIO:
    writer = db.topic_client.writer(topic_url, producer_id=ydb_config['producer_id'])
    return writer


