import unittest
import os
from util import constants
from pm4py.objects.log.importer.xes import factory as xes_importer
from KPIAlgebras.use_cases import alignment_computation_use_case 
from KPIAlgebras.entities import data


class TestEventlog(unittest.TestCase):
    def setUp(self):
        file_name = 'partially_ordered_test_log.xes'
        path = os.path.join(constants.test_upload_folder, file_name)
        self.log = data.EventLog(xes_importer.import_log(path))

    def test_event_log_creation(self):
        event_log = data.EventLog(self.log)
        self.assertIsNotNone(event_log.log)

if __name__ == "__main__":
    unittest.main()