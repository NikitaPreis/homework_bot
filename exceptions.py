class VenvVariableException(Exception):
    """Отсутствует переменная окружения."""

    pass


class PracticumHomeworkUnavailable(Exception):
    """Нет доступа к сервису Практикум.Домашка."""

    pass


class ResponseHaventExpectedKeys:
    """Ответ не содержит ожидаемых ключей."""

    pass


class UnexpectedStatusHomework:
    """Неожиданный статус домашней работы."""

    pass
