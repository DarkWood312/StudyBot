class NumDontExistError(Exception):
    pass


class BaseDontExistError(Exception):
    pass


class WolframException:
    class StatusNot200(Exception):
        pass

    class NotSuccess(Exception):
        pass


class AIException:
    class TooManyRequests(Exception):
        def __init__(self, message='Слишком много запросов. Подождите 10 секунд'):
            self.message = message
            super().__init__(message)
