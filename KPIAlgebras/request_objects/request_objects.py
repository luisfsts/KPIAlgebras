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
        if 'event_log' in dict:
            if not dict['event_log'].endswith(".xes") or not dict['event_log'].endswith(".csv"):
                invalid_request.add_error("Event log","extension is not supported")
                return invalid_request
        else:
            invalid_request.add_error("Event log","is missing") 
            return invalid_request

        return cls(parameters=dict.get("event_log", None))

class TimeShiftingRequestObject(ValidRequestObject):
    def __init__(self, parameters):
        self.parameters = parameters
    
    @classmethod
    def from_dict(cls, dict):
        invalid_request = InvalidRequestObject()
        if 'target_node' not in dict:
            invalid_request.add_error("Target Node", "is missing")
        if 'delta' not in dict:
            invalid_request.add_error("Delta", "is missing")
        
        if invalid_request.has_errors():
            return invalid_request
        
        return cls(parameters=dict)
            
