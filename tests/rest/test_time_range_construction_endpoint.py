import unittest
import os
from KPIAlgebras import app
from KPIAlgebras.response_objects import response_objects

class TestTimeRangeConstructionEndpoint(unittest.TestCase):
    def setUp(self):
        file_name = "partially_ordered_test_log.xes"
        path = os.path.join('/GitHub/KPIAlgebras/tests/files', file_name)
        self.file = open(path, 'rb')
        self.data = {'eventLog': (self.file, file_name)}
        self.app =  app.create_app().test_client()
        self.app.testing = True
        


    def test_time_range_construction_endpoint(self):
        http_response = self.app.post('/measurement', data = self.data)
        self.assertTrue(bool(http_response))
        self.assertEquals(http_response.status_code, 200)
        self.assertEquals(http_response.mimetype, 'application/json')