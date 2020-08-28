import unittest
import os
from KPIAlgebras import app
from KPIAlgebras.response_objects import response_objects
from KPIAlgebras.entities import model, data
from KPIAlgebras.rest import endpoints
from pm4py.objects.conversion.process_tree.converter import to_petri_net_transition_bordered as converter
from pm4py.objects.log.importer.xes import factory as xesimporter
from pm4py.objects.process_tree import util as process_tree_util
from datetimerange import DateTimeRange

class TestTimeRangeConstructionEndpoint(unittest.TestCase):
    def setUp(self):
        file_name = "partially_ordered_test_log.xes"
        path = os.path.join('/GitHub/KPIAlgebras/tests/files', file_name)
        self.event_log = data.EventLog(xesimporter.import_log(path))
        self.log = self.event_log
        process_tree = process_tree_util.parse("->( 'a' , +( 'b', 'c' ), 'd' )")
        self.extended_process_tree = model.ExtendedProcessTree(process_tree)
        self.model, self.initial_marking, self.final_marking = converter.apply(self.extended_process_tree)
        transition_a = [transition.name for transition in self.model.transitions if transition.label == "a"][0]
        transition_b = [transition.name for transition in self.model.transitions if transition.label == "b"][0]
        transition_c = [transition.name for transition in self.model.transitions if transition.label == "c"][0]
        transition_d = [transition.name for transition in self.model.transitions if transition.label == "d"][0]
        self.alignments = [{'alignment': [(('t_0_1596012778.96210121990', '>>'), (None, '>>')), 
                                        (('>>', "->( 'a', +( 'b', 'c' ), 'd' )_start"), ('>>', None)), 
                                        (('t_a_0', transition_a), ('a', 'a')), 
                                        (('>>', "+( 'b', 'c' )_start"), ('>>', None)), 
                                        (('t_c_1', transition_c), ('c', 'c')), 
                                        (('t_b_2', transition_b), ('b', 'b')), 
                                        (('>>', "+( 'b', 'c' )_end"), ('>>', None)), 
                                        (('t_d_3', transition_d), ('d', 'd')), 
                                        (('t_1_1596012778.96210123213', '>>'), (None, '>>')), 
                                        (('>>', "->( 'a', +( 'b', 'c' ), 'd' )_end"), ('>>', None))], 
                           'cost': 6, 
                           'visited_states': 11, 
                           'queued_states': 30, 
                           'traversed_arcs': 30}]
        self.time_ranges = {"->( 'a', +( 'b', 'c' ), 'd' )": {'waiting_times':[DateTimeRange('2019-05-20T01:00:00+0000', '2019-05-20T01:00:00+0000')],
                                                                'service_times': [DateTimeRange('2019-05-20T01:00:00+0000','2019-05-20T12:30:00+0000'), 
                                                                                    DateTimeRange('2019-05-20T12:51:00+0000','2019-05-21T14:14:00+0000' ), 
                                                                                    DateTimeRange('2019-05-21T14:23:00+0000', '2019-05-21T17:06:00+0000')],
                                                                'idle_times': [DateTimeRange('2019-05-20T12:30:00+0000', '2019-05-20T12:51:00+0000'), 
                                                                                DateTimeRange('2019-05-21T14:14:00+0000', '2019-05-21T14:23:00+0000')]}, 
                            'a': {'waiting_times': [DateTimeRange('2019-05-20T01:00:00+0000','2019-05-20T01:00:00+0000')], 
                                    'service_times': [DateTimeRange('2019-05-20T01:00:00+0000','2019-05-20T12:30:00+0000')]},
                            "+( 'b', 'c' )": {'waiting_times':[DateTimeRange('2019-05-20T12:30:00+0000','2019-05-20T12:51:00+0000')],
                                                'service_times': [DateTimeRange('2019-05-20T12:51:00+0000','2019-05-21T14:14:00+0000')],
                                                'idle_times': []},
                            'c':{'waiting_times': [DateTimeRange('2019-05-20T12:30:00+0000','2019-05-20T12:51:00+0000')],
                                  'service_times': [DateTimeRange('2019-05-20T12:51:00+0000','2019-05-20T15:55:00+0000')]},
                            'b':{'waiting_times': [DateTimeRange('2019-05-20T12:30:00+0000','2019-05-20T15:02:00+0000')],
                                  'service_times': [DateTimeRange('2019-05-20T15:02:00+0000','2019-05-21T14:14:00+0000')]},      
                            'd':{'waiting_times': [DateTimeRange('2019-05-21T14:14:00+0000','2019-05-21T14:23:00+0000')],
                                  'service_times': [DateTimeRange('2019-05-21T14:23:00+0000','2019-05-21T17:06:00+0000')]}}
        
        for node in self.extended_process_tree.get_nodes_bottom_up():
            node.kpis = {**node.kpis,**self.time_ranges[node.__str__()]}
        endpoints.log = self.log
        endpoints.alignments = self.alignments
        endpoints.model = self.model
        endpoints.initial_marking = self.initial_marking
        endpoints.final_marking = self.final_marking
        endpoints.extended_process_tree = self.extended_process_tree
        self.file = open(path, 'rb')
        self.data = {'eventLog': (self.file, file_name)}
        self.app =  app.create_app().test_client()
        self.app.testing = True
        
    def test_time_range_construction_endpoint(self):
        http_response = self.app.post('/measurement', data = self.data)
        self.assertTrue(bool(http_response))
        self.assertEquals(http_response.status_code, 200)
        self.assertEquals(http_response.mimetype, 'application/json')
    
    def test_time_shifting_endpoint(self):
        http_response = self.app.post('/timeshifting?delta=0.2&kpi=service_time&target_node=b')
        self.assertEquals(http_response.status_code, 200)
        self.assertEquals(http_response.mimetype, 'application/json')