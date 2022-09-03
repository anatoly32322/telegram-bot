import asyncio
import logging
import sys
from tgBot import start_bot
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


def main():
    token = sys.argv[1]
    path = sys.argv[2]
    start_bot(token, path)


if __name__ == '__main__':
    main()
