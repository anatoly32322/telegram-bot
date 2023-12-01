import asyncio
import logging
import sys
import configparser
from tgBot import start_bot
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)


config = configparser.ConfigParser()
config.read('settings.ini')
bot_config = config['bot']


def main():
    token = bot_config['token']
    path = bot_config['path']
    start_bot(token, path)


if __name__ == '__main__':
    main()
