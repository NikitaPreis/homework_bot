import logging


logging.basicConfig(
    level=logging.DEBUG,
    filename='main.log',
    filemode='w',
    format='%(asctime)s, %(lineno)d, %(levelname)s, %(message)s, %(name)s'
)
