import json
import unittest
from datetimerange import DateTimeRange
from pm4py.objects.process_tree import util as process_tree_util
from KPIAlgebras.entities import model
from KPIAlgebras.serializers import extended_process_tree_serializer as encoder


class TestExtendedProcessTreeSerializer(unittest.TestCase):
    def setUp(self):
        process_tree = process_tree_util.parse("->( 'a' , +( 'b', 'c' ), 'd' )")
        self.extended_process_tree = model.ExtendedProcessTree(process_tree)
        self.time_ranges = {"->( 'a', +( 'b', 'c' ), 'd' )": {'cycle_times':[DateTimeRange('2019-05-20T01:00:00+0000','2019-05-21T17:06:00+0000')],
                                                                'waiting_times':[DateTimeRange('2019-05-20T01:00:00+0000', '2019-05-20T01:00:00+0000')],
                                                                'service_times': [DateTimeRange('2019-05-20T01:00:00+0000','2019-05-20T12:30:00+0000'), 
                                                                                    DateTimeRange('2019-05-20T12:51:00+0000','2019-05-21T14:14:00+0000' ), 
                                                                                    DateTimeRange('2019-05-21T14:23:00+0000', '2019-05-21T17:06:00+0000')],
                                                                'idle_times': [DateTimeRange('2019-05-20T12:30:00+0000', '2019-05-20T12:51:00+0000'), 
                                                                                DateTimeRange('2019-05-21T14:14:00+0000', '2019-05-21T14:23:00+0000')]}, 
                            'a': {'cycle_times': [DateTimeRange('2019-05-20T01:00:00+0000','2019-05-20T12:30:00+0000')],
                                    'waiting_times': [DateTimeRange('2019-05-20T01:00:00+0000','2019-05-20T01:00:00+0000')], 
                                    'service_times': [DateTimeRange('2019-05-20T01:00:00+0000','2019-05-20T12:30:00+0000')]},
                            "+( 'b', 'c' )": {'cycle_times':[DateTimeRange('2019-05-20T12:30:00+0000','2019-05-21T14:14:00+0000')],
                                                'waiting_times':[DateTimeRange('2019-05-20T12:30:00+0000','2019-05-20T12:51:00+0000')],
                                                'service_times': [DateTimeRange('2019-05-20T12:51:00+0000','2019-05-21T14:14:00+0000')],
                                                'idle_times': []},
                            'c':{'cycle_times': [DateTimeRange('2019-05-20T12:30:00+0000','2019-05-20T15:55:00+0000')],
                                  'waiting_times': [DateTimeRange('2019-05-20T12:30:00+0000','2019-05-20T12:51:00+0000')],
                                  'service_times': [DateTimeRange('2019-05-20T12:51:00+0000','2019-05-20T15:55:00+0000')]},
                            'b':{'cycle_times': [DateTimeRange('2019-05-20T12:30:00+0000','2019-05-21T14:14:00+0000')],
                                  'waiting_times': [DateTimeRange('2019-05-20T12:30:00+0000','2019-05-20T15:02:00+0000')],
                                  'service_times': [DateTimeRange('2019-05-20T15:02:00+0000','2019-05-21T14:14:00+0000')]},      
                            'd':{'cycle_times': [DateTimeRange('2019-05-21T14:14:00+0000','2019-05-21T17:06:00+0000')],
                                 'waiting_times': [DateTimeRange('2019-05-21T14:14:00+0000','2019-05-21T14:23:00+0000')],
                                  'service_times': [DateTimeRange('2019-05-21T14:23:00+0000','2019-05-21T17:06:00+0000')]}}
        nodes = self.extended_process_tree.get_nodes_bottom_up()
        
        for node in nodes:
            node.kpis = self.time_ranges[node.__str__()]
        
        self.expected_json = """
                                {"name": "->( 'a', +( 'b', 'c' ), 'd' )", 
                                 "svg": null, 
                                 "operators": "->,*,X,^", 
                                 "nodes": [{"name": "a", 
                                            "operator": null, 
                                            "kpis": {"cycle_time": "11:30:00", 
                                                      "waiting_time": "0:00:00", 
                                                      "service_time": "11:30:00", 
                                                      "idle_time": "0:00:00"}, 
                                            "children": []}, 
                                           {"name": "b", 
                                            "operator": null, 
                                            "kpis": {"cycle_time": "1 day, 1:44:00", 
                                                     "waiting_time": "2:32:00", 
                                                     "service_time": "23:12:00", 
                                                     "idle_time": "0:00:00"}, 
                                                     "children": []}, 
                                                     {"name": "c", "operator": null, "kpis": {"cycle_time": "3:25:00", "waiting_time": "0:21:00", "service_time": "3:04:00", "idle_time": "0:00:00"}, "children": []}, {"name": "+( 'b', 'c' )", "operator": "PARALLEL", "kpis": {"cycle_time": "1 day, 1:44:00", "waiting_time": "0:21:00", "service_time": "1 day, 1:23:00", "idle_time": "0:00:00"}, "children": ["b", "c"]}, {"name": "d", "operator": null, "kpis": {"cycle_time": "2:52:00", "waiting_time": "0:09:00", "service_time": "2:43:00", "idle_time": "0:00:00"}, "children": []}, {"name": "->( 'a', +( 'b', 'c' ), 'd' )", "operator": "SEQUENCE", "kpis": {"cycle_time": "1 day, 16:06:00", "waiting_time": "0:00:00", "service_time": "13:12:00", "idle_time": "0:15:00"}, "children": ["a", "+( 'b', 'c' )", "d"]}]}
                            """

    def test_serialize_domain_Extended_process_tree(self):
        json_extended_tree = json.dumps(self.extended_process_tree, check_circular=False, cls=encoder.ExtendedProcessTreeJsonEncoder)
        self.assertDictEqual(json.loads(self.expected_json), json.loads(json_extended_tree))