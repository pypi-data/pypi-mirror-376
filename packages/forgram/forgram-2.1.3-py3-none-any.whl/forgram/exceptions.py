class ForgramError(Exception):
    pass

class APIError(ForgramError):
    def __init__(self, message, code=None):
        super().__init__(message) 
        self.code = code

class NetworkError(ForgramError):
    pass
