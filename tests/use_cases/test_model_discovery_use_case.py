import unittest
import os
from pm4py.objects.process_tree import util as process_tree_util
from KPIAlgebras.entities import model
from KPIAlgebras.use_cases import model_discovery_use_case as m
from pm4py.objects.log.importer.xes import factory as xes_importer
from util import constants


class TestModelDiscoveryUseCase(unittest.TestCase):
    def setUp(self):
        process_tree = process_tree_util.parse("->( *( X( 'a' ), tau), +( 'b', 'c' ), *( X( 'd' ), tau ) )")
        self.mock_extended_process_tree = model.ExtendedProcessTree(process_tree)

        file_name = 'partially_ordered_test_log.xes'
        path = os.path.join(constants.test_upload_folder,file_name)
        self.log = xes_importer.import_log(path)

    def test_model_discovery(self):
        use_case = m.ModelDiscoveryUseCase()
        extended_process_tree = use_case.discover(self.log)
        self.assertEqual(self.mock_extended_process_tree.get_leaves().__str__(),extended_process_tree.get_leaves().__str__())