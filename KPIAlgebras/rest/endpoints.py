import os
import json
import copy
from flask import Blueprint, request, Response, current_app
from KPIAlgebras.util import constants, http_response_status_code
from KPIAlgebras.use_cases import import_event_log_use_case as import_log
from KPIAlgebras.use_cases import model_discovery_use_case as discovery
from KPIAlgebras.use_cases import alignment_computation_use_case as alignment
from KPIAlgebras.use_cases import time_range_construction_use_case as measurement_fine_grained
from KPIAlgebras.use_cases import cycle_time_analysis_use_case as measurement_high_level
from KPIAlgebras.use_cases import decorate_extended_process_tree_use_case as decorate_tree
from KPIAlgebras.serializers import extended_process_tree_serializer as serializer
from KPIAlgebras.request_objects import request_objects 
from pm4py.objects.conversion.process_tree.converter import to_petri_net_transition_bordered as converter
from pm4py.objects.process_tree import util as process_tree_util
from KPIAlgebras.entities import model as model_object
from KPIAlgebras.entities import data
from pm4py.visualization.common.utils import get_base64_from_gviz
from KPIAlgebras.response_objects import response_objects
import time

blueprint = Blueprint('endpoints', __name__)
alignments = None
log = None
model = None
initial_marking = None
final_marking = None
extended_process_tree = None

@blueprint.route('/measurement', methods=['POST'])
def measurement():
    print("Begining the fine grained analysis")
    t1 = time.perf_counter()
    parameters =  dict()
    file = request.files['eventLog']
    file.save(os.path.join(constants.upload_folder, file.filename))
    
    import_log_use_case = import_log.ImportEventLogUseCase()
    request_object = request_objects.TimeRangeConstructionRequestObject.from_dict({'event_log': file.filename})
    global log
    log = data.EventLog(import_log_use_case.import_event_log_from_xes(request_object))
    os.remove(os.path.join(constants.upload_folder, file.filename))

    # discovery_use_case = discovery.ModelDiscoveryUseCase()
    # extended_process_tree = discovery_use_case.discover(log)
    process_tree = process_tree_util.parse("->( 'a' , +( 'b', 'c' ), 'd' )")
    # process_tree = process_tree_util.parse("->('start', +('a', ->('b', 'c', 'd')), 'end')")
    # process_tree = process_tree_util.parse("->('Create Fine', X(tau, ->('Send Fine', 'Insert Fine Notification')), +(X(tau, 'Add penalty'), X(tau, 'Payment')), X(tau, 'Send for Credit Collection'))")
    global extended_process_tree
    extended_process_tree = model_object.ExtendedProcessTree(process_tree)
    global model, initial_marking, final_marking
    model, initial_marking, final_marking = converter.apply(extended_process_tree)

    alignment_use_case = alignment.AlignmentComputationUseCase()
    global alignments
    alignments = alignment_use_case.compute(model, initial_marking, final_marking, log)

    high_level_use_case = measurement_high_level.CycleTimeAnalysisUseCase()
    high_level_response = high_level_use_case.analyse(log.log, alignments, extended_process_tree, model)
    extended_process_tree = high_level_response.value
    fine_grained_use_case = measurement_fine_grained.TimeRangesConstructionUseCase(log, extended_process_tree, model, initial_marking, final_marking, alignments) 
    response = fine_grained_use_case.construct_time_ranges(log.log, alignments, model, initial_marking, final_marking)

    decoration_use_case = decorate_tree.DecorateExtendedProcessTreeUseCase()
    gviz = decoration_use_case.decorate(extended_process_tree)
    svg = get_base64_from_gviz(gviz)

    extended_process_tree_json = json.dumps(response.value, cls=serializer.ExtendedProcessTreeJsonEncoder)
    json_dict = json.loads(extended_process_tree_json)
    json_dict["svg"] = svg.decode('utf-8')

    extended_process_tree_json = json.dumps(json_dict, cls=serializer.ExtendedProcessTreeJsonEncoder) 
    t2 = time.perf_counter()
    print(t2-t1)
    return Response(extended_process_tree_json, mimetype='application/json',
                    status=http_response_status_code.STATUS_CODES[response.type])

@blueprint.route('/timeshifting', methods=['POST'])
def timeshifting():
    parameters = request.get_json()

    if parameters is None:
        parameters = dict()
        for arg, value in request.args.items():
            parameters[arg] = value
                
    request_object = request_objects.TimeShiftingRequestObject.from_dict(parameters)

    global log, model, initial_marking, final_marking, extended_process_tree, alignments
    extended_process_tree.states.append(copy.deepcopy(extended_process_tree))        
    fine_grained_use_case = measurement_fine_grained.TimeRangesConstructionUseCase(log.log, extended_process_tree, model, initial_marking, final_marking, alignments) 
    response =  fine_grained_use_case.shift_time_ranges(request_object)

    decoration_use_case = decorate_tree.DecorateExtendedProcessTreeUseCase()
    gviz = decoration_use_case.decorate(extended_process_tree)
    svg = get_base64_from_gviz(gviz)
    extended_process_tree_json = json.dumps(response.value, cls=serializer.ExtendedProcessTreeJsonEncoder)
    json_dict = json.loads(extended_process_tree_json)
    json_dict["svg"] = svg.decode('utf-8')

    extended_process_tree_json = json.dumps(json_dict, cls=serializer.ExtendedProcessTreeJsonEncoder) 

    return  Response(extended_process_tree_json, mimetype='application/json',
                    status=http_response_status_code.STATUS_CODES[response.type])

@blueprint.route('/undoChange', methods=['GET'])
def undo_change():
    global extended_process_tree
    extended_process_tree = extended_process_tree.states.pop() 
    decoration_use_case = decorate_tree.DecorateExtendedProcessTreeUseCase()
    gviz = decoration_use_case.decorate(extended_process_tree)
    svg = get_base64_from_gviz(gviz)
    extended_process_tree_json = json.dumps(extended_process_tree, cls=serializer.ExtendedProcessTreeJsonEncoder)
    json_dict = json.loads(extended_process_tree_json)
    json_dict["svg"] = svg.decode('utf-8')
    extended_process_tree_json = json.dumps(json_dict, cls=serializer.ExtendedProcessTreeJsonEncoder) 
    return Response(extended_process_tree_json, mimetype='application/json',
                    status=http_response_status_code.STATUS_CODES[response_objects.ResponseSuccess.SUCCESS])

@blueprint.route('/undoAllChanges', methods=['GET'])
def undo_all_changes():
    global extended_process_tree
    extended_process_tree = extended_process_tree.states[0]
    decoration_use_case = decorate_tree.DecorateExtendedProcessTreeUseCase()
    gviz = decoration_use_case.decorate(extended_process_tree)
    svg = get_base64_from_gviz(gviz)
    extended_process_tree_json = json.dumps(extended_process_tree, cls=serializer.ExtendedProcessTreeJsonEncoder)
    json_dict = json.loads(extended_process_tree_json)
    json_dict["svg"] = svg.decode('utf-8')
    extended_process_tree_json = json.dumps(json_dict, cls=serializer.ExtendedProcessTreeJsonEncoder) 
    return Response(extended_process_tree_json, mimetype='application/json',
                    status=http_response_status_code.STATUS_CODES[response_objects.ResponseSuccess.SUCCESS])