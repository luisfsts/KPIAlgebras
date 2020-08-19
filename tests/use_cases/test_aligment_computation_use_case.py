import unittest
import os
from util import constants
from pm4py.objects.log.importer.xes import factory as xesimporter
from pm4py.objects.process_tree import util as process_tree_util
from KPIAlgebras.use_cases import alignment_computation_use_case as alignment
from KPIAlgebras.entities import model, data


class TestAligmentComputationUseCase(unittest.TestCase):
    def setUp(self):
        file_name = "partially_ordered_test_log.xes"
        path = os.path.join('/GitHub/KPIAlgebras/tests/files', file_name)
        self.log = data.EventLog(xesimporter.import_log(path))

        process_tree = process_tree_util.parse("->( 'a' , +( 'b', 'c' ), 'd' )")
        self.mock_extended_process_tree = model.ExtendedProcessTree(process_tree)

    def test_alignment_computation(self):
        use_case = alignment.AlignmentComputationUseCase()
        alignments = use_case.compute(self.mock_extended_process_tree, self.log)
        print(alignments)
        self.assertEqual(len(alignments), 1)



if __name__ == "__main__":
    unittest.main()
