import unittest
from unittest import mock
import os
from util import constants
# from pm4py.objects.log.importer.xes import factory as xes_importer
from KPIAlgebras.use_cases import import_event_log_use_case as importer


class TestImportEventLogUseCase(unittest.TestCase):
    def setUp(self):
        self.file_name = 'partially_ordered_test_log.xes'

    def test_import_event_log_from_xes(self):
        use_case = importer.ImportEventLogUseCase()
        event_log = use_case.import_event_log_from_xes(self.file_name)
        
        self.assertEqual(len(event_log), 1)