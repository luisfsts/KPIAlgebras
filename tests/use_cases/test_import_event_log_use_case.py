import unittest
from unittest import mock
import os
from util import constants
from KPIAlgebras.use_cases import import_event_log_use_case as importer
from KPIAlgebras.request_objects import request_objects

class TestImportEventLogUseCase(unittest.TestCase):
    def setUp(self):
        self.file_name = 'partially_ordered_test_log2.xes'

    def test_import_event_log_from_xes(self):
        use_case = importer.ImportEventLogUseCase()
        request_object = request_objects.TimeRangeConstructionRequestObject.from_dict({'event_log': self.file_name})
        event_log = use_case.import_event_log_from_xes(request_object)
        self.assertEqual(len(event_log), 1)