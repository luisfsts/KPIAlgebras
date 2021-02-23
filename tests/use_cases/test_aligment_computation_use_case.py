import unittest
import os
from util import constants
from pm4py.objects.log.importer.xes import factory as xesimporter
from pm4py.objects.process_tree import util as process_tree_util
from KPIAlgebras.use_cases import alignment_computation_use_case as alignment
from KPIAlgebras.entities import model, data
from pm4py.objects.conversion.process_tree.converter import to_petri_net_transition_bordered as converter
from pm4py.visualization.petrinet import visualizer as pn_visualizer

class TestAligmentComputationUseCase(unittest.TestCase):
    def setUp(self):
        file_name = "Log for Process with loop.xes"
        path = os.path.join('/GitHub/KPIAlgebras/tests/files', file_name)
        self.log = data.EventLog(xesimporter.import_log(path))

        process_tree = process_tree_util.parse("->('a', *(->('c', 'd'), tau), 'b')")
        self.extended_process_tree = model.ExtendedProcessTree(process_tree)
        self.model, self.initial_marking, self.final_marking = converter.apply(self.extended_process_tree)
  
    def test_alignment_computation(self):
        use_case = alignment.AlignmentComputationUseCase()
        alignments = use_case.compute(self.model, self.initial_marking, self.final_marking, self.log)
        self.assertEqual(len(alignments), 1)



if __name__ == "__main__":
    unittest.main()
