class ResponseFailure:
    PARAMETERS_ERROR = 'parameterserror'
    
    def __init__(self, type, message):
        self.type = type
        self.message = self.format_message(message)
    
    def format_message(self, message):
        if isinstance(message, Exception):
            return "{}: {}".format(message.__class__.__name__, "{}".format(message))
        return message

    @property
    def value(self):
        return {'type': self.type, 'message': self.message}    
    
    @classmethod
    def build_from_invalid_request(cls, invalid_request):
        message = "\n".join(["{}: {}".format(err['parameter'], err['message'])
                             for err in invalid_request.errors])
        return cls(cls.PARAMETERS_ERROR, message)
        
    def __bool__(self):
        return False

class ResponseSuccess:
    SUCCESS = 'sucess'

    def __init__(self, value):
        self.type = self.SUCCESS
        self.value = value
    
    def __bool_(self):
        return True