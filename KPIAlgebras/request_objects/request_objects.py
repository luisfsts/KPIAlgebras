class InvalidRequestObject:
    def __init__(self):
        self.errors = []

    def add_error(self, parameter, message):
        self.errors.append({'parameter': parameter, 'message':message})
    
    def has_errors(self):
        return len(self.errors) > 0

    def __bool__(self):
        return False    

class ValidRequestObject:
    @classmethod
    def from_dict(cls, dict):
        raise NotImplementedError

    def __bool__(self):
        return True
    
class TimeRangeConstructionRequestObject(ValidRequestObject):
    # accepted_extensions = ['.xes', '.csv']

    def __init__(self, parameters):
        self.parameters = parameters

    @classmethod
    def from_dict(cls, dict):
        invalid_request = InvalidRequestObject()
        if 'input' in dict:
            if not dict['input'].endswith(".xes") or not dict['input'].endswith(".csv"):
                invalid_request.add_error("Event log","extension is not supported")
                return invalid_request
        else:
            invalid_request.add_error("Event log","is missing") 
            return invalid_request

        return cls(parameters=dict.get("input", None))