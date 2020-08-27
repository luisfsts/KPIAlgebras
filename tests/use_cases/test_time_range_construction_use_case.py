import unittest
import os
from KPIAlgebras.entities import model, data
from KPIAlgebras.use_cases import time_range_construction_use_case as measurement
from pm4py.objects.conversion.process_tree.converter import to_petri_net_transition_bordered as converter
from pm4py.objects.log.importer.xes import factory as xesimporter
from pm4py.objects.process_tree import util as process_tree_util
from datetimerange import DateTimeRange
from datetime import datetime, timedelta

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
        
    def test_time_range_construction(self):
        use_case = measurement.TimeRangesConstructionUseCase(self.log, self.extended_process_tree, self.model, self.initial_marking, self.final_marking, self.alignments) 
        response = use_case.construct_time_ranges(self.log,
                                                    self.alignments, 
                                                    self.model, 
                                                    self.initial_marking, 
                                                    self.final_marking)
        for node in response.value.get_nodes_bottom_up():
            self.assertDictEqual(self.time_ranges[node.__str__()], node.kpis)
        
    def test_waiting_time_shifting_on_parallel_construction_with_no_gains(self):
        use_case = measurement.TimeRangesConstructionUseCase(self.log, self.extended_process_tree, self.model, self.initial_marking, self.final_marking, self.alignments) 
        delta = 0.2
        kpi = 'waiting_time'
        node = 'c' 
        response =  use_case.shift_time_ranges(node, kpi, delta)
        for node in response.value.get_nodes_bottom_up():
            self.assertDictEqual(self.waiting_shifted_time_ranges_with_no_gains[node.__str__()], node.kpis)
    
    def test_waiting_time_shifting_on_parallel_construction_with_gains(self):
        use_case = measurement.TimeRangesConstructionUseCase(self.log, self.extended_process_tree, self.model, self.initial_marking, self.final_marking, self.alignments) 
        delta = 0.2
        kpi = 'waiting_time'
        node = 'b' 
        response = use_case.shift_time_ranges(node, kpi, delta)
        for node in response.value.get_nodes_bottom_up():
            self.assertDictEqual(self.waiting_shifted_time_ranges_with_gains[node.__str__()], node.kpis)
    
    def test_service_time_shifting_on_parallel_construction_with_gains(self):
        use_case = measurement.TimeRangesConstructionUseCase(self.log, self.extended_process_tree, self.model, self.initial_marking, self.final_marking, self.alignments) 
        delta = 0.2
        kpi = 'service_time'
        node = 'b' 
        response = use_case.shift_time_ranges(node, kpi, delta)
        for node in response.value.get_nodes_bottom_up():
            self.assertDictEqual(self.service_shifted_time_ranges_with_gains[node.__str__()], node.kpis) 
    
    def test_service_time_shifting_on_parallel_construction_with_no_gains(self):
        use_case = measurement.TimeRangesConstructionUseCase(self.log, self.extended_process_tree, self.model, self.initial_marking, self.final_marking, self.alignments) 
        delta = 0.2
        kpi = 'service_time'
        node = 'c' 
        # date = DateTimeRange('2019-05-20T12:51:00+0000','2019-05-20T15:55:00+0000')
        # start = date.start_datetime
        # end = date.end_datetime
        # duration = end - start
        # shiftting_amount = timedelta(seconds = duration.total_seconds() * delta)
        # new_date = end - shiftting_amount
        # date.set_end_datetime(new_date)
        # print(new_date)
        response = use_case.shift_time_ranges(node, kpi, delta)
        for node in response.value.get_nodes_bottom_up():
            self.assertDictEqual(self.service_shifted_time_ranges_with_no_gains[node.__str__()], node.kpis) 