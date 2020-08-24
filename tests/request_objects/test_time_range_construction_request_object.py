import unittest
from KPIAlgebras.request_objects import request_objects 

class TestTimeRangeConstructionRequest(unittest.TestCase):
    def test_kpi_measurement_with_valid_extensions(self):
        request = request_objects.TimeRangeConstructionRequestObject({'input':"partially_ordered_test_log.xes"})
        self.assertDictEqual(request.parameters, {'input':"partially_ordered_test_log.xes"})
        self.assertTrue(bool(request))
    
    def test_kpi_measurement_with_invalid_extensions(self):
        request = request_objects.TimeRangeConstructionRequestObject.from_dict({'input':"test.xlsx"})
        self.assertTrue(request.has_errors)
        self.assertEquals(request.errors[0]['parameter'],"Event log")
    
    def test_kpi_measurement_with_empty_input(self):
        request = request_objects.TimeRangeConstructionRequestObject.from_dict({})
        self.assertTrue(request.has_errors)
        self.assertEquals(request.errors[0]['parameter'],"Event log")