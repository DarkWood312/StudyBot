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

    class ApiIsBroken(Exception):
        def __init__(self, message='Похоже что API сломан сейчас...'):
            self.message = message
            super().__init__(message)

    class Error(Exception):
        def __init__(self, message='error'):
            self.message = message
            super().__init__(message)


class GigaException:
    class WrongAuthorization(Exception):
        def __init__(self, message='Wrong authorization'):
            self.message = message
            super().__init__(message)

class UchusOnlineException:
    class Unauthorized(Exception):
        def __init__(self, message='Unauthorized!'):
            self.message = message
            super().__init__(message)