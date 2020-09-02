import json
import datetime
import copy

class ExtendedProcessTreeJsonEncoder(json.JSONEncoder):
    def default(self, obj):
            try:
                nodes = obj.get_nodes_bottom_up()
                to_serialize = {'name': obj.__str__(),
                                'svg': None,
                                'operators':"->,*,X,^",
                                'nodes':[]}

                for node in nodes:
                    to_serialize["nodes"].append({'name': node.__str__(),
                                                'operator': node.operator.name if node.operator is not None else None,
                                                'kpis':{'cycle_time': str(sum([(range.end_datetime - range.start_datetime) for range 
                                                                      in node.kpis["cycle_times"]], datetime.timedelta())/len(node.kpis["cycle_times"]))
                                                                    #   TODO remove if not necessary
                                                                      if "cycle_times" in node.kpis and node.kpis["cycle_times"] else None,
                                                        'waiting_time': str(sum([(range.end_datetime - range.start_datetime) for range 
                                                                      in node.kpis["waiting_times"]], datetime.timedelta())/len(node.kpis["waiting_times"])),
                                                        'service_time': str(sum([(range.end_datetime - range.start_datetime) for range 
                                                                      in node.kpis["service_times"]], datetime.timedelta())/(len(node.kpis["cycle_times"]) if node.children else len(node.kpis["service_times"]))),
                                                        'idle_time': str(sum([(range.end_datetime - range.start_datetime) for range 
                                                                     in node.kpis["idle_times"]], datetime.timedelta())/len(node.kpis["cycle_times"])) 
                                                                     if "idle_times" in node.kpis and node.kpis["idle_times"] else "0:00:00"},
                                                'children':[children.__str__() for children in node.children]})
                to_serialize['originalState'] = self.default(obj.states[0]) if obj.states else copy.deepcopy(to_serialize)
                return to_serialize
            except AttributeError:
                return super().default(obj)
