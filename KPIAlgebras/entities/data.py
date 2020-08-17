class EventLog:
    def __init__(self, log):
        self.log = log
    
    def is_atomic(self, event_label):
        start = None
        complete = None
        for trace in self.log:
            if start is None or not start:
                start = [event for event in trace if
                            event["concept:name"] == event_label and event["lifecycle:transition"] == "start"]
            if complete is None or not complete:
                complete = [event for event in trace if
                            event["concept:name"] == event_label and event["lifecycle:transition"] == "complete"]
            if start and complete:
                break

        return True if not start or not complete else False
