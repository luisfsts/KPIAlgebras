import os
import json
from flask import Blueprint, request, Response, current_app
from KPIAlgebras.util import constants, http_response_status_code
from KPIAlgebras.use_cases import import_event_log_use_case as import_log
from KPIAlgebras.use_cases import model_discovery_use_case as discovery
from KPIAlgebras.use_cases import alignment_computation_use_case as alignment
from KPIAlgebras.use_cases import time_range_construction_use_case as measurement_fine_grained
from KPIAlgebras.use_cases import cycle_time_analysis_use_case as measurement_high_level
from KPIAlgebras.serializers import extended_process_tree_serializer as serializer
from KPIAlgebras.request_objects import request_objects 
from pm4py.objects.conversion.process_tree.converter import to_petri_net_transition_bordered as converter
from pm4py.objects.process_tree import util as process_tree_util
from KPIAlgebras.entities import model as model_object
from KPIAlgebras.entities import data

blueprint = Blueprint('measurement', __name__)


@blueprint.route('/measurement', methods=['POST'])
def measurement():
    parameters =  dict()
    file = request.files['eventLog']
    file.save(os.path.join(constants.upload_folder, file.filename))
    
    import_log_use_case = import_log.ImportEventLogUseCase()
    request_object = request_objects.TimeRangeConstructionRequestObject.from_dict({'event_log': file.filename})
    log = data.EventLog(import_log_use_case.import_event_log_from_xes(request_object))
    os.remove(os.path.join(constants.upload_folder, file.filename))

    # discovery_use_case = discovery.ModelDiscoveryUseCase()
    # extended_process_tree = discovery_use_case.discover(log)
    process_tree = process_tree_util.parse("->( 'a' , +( 'b', 'c' ), 'd' )")
    extended_process_tree = model_object.ExtendedProcessTree(process_tree)
    model, initial_marking, final_marking = converter.apply(extended_process_tree)

    alignment_use_case = alignment.AlignmentComputationUseCase()
    alignments = alignment_use_case.compute(model, initial_marking, final_marking, log)

    high_level_use_case = measurement_high_level.CycleTimeAnalysisUseCase()
    high_level_response = high_level_use_case.analyse(log.log, alignments, extended_process_tree, model)
    extended_process_tree = high_level_response.value
    fine_grained_use_case = measurement_fine_grained.TimeRangesConstructionUseCase(log, extended_process_tree, model, initial_marking, final_marking, alignments) 
    response = fine_grained_use_case.construct_time_ranges(log.log, alignments, model, initial_marking, final_marking)

    current_app.process_tree = response.value

    return Response(json.dumps(response.value, cls=serializer.ExtendedProcessTreeJsonEncoder), mimetype='application/json',
                    status=http_response_status_code.STATUS_CODES[response.type])