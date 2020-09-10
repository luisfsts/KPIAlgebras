import unittest
import os
from KPIAlgebras.entities import model, data
from KPIAlgebras.use_cases import time_range_construction_use_case as measurement
from pm4py.objects.conversion.process_tree.converter import to_petri_net_transition_bordered as converter
from pm4py.objects.log.importer.xes import factory as xesimporter
from pm4py.objects.process_tree import util as process_tree_util
from datetimerange import DateTimeRange
from datetime import datetime, timedelta
from KPIAlgebras.request_objects import request_objects

class TestTimeRangeConstructionUseCase(unittest.TestCase):
    def setUp(self):
        file_name = "partially_ordered_test_log.xes"
        path = os.path.join('/GitHub/KPIAlgebras/tests/files', file_name)
        self.event_log = data.EventLog(xesimporter.import_log(path))
        self.log = self.event_log.log
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
        
        self.waiting_shifted_time_ranges_with_no_gains = {"->( 'a', +( 'b', 'c' ), 'd' )": {'waiting_times':[DateTimeRange('2019-05-20T01:00:00+0000', '2019-05-20T01:00:00+0000')],
                                                                    'service_times': [DateTimeRange('2019-05-20T01:00:00+0000','2019-05-20T12:30:00+0000'), 
                                                                                    DateTimeRange('2019-05-20T12:46:48+0000','2019-05-21T14:14:00+0000' ), 
                                                                                    DateTimeRange('2019-05-21T14:23:00+0000', '2019-05-21T17:06:00+0000')],
                                                                    'idle_times': [DateTimeRange('2019-05-20T12:30:00+0000', '2019-05-20T12:46:48+0000'), 
                                                                                DateTimeRange('2019-05-21T14:14:00+0000', '2019-05-21T14:23:00+0000')]}, 
                                    'a': {'waiting_times': [DateTimeRange('2019-05-20T01:00:00+0000','2019-05-20T01:00:00+0000')], 
                                            'service_times': [DateTimeRange('2019-05-20T01:00:00+0000','2019-05-20T12:30:00+0000')]},
                                    "+( 'b', 'c' )": {'waiting_times':[DateTimeRange('2019-05-20T12:30:00+0000','2019-05-20T12:46:48+0000')],
                                                        'service_times': [DateTimeRange('2019-05-20T12:46:48+0000','2019-05-21T14:14:00+0000')],
                                                        'idle_times': []},
                                    'c':{'waiting_times': [DateTimeRange('2019-05-20T12:30:00+0000','2019-05-20T12:46:48+0000')],
                                        'service_times': [DateTimeRange('2019-05-20T12:46:48+0000','2019-05-20T15:50:48+0000')]},
                                    'b':{'waiting_times': [DateTimeRange('2019-05-20T12:30:00+0000','2019-05-20T15:02:00+0000')],
                                        'service_times': [DateTimeRange('2019-05-20T15:02:00+0000','2019-05-21T14:14:00+0000')]},      
                                    'd':{'waiting_times': [DateTimeRange('2019-05-21T14:14:00+0000','2019-05-21T14:23:00+0000')],
                                        'service_times': [DateTimeRange('2019-05-21T14:23:00+0000','2019-05-21T17:06:00+0000')]}}
        
        self.waiting_shifted_time_ranges_with_gains = {"->( 'a', +( 'b', 'c' ), 'd' )": {'waiting_times':[DateTimeRange('2019-05-20T01:00:00+0000', '2019-05-20T01:00:00+0000')],
                                                                'service_times': [DateTimeRange('2019-05-20T01:00:00+0000','2019-05-20T12:30:00+0000'), 
                                                                                    DateTimeRange('2019-05-20T12:51:00+0000','2019-05-21T13:43:36+0000' ), 
                                                                                    DateTimeRange('2019-05-21T13:52:36+0000', '2019-05-21T16:35:36+0000')],
                                                                'idle_times': [DateTimeRange('2019-05-20T12:30:00+0000', '2019-05-20T12:51:00+0000'), 
                                                                                DateTimeRange('2019-05-21T13:43:36+0000', '2019-05-21T13:52:36+0000')]}, 
                            'a': {'waiting_times': [DateTimeRange('2019-05-20T01:00:00+0000','2019-05-20T01:00:00+0000')], 
                                    'service_times': [DateTimeRange('2019-05-20T01:00:00+0000','2019-05-20T12:30:00+0000')]},
                            "+( 'b', 'c' )": {'waiting_times':[DateTimeRange('2019-05-20T12:30:00+0000','2019-05-20T12:51:00+0000')],
                                                'service_times': [DateTimeRange('2019-05-20T12:51:00+0000','2019-05-21T13:43:36+0000')],
                                                'idle_times': []},
                            'c':{'waiting_times': [DateTimeRange('2019-05-20T12:30:00+0000','2019-05-20T12:51:00+0000')],
                                  'service_times': [DateTimeRange('2019-05-20T12:51:00+0000','2019-05-20T15:55:00+0000')]},
                            'b':{'waiting_times': [DateTimeRange('2019-05-20T12:30:00+0000','2019-05-20T14:31:36+0000')],
                                'service_times': [DateTimeRange('2019-05-20T14:31:36+0000','2019-05-21T13:43:36+0000')]},      
                            'd':{'waiting_times': [DateTimeRange('2019-05-21T13:43:36+0000','2019-05-21T13:52:36+0000')],
                                'service_times': [DateTimeRange('2019-05-21T13:52:36+0000','2019-05-21T16:35:36+0000')]}}
        
        self.service_shifted_time_ranges_with_gains = {"->( 'a', +( 'b', 'c' ), 'd' )": {'waiting_times':[DateTimeRange('2019-05-20T01:00:00+0000', '2019-05-20T01:00:00+0000')],
                                                                'service_times': [DateTimeRange('2019-05-20T01:00:00+0000','2019-05-20T12:30:00+0000'), 
                                                                                    DateTimeRange('2019-05-20T12:51:00+0000','2019-05-21T09:35:36+0000' ), 
                                                                                    DateTimeRange('2019-05-21T09:44:36+0000', '2019-05-21T12:27:36+0000')],
                                                                'idle_times': [DateTimeRange('2019-05-20T12:30:00+0000', '2019-05-20T12:51:00+0000'), 
                                                                                DateTimeRange('2019-05-21T09:35:36+0000', '2019-05-21T09:44:36+0000')]}, 
                            'a': {'waiting_times': [DateTimeRange('2019-05-20T01:00:00+0000','2019-05-20T01:00:00+0000')], 
                                    'service_times': [DateTimeRange('2019-05-20T01:00:00+0000','2019-05-20T12:30:00+0000')]},
                            "+( 'b', 'c' )": {'waiting_times':[DateTimeRange('2019-05-20T12:30:00+0000','2019-05-20T12:51:00+0000')],
                                                'service_times': [DateTimeRange('2019-05-20T12:51:00+0000','2019-05-21T09:35:36+0000')],
                                                'idle_times': []},
                            'c':{'waiting_times': [DateTimeRange('2019-05-20T12:30:00+0000','2019-05-20T12:51:00+0000')],
                                  'service_times': [DateTimeRange('2019-05-20T12:51:00+0000','2019-05-20T15:55:00+0000')]},
                            'b':{'waiting_times': [DateTimeRange('2019-05-20T12:30:00+0000','2019-05-20T15:02:00+0000')],
                                  'service_times': [DateTimeRange('2019-05-20T15:02:00+0000','2019-05-21T09:35:36+0000')]},      
                            'd':{'waiting_times': [DateTimeRange('2019-05-21T09:35:36+0000','2019-05-21T09:44:36+0000')],
                                  'service_times': [DateTimeRange('2019-05-21T09:44:36+0000','2019-05-21T12:27:36+0000')]}}

        self.service_shifted_time_ranges_with_no_gains = {"->( 'a', +( 'b', 'c' ), 'd' )": {'waiting_times':[DateTimeRange('2019-05-20T01:00:00+0000', '2019-05-20T01:00:00+0000')],
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
                                  'service_times': [DateTimeRange('2019-05-20T12:51:00+0000','2019-05-20T15:18:12+0000')]},
                            'b':{'waiting_times': [DateTimeRange('2019-05-20T12:30:00+0000','2019-05-20T15:02:00+0000')],
                                  'service_times': [DateTimeRange('2019-05-20T15:02:00+0000','2019-05-21T14:14:00+0000')]},      
                            'd':{'waiting_times': [DateTimeRange('2019-05-21T14:14:00+0000','2019-05-21T14:23:00+0000')],
                                  'service_times': [DateTimeRange('2019-05-21T14:23:00+0000','2019-05-21T17:06:00+0000')]}}
        
        file_name_2 = "Log for Process with loop.xes"
        path = os.path.join('/GitHub/KPIAlgebras/tests/files', file_name_2)
        self.event_log_with_loops = data.EventLog(xesimporter.import_log(path))
        self.log_with_loops = self.event_log_with_loops.log
        process_tree = process_tree_util.parse("->('a', *(->('c', 'd'), tau), 'b')")
        self.extended_process_tree_with_loops = model.ExtendedProcessTree(process_tree)
        self.model_with_loops, self.initial_marking_with_loops, self.final_marking_with_loops = converter.apply(self.extended_process_tree_with_loops)
        transition_a = [transition.name for transition in self.model_with_loops.transitions if transition.label == "a"][0]
        transition_b = [transition.name for transition in self.model_with_loops.transitions if transition.label == "b"][0]
        transition_c = [transition.name for transition in self.model_with_loops.transitions if transition.label == "c"][0]
        transition_d = [transition.name for transition in self.model_with_loops.transitions if transition.label == "d"][0]
        silent_transition = [transition.name for transition in self.model_with_loops.transitions if transition.label is None and 
                              (not transition.name.endswith("_start") and not not transition.name.endswith("_end"))][0]
        self.alignments_with_loops = [{'alignment': [(('t_0_1598948941.94495631998', '>>'), (None, '>>')), 
                                                    (('>>', "->( 'a', *( ->( 'c', 'd' ), τ ), 'b' )_start"), ('>>', None)), 
                                                    (('t_a_0', transition_a), ('a', 'a')), 
                                                    (('>>', "*( ->( 'c', 'd' ), τ )_start"), ('>>', None)), 
                                                    (('>>', "->( 'c', 'd' )_start"), ('>>', None)), 
                                                    (('t_c_1', transition_c), ('c', 'c')), 
                                                    (('t_d_2', transition_d), ('d', 'd')), 
                                                    (('>>', "->( 'c', 'd' )_end"), ('>>', None)), 
                                                    (('>>', silent_transition), ('>>', None)), 
                                                    (('>>', "->( 'c', 'd' )_start"), ('>>', None)), 
                                                    (('t_c_3', transition_c), ('c', 'c')), 
                                                    (('t_d_4', transition_d), ('d', 'd')), 
                                                    (('>>', "->( 'c', 'd' )_end"), ('>>', None)), 
                                                    (('>>', "*( ->( 'c', 'd' ), τ )_end"), ('>>', None)), 
                                                    (('t_b_5', transition_b), ('b', 'b')), 
                                                    (('>>', "->( 'a', *( ->( 'c', 'd' ), τ ), 'b' )_end"), ('>>', None)), 
                                                    (('t_1_1598948941.94495633537', '>>'), (None, '>>'))], 
                                                    'cost': 11, 'visited_states': 18, 'queued_states': 43, 'traversed_arcs': 43}]
        
        self.time_ranges_with_loops = {"->('a', *(->('c', 'd'), tau), 'b')": {'waiting_times':[DateTimeRange('1970-01-01T01:00:00+01:00', '1970-01-01T01:00:00+01:00')],
                                                                'service_times': [DateTimeRange('2019-05-20T01:00:00+0000','1970-01-01T01:10:30+01:00'), 
                                                                                    DateTimeRange('1970-01-01T01:12:30+01:00','1970-01-01T01:18:26+01:00' ), 
                                                                                    DateTimeRange('1970-01-01T02:08:32+01:00', '1970-01-01T02:22:26+01:00'),
                                                                                    DateTimeRange('1970-01-01T02:24:11+01:00', '1970-01-01T02:33:09+01:00'),
                                                                                    DateTimeRange('1970-01-01T03:24:35+01:00', '1970-01-01T03:35:26+01:00'),
                                                                                    DateTimeRange('1970-01-01T03:38:12+01:00', '1970-01-01T03:46:48+01:00')],
                                                                'idle_times': [DateTimeRange('1970-01-01T01:10:30+01:00', '1970-01-01T01:12:30+01:00'), 
                                                                                DateTimeRange('1970-01-01T01:18:26+01:00', '1970-01-01T02:08:32+01:00'),
                                                                                DateTimeRange('1970-01-01T02:22:26+01:00', '1970-01-01T02:24:11+01:00'),
                                                                                DateTimeRange('1970-01-01T02:33:09+01:00', '1970-01-01T03:24:35+01:00'),
                                                                                DateTimeRange('1970-01-01T03:35:26+01:00', '1970-01-01T03:38:12+01:00')]}, 
                            'a': {'waiting_times': [DateTimeRange('1970-01-01T01:00:00+01:00','1970-01-01T01:00:00+01:00')], 
                                    'service_times': [DateTimeRange('1970-01-01T01:00:00+01:00','1970-01-01T01:10:30+01:00')]},
                            "->( 'c', 'd' )": {'waiting_times':[DateTimeRange('1970-01-01T01:10:30+01:00','1970-01-01T01:12:30+01:00'),
                                                                DateTimeRange('1970-01-01T02:22:26+01:00','1970-01-01T02:24:11+01:00')],
                                                'service_times': [DateTimeRange('1970-01-01T01:12:30+01:00','1970-01-01T01:18:26+01:00'),
                                                                  DateTimeRange('1970-01-01T02:08:32+01:00','1970-01-01T02:22:26+01:00'),
                                                                  DateTimeRange('1970-01-01T02:24:11+01:00','1970-01-01T02:33:09+01:00'),
                                                                  DateTimeRange('1970-01-01T03:24:35+01:00','1970-01-01T03:35:26+01:00')],
                                                'idle_times': [DateTimeRange('1970-01-01T01:18:26+01:00','1970-01-01T02:08:32+01:00'),
                                                                DateTimeRange('1970-01-01T02:33:09+01:00','1970-01-01T03:24:35+01:00')]},
                            "*( ->( 'c', 'd' ), tau)":{'waiting_times': [DateTimeRange('2019-05-20T12:30:00+0000','2019-05-20T12:51:00+0000')],
                                                'service_times': [DateTimeRange('1970-01-01T01:12:30+01:00','1970-01-01T01:18:26+01:00'),
                                                                  DateTimeRange('1970-01-01T02:08:32+01:00','1970-01-01T02:22:26+01:00'),
                                                                  DateTimeRange('1970-01-01T02:24:11+01:00','1970-01-01T02:33:09+01:00'),
                                                                  DateTimeRange('1970-01-01T03:24:35+01:00','1970-01-01T03:35:26+01:00')],
                                                'idle_times': [DateTimeRange('1970-01-01T01:18:26+01:00','1970-01-01T02:08:32+01:00'),
                                                               DateTimeRange('1970-01-01T02:22:26+01:00','1970-01-01T02:24:11+01:00'),
                                                               DateTimeRange('1970-01-01T02:33:09+01:00','1970-01-01T03:24:35+01:00')]},
                            'c':{'waiting_times':[DateTimeRange('1970-01-01T01:10:30+01:00','1970-01-01T01:12:30+01:00'),
                                                 DateTimeRange('1970-01-01T02:22:26+01:00','1970-01-01T02:24:11+01:00')],
                                  'service_times': [DateTimeRange('1970-01-01T01:12:30+01:00','1970-01-01T01:18:26+01:00'),
                                                    DateTimeRange('1970-01-01T02:24:11+01:00','1970-01-01T02:33:09+01:00')]},      
                            'd':{'waiting_times': [DateTimeRange('1970-01-01T01:18:26+01:00','1970-01-01T02:08:32+01:00'),
                                                   DateTimeRange('1970-01-01T02:33:09+01:00','1970-01-01T03:24:35+01:00')],
                                  'service_times': [DateTimeRange('1970-01-01T02:08:32+01:00','1970-01-01T02:22:26+01:00'),
                                                    DateTimeRange('1970-01-01T03:24:35+01:00','1970-01-01T03:35:26+01:00')]},
							'b':{'waiting_times': [DateTimeRange('1970-01-01T03:35:26+01:00','1970-01-01T03:38:12+01:00')],
                                  'service_times': [DateTimeRange('1970-01-01T03:38:12+01:00','1970-01-01T03:46:48+01:00')]}}
        
    def test_time_range_construction(self):
        use_case = measurement.TimeRangesConstructionUseCase(self.log, self.extended_process_tree, self.model, self.initial_marking, self.final_marking, self.alignments) 
        response = use_case.construct_time_ranges(self.log,
                                                    self.alignments, 
                                                    self.model, 
                                                    self.initial_marking, 
                                                    self.final_marking)
        for node in response.value.get_nodes_bottom_up():
            self.assertDictEqual(self.time_ranges[node.__str__()], node.kpis)
    
    def test_time_range_construction_with_loops(self):
        use_case = measurement.TimeRangesConstructionUseCase(self.log_with_loops, self.extended_process_tree_with_loops, 
                                                                self.model_with_loops, self.initial_marking_with_loops, 
                                                                self.final_marking_with_loops, self.alignments_with_loops) 
        response = use_case.construct_time_ranges(self.log_with_loops,
                                                    self.alignments_with_loops, 
                                                    self.model_with_loops, 
                                                    self.initial_marking_with_loops, 
                                                    self.final_marking_with_loops)
        for node in response.value.get_nodes_bottom_up():
            self.assertDictEqual(self.time_ranges[node.__str__()], node.kpis)
        
    # def test_waiting_time_shifting_on_parallel_construction_with_no_gains(self):
    #     use_case = measurement.TimeRangesConstructionUseCase(self.log, self.extended_process_tree, self.model, self.initial_marking, self.final_marking, self.alignments) 
    #     parameters={'delta':0.2, 'kpi':'waiting_time','target_node':{'name':'c'}} 
    #     request_object = request_objects.TimeShiftingRequestObject.from_dict(parameters)
    #     response = use_case.shift_time_ranges(request_object)
    #     for node in response.value.get_nodes_bottom_up():
    #         self.assertDictEqual(self.waiting_shifted_time_ranges_with_no_gains[node.__str__()], node.kpis)
    
    # def test_waiting_time_shifting_on_parallel_construction_with_gains(self):
    #     use_case = measurement.TimeRangesConstructionUseCase(self.log, self.extended_process_tree, self.model, self.initial_marking, self.final_marking, self.alignments) 
    #     parameters={'delta':0.2, 'kpi':'waiting_time','target_node':{'name':'b'}} 
    #     request_object = request_objects.TimeShiftingRequestObject.from_dict(parameters)
    #     response = use_case.shift_time_ranges(request_object)
    #     for node in response.value.get_nodes_bottom_up():
    #         self.assertDictEqual(self.waiting_shifted_time_ranges_with_gains[node.__str__()], node.kpis)
    
    # def test_service_time_shifting_on_parallel_construction_with_gains(self):
    #     use_case = measurement.TimeRangesConstructionUseCase(self.log, self.extended_process_tree, self.model, self.initial_marking, self.final_marking, self.alignments) 
    #     parameters={'delta':0.2, 'kpi':'service_time','target_node':{'name':'b'}} 
    #     request_object = request_objects.TimeShiftingRequestObject.from_dict(parameters)
    #     response = use_case.shift_time_ranges(request_object)
    #     for node in response.value.get_nodes_bottom_up():
    #         self.assertDictEqual(self.service_shifted_time_ranges_with_gains[node.__str__()], node.kpis) 
    
    # def test_service_time_shifting_on_parallel_construction_with_no_gains(self):
    #     use_case = measurement.TimeRangesConstructionUseCase(self.log, self.extended_process_tree, self.model, self.initial_marking, self.final_marking, self.alignments) 
    #     parameters={'delta':0.2, 'kpi':'service_time','target_node':{'name':'c'}} 
    #     request_object = request_objects.TimeShiftingRequestObject.from_dict(parameters)
    #     response = use_case.shift_time_ranges(request_object)
    #     for node in response.value.get_nodes_bottom_up():
    #         self.assertDictEqual(self.service_shifted_time_ranges_with_no_gains[node.__str__()], node.kpis) 