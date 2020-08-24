import unittest
from KPIAlgebras.entities import model, data
from KPIAlgebras.use_cases import cycle_time_analysis_use_case as measurement
from pm4py.objects.log.importer.xes import factory as xesimporter
from pm4py.objects.conversion.process_tree.converter import to_petri_net_transition_bordered as converter
from pm4py.objects.process_tree import util as process_tree_util
from datetimerange import DateTimeRange
from datetime import datetime, timedelta
import os

class TestCycleTimeAnalysisUseCase(unittest.TestCase):
    def setUp(self):
        file_name = "partially_ordered_test_log.xes"
        path = os.path.join('/GitHub/KPIAlgebras/tests/files', file_name)
        self.event_log = data.EventLog(xesimporter.import_log(path))
        self.log = self.event_log.log
        self.process_tree = process_tree_util.parse("->( 'a' , +( 'b', 'c' ), 'd' )")
        self.extended_process_tree = model.ExtendedProcessTree(self.process_tree)
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
        self.time_ranges = {"->( 'a', +( 'b', 'c' ), 'd' )": {'cycle_times':[DateTimeRange('2019-05-20T01:00:00+0000','2019-05-21T17:06:00+0000')]}, 
                            'a': {'cycle_times': [DateTimeRange('2019-05-20T01:00:00+0000','2019-05-20T12:30:00+0000')]},
                            "+( 'b', 'c' )": {'cycle_times':[DateTimeRange('2019-05-20T12:30:00+0000','2019-05-21T14:14:00+0000')]},
                            'c':{'cycle_times': [DateTimeRange('2019-05-20T12:30:00+0000','2019-05-20T15:55:00+0000')]},
                            'b':{'cycle_times': [DateTimeRange('2019-05-20T12:30:00+0000','2019-05-21T14:14:00+0000')]},      
                            'd':{'cycle_times': [DateTimeRange('2019-05-21T14:14:00+0000','2019-05-21T17:06:00+0000')]}}

    def test_cycle_time_analysis_use_case(self):
        use_case = measurement.CycleTimeAnalysisUseCase()
        ranges = use_case.analyse(self.log, self.alignments, self.extended_process_tree, self.model)
        self.assertDictEqual(self.time_ranges, ranges)