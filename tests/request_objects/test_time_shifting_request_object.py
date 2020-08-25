import unittest
from KPIAlgebras.request_objects import request_objects 

class TestTimeShiftingRequestObject(unittest.TestCase):
    def test_kpi_measurement_with_valid_request(self):
        request = request_objects.TimeShiftingRequestObject({'target_node':"b", "delta": "0.2" })
        self.assertDictEqual(request.parameters, {'target_node':"b", "delta": "0.2"})
        self.assertTrue(bool(request))
    
    def test_kpi_measurement_with_missing_delta(self):
        request = request_objects.TimeShiftingRequestObject.from_dict({'target_node':"b"})
        self.assertTrue(request.has_errors)
        self.assertEquals(request.errors[0]['parameter'],"Delta")
    
    def test_kpi_measurement_with_missing_target_node(self):
        request = request_objects.TimeShiftingRequestObject.from_dict({"delta": "0.2" })
        self.assertTrue(request.has_errors)
        self.assertEquals(request.errors[0]['parameter'],"Target Node")