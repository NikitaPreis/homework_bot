import telegram
import telegram.ext

import requests

from http import HTTPStatus

import time

import os

from sys import stdout

import logging

from exceptions import (VenvVariableException,
                        PracticumHomeworkUnavailable,
                        ResponseHaventExpectedKeys,
                        UnexpectedStatusHomework)

from constants import (LAST_WORK,
                       RETRY_PERIOD,
                       ENDPOINT,
                       HOMEWORK_VERDICTS)

from dotenv import load_dotenv

load_dotenv()


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

logger = logging.getLogger(__name__)
stream_handler = logging.StreamHandler(stream=stdout)
logger.addHandler(stream_handler)
formatter = logging.Formatter(
    '%(asctime)s, %(lineno)d, %(levelname)s, %(message)s, %(name)s'
)
stream_handler.setFormatter(formatter)
file_handler = logging.FileHandler('homework.log')
logger.addHandler(file_handler)


def check_tokens():
    """Проверяет доступность переменных окружения."""
    venv_variables = (PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID)
    for venv_variable in venv_variables:
        if not(venv_variable):
            logging.critical(
                f'''Отсутствует обязательная
                переменная окружения: {venv_variable}'''
            )
            raise VenvVariableException


def send_message(bot, message):
    """Отправляет сообщение в Telegram чат, определяемый TELEGRAM_CHAT_ID.
    Принимает на вход два параметра:
    экземпляр класса Bot и строку с текстом сообщения.
    """
    try:
        new_message = bot.send_message(TELEGRAM_CHAT_ID, message)
        logging.debug('Сообщение успешно доставлено')
        return new_message
    except Exception as error:
        logging.error(f'Сбой при отправке сообщения в Telegram: {error}')


def get_api_answer(timestamp):
    """Делает запрос к единственному эндпоинту API-сервиса.
    В качестве параметра в функцию передается временная метка.
    В случае успешного запроса должна вернуть ответ API,
    приведя его из JSON к типам данных Python.
    """
    payload = {'from_date': timestamp}
    try:
        homework_statuses = requests.get(ENDPOINT,
                                         headers=HEADERS,
                                         params=payload)
    except requests.RequestException as error:
        logging.error(f'Возникла ошибка запроса к сервису: {error}')
    except Exception as error:
        logging.error(f'Сбой при запросе к сервису Практикум.Домашка: {error}')
    if homework_statuses.status_code != HTTPStatus.OK:
        logging.error('Нет доступа к сервису Практикум.Домашка')
        raise PracticumHomeworkUnavailable
    return homework_statuses.json()


def check_response(response):
    """Проверяет ответ API на соответствие документации.
    В качестве параметра функция получает ответ API,
    приведенный к типам данных Python.
    """
    if type(response) is not dict:
        logging.error('В ответе API данные передаются не словарем')
        raise TypeError
    if type(response.get('homeworks')) is not list:
        logging.error('В ответе API отсутствуют ожидаемые ключи')
        raise TypeError


def parse_status(homework):
    """Извлекает из информации о конкретной домашней работе статус этой работы.
    В качестве параметра получает один элемент из списка домашних работ.
    В случае успеха, возвращает строку для отправки в Telegram,
    содержащую один из вердиктов словаря HOMEWORK_VERDICTS.
    """
    homework_name = homework.get('homework_name')
    if homework_name is None:
        raise ResponseHaventExpectedKeys
    hw_status = homework.get('status')
    if hw_status not in HOMEWORK_VERDICTS:
        raise UnexpectedStatusHomework
    verdict = HOMEWORK_VERDICTS[hw_status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    check_tokens()

    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())

    past_message = ''

    while True:
        try:
            response = get_api_answer(timestamp)
            check_response(response)
            message = parse_status(response['homeworks'][LAST_WORK])
            if message != past_message:
                send_message(bot, message)
                past_message = message
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            if message != past_message:
                send_message(bot, message)
                past_message = message
        time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
