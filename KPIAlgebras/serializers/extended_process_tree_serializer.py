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
                    avg_cycle_time = node.get_avg_kpi_value("cycle_times") 
                    avg_waiting_time = node.get_avg_kpi_value("waiting_times") 
                    avg_service_time =  node.get_avg_kpi_value("service_times") 
                    avg_idle_time =  node.get_avg_kpi_value("idle_times") 
                    to_serialize["nodes"].append({'name': node.__str__(),
                                                'operator': node.operator.name if node.operator is not None else None,
                                                'kpis':{'Sojourn time': {'repr': str(avg_cycle_time) if avg_cycle_time is not None else None, 
                                                                        'duration': avg_cycle_time.total_seconds() if avg_cycle_time is not None else None},
                                                        'Waiting time': {'repr': str(avg_waiting_time) if avg_cycle_time is not None else None, 
                                                                        'duration': avg_waiting_time.total_seconds()if avg_waiting_time is not None else None},
                                                        'Service time': {'repr': str(avg_service_time) if avg_cycle_time is not None else None, 
                                                                        'duration': avg_service_time.total_seconds()if avg_service_time is not None else None},
                                                        'Idle time':{'repr': str(avg_idle_time) if avg_cycle_time is not None else None, 
                                                                    'duration': avg_idle_time.total_seconds() if avg_idle_time is not None else None}},
                                                'children':[children.__str__() for children in node.children]})
                to_serialize['originalState'] = self.default(obj.states[0]) if obj.states else copy.deepcopy(to_serialize)
                return to_serialize
            except AttributeError:
                return super().default(obj)
