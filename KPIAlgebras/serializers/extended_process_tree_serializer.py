import json
import datetime
import copy

class ExtendedProcessTreeJsonEncoder(json.JSONEncoder):
    def default(self, obj):
            try:
                nodes = obj.get_nodes_bottom_up()
                to_serialize = {'name': obj.__str__(),
                                'svg': None,
                                'operators':['->','*','X','^'],
                                'nodes':[]}

                for node in nodes:
                    avg_cycle_time = str(sum([(range.end_datetime - range.start_datetime) for range in node.kpis["cycle_times"]], datetime.timedelta())
                                        /len(node.kpis["cycle_times"])) if "cycle_times" in node.kpis and node.kpis["cycle_times"] else None
                    avg_waiting_time = str(sum([(range.end_datetime - range.start_datetime) for range 
                                            in node.kpis["waiting_times"]], datetime.timedelta())/len(node.kpis["waiting_times"])) if "waiting_times" in node.kpis and node.kpis["waiting_times"] else None
                    avg_service_time = str(sum([(range.end_datetime - range.start_datetime) for range 
                                                in node.kpis["service_times"]], datetime.timedelta())/(len(node.kpis["waiting_times"]) 
                                                if node.children else len(node.kpis["service_times"]))) if "service_times" in node.kpis and node.kpis["service_times"] else None
                    avg_idle_time =  str(sum([(range.end_datetime - range.start_datetime) for range 
                                        in node.kpis["idle_times"]], datetime.timedelta())/len(node.kpis["waiting_times"])) if "idle_times" in node.kpis and node.kpis["idle_times"] else "0:00:00"
                    to_serialize["nodes"].append({'name': node.__str__(),
                                                'operator': node.operator.name if node.operator is not None else None,
                                                'kpis':{'cycle_time': avg_cycle_time,
                                                        'waiting_time': avg_waiting_time,
                                                        'service_time': avg_service_time,
                                                        'idle_time':avg_idle_time},
                                                'children':[children.__str__() for children in node.children]})
                to_serialize['originalState'] = self.default(obj.states[0]) if obj.states else copy.deepcopy(to_serialize)
                return to_serialize
            except AttributeError:
                return super().default(obj)
