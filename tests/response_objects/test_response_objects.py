import unittest
from KPIAlgebras.response_objects import response_objects
from KPIAlgebras.request_objects import request_objects

class TestResponseObjects(unittest.TestCase):
    def test_response_sucess_is_true(self):
        value = "test"
        response_sucess = response_objects.ResponseSuccess(value)
        self.assertTrue(bool(response_sucess))

    def test_response_success_has_type_and_value(self):
        value = "test"
        response_success = response_objects.ResponseSuccess(value)
        self.assertEquals(response_success.value, value)
        self.assertEquals(response_success.type, response_objects.ResponseSuccess.SUCCESS)
        
    def test_response_failure_is_false(self):
        type = 'test)type'
        message = 'test_message'
        response_failure = response_objects.ResponseFailure(type, message)
        self.assertFalse(bool(response_failure))
    
    def test_response_failure_has_type_and_message(self):
        type = 'parameterserror'
        message = 'test_message'
        response_failure = response_objects.ResponseFailure(type, message)
        self.assertEquals(response_failure.type, type)
        self.assertEquals(response_failure.message, message)

    def test_response_failure_has_value(self):
        type = 'parameterserror'
        message = 'test_message'
        response_failure = response_objects.ResponseFailure(type, message)
        self.assertDictEqual(response_failure.value, {'type': type, 'message':message})

    def test_response_failure_build_from_invalid_request(self):
        invalid_request = request_objects.InvalidRequestObject()
        response_failure = response_objects.ResponseFailure.build_from_invalid_request(invalid_request)
        self.assertFalse(bool(response_failure))
        self.assertEquals(response_failure.type, response_objects.ResponseFailure.PARAMETERS_ERROR)

    def test_response_failure_build_from_invalid_request_with_errors(self):
        invalid_request = request_objects.InvalidRequestObject()
        invalid_request.add_error("Target Node", 'is missing')
        invalid_request.add_error("Delta", 'is missing')
        response_failure = response_objects.ResponseFailure.build_from_invalid_request(invalid_request)
        self.assertFalse(bool(response_failure))
        self.assertEquals(response_failure.type, response_objects.ResponseFailure.PARAMETERS_ERROR)
        self.assertEquals(response_failure.message, "Target Node: is missing\nDelta: is missing")