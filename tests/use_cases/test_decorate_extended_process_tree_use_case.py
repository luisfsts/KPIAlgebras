import unittest
import os
from KPIAlgebras.entities import model, data
from pm4py.objects.conversion.process_tree.converter import to_petri_net_transition_bordered as converter
from pm4py.objects.log.importer.xes import factory as xesimporter
from pm4py.objects.process_tree import util as process_tree_util
from datetimerange import DateTimeRange
from KPIAlgebras.use_cases import decorate_extended_process_tree_use_case

class TestDecorateExtendedProcessTreeUseCase(unittest.TestCase):
    def setUp(self):
        file_name = "partially_ordered_test_log.xes"
        path = os.path.join('/GitHub/KPIAlgebras/tests/files', file_name)
        self.event_log = data.EventLog(xesimporter.import_log(path))
        self.log = self.event_log
        process_tree = process_tree_util.parse("->( 'a' , +( 'b', 'c' ), 'd' )")
        self.extended_process_tree = model.ExtendedProcessTree(process_tree)
        self.model, self.initial_marking, self.final_marking = converter.apply(self.extended_process_tree)
        self.time_ranges = {"->( 'a', +( 'b', 'c' ), 'd' )": {'cycle_times':[DateTimeRange('2019-05-20T01:00:00+0000', '2019-05-21T17:06:00+0000')],
														'waiting_times':[DateTimeRange('2019-05-20T01:00:00+0000', '2019-05-20T01:00:00+0000')],
                                                                'service_times': [DateTimeRange('2019-05-20T01:00:00+0000','2019-05-20T12:30:00+0000'), 
                                                                                    DateTimeRange('2019-05-20T12:51:00+0000','2019-05-21T14:14:00+0000' ), 
                                                                                    DateTimeRange('2019-05-21T14:23:00+0000', '2019-05-21T17:06:00+0000')],
                                                                'idle_times': [DateTimeRange('2019-05-20T12:30:00+0000', '2019-05-20T12:51:00+0000'), 
                                                                                DateTimeRange('2019-05-21T14:14:00+0000', '2019-05-21T14:23:00+0000')]}, 
                            'a': {'cycle_times':[DateTimeRange('2019-05-20T01:00:00+0000', '2019-05-20T12:30:00+0000')],
								'waiting_times': [DateTimeRange('2019-05-20T01:00:00+0000','2019-05-20T01:00:00+0000')], 
                                    'service_times': [DateTimeRange('2019-05-20T01:00:00+0000','2019-05-20T12:30:00+0000')]},
                            "+( 'b', 'c' )": {'cycle_times':[DateTimeRange('2019-05-20T12:30:00+0000', '2019-05-21T14:14:00+0000')],
												'waiting_times':[DateTimeRange('2019-05-20T12:30:00+0000','2019-05-20T12:51:00+0000')],
                                                'service_times': [DateTimeRange('2019-05-20T12:51:00+0000','2019-05-21T14:14:00+0000')],
                                                'idle_times': []},
                            'c':{'cycle_times':[DateTimeRange('2019-05-20T12:30:00+0000', '2019-05-20T15:55:00+0000')],
									'waiting_times': [DateTimeRange('2019-05-20T12:30:00+0000','2019-05-20T12:51:00+0000')],
                                  'service_times': [DateTimeRange('2019-05-20T12:51:00+0000','2019-05-20T15:55:00+0000')]},
                            'b':{'cycle_times':[DateTimeRange('2019-05-20T12:30:00+0000', '2019-05-21T14:14:00+0000')],
								'waiting_times': [DateTimeRange('2019-05-20T12:30:00+0000','2019-05-20T15:02:00+0000')],
                                  'service_times': [DateTimeRange('2019-05-20T15:02:00+0000','2019-05-21T14:14:00+0000')]},      
                            'd':{'cycle_times':[DateTimeRange('2019-05-21T14:14:00+0000', '2019-05-21T17:06:00+0000')],
								'waiting_times': [DateTimeRange('2019-05-21T14:14:00+0000','2019-05-21T14:23:00+0000')],
                                  'service_times': [DateTimeRange('2019-05-21T14:23:00+0000','2019-05-21T17:06:00+0000')]}}
        
        for node in self.extended_process_tree.get_nodes_bottom_up():
            node.kpis = {**node.kpis,**self.time_ranges[node.__str__()]}

    def test_decorate_extende_process_tree_use_case(self):
        use_case = decorate_extended_process_tree_use_case.DecorateExtendedProcessTreeUseCase()
        response = use_case.decorate(self.extended_process_tree)
        self.assertIsNotNone(response)