from KPIAlgebras.response_objects import response_objects

STATUS_CODES = {
    response_objects.ResponseSuccess.SUCCESS: 200,
    # response_objects.ResponseFailure.RESOURCE_ERROR: 404,
    response_objects.ResponseFailure.PARAMETERS_ERROR: 400
    # res.ResponseFailure.SYSTEM_ERROR: 500
}