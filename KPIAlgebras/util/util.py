from KPIAlgebras.entities.model import ExtendedProcessTree
from pm4py.objects.process_tree.pt_operator import Operator as pt_opt
from pm4py.objects import petri
from pm4py.objects.petri import utils as petri_net_utils
from pm4py.util import xes_constants as xes_util

def is_atomic(event_label, log):
    start = None
    complete = None
    for trace in log:
        if start is None or not start:
            start = [event for event in trace if
                     event["concept:name"] == event_label and event["lifecycle:transition"] == "start"]
        if complete is None or not complete:
            complete = [event for event in trace if
                        event["concept:name"] == event_label and event["lifecycle:transition"] == "complete"]
        if start and complete:
            break

    return True if not start or not complete else False


# def unfold_leafs(tree, log, parameters=None):
#     if "classifier_name" in parameters and (parameters["classifier_name"] == "MXML Legacy Classifier" or
#                                             parameters["classifier_name"] == "customClassifier"):                                   
#         atomic_leafs = []
#         for leaf in tree.get_leafs():
#             index = tree.children.index(leaf)
#             tree.children.remove(leaf)
#             if not is_atomic(leaf.label, log):
#                 if tree.operator == pt_opt.SEQUENCE:
#                     tree.children[index:index] = [ExtendedProcessTree(None, tree, None, (leaf.label + "+start")),
#                                                   ExtendedProcessTree(None, tree, None, (leaf.label + "+complete"))]
#                 else:
#                     children = [ExtendedProcessTree(None, tree, None, (leaf.label + "+start")),
#                                 ExtendedProcessTree(None, tree, None, (leaf.label + "+complete"))]
#                     tree.children[index:index] = [ExtendedProcessTree(pt_opt.SEQUENCE, tree, children, None)]
#             else:
#                 atomic_leafs.append(leaf.label)
#                 tree.children[index:index] = [ExtendedProcessTree(None, tree, None, (leaf.label + "+complete"))]
#         if atomic_leafs:
#             if "atomic_leafs" in parameters:
#                 for leaf in atomic_leafs:
#                     if leaf not in parameters["atomic_leafs"]:
#                         parameters["atomic_leafs"].append(leaf)
#             else:
#                 parameters["atomic_leafs"] = atomic_leafs
#         for node in nodes:
#             node = unfold_leafs(node, log, parameters)

#     return tree

def overlap(instance, next_instance):
    return (instance["timestamps"][0] < next_instance["timestamps"][1]  and
            next_instance["timestamps"][0]  < instance["timestamps"][1])  

def add_connections(instance, trace_net, instances):
    transition = petri_net_utils.get_transition_by_name(trace_net, 't_' + instance["name"] + '_' + str(instances.index(instance)))
    post_instances = [i for i in instances if instances.index(i) > instances.index(instance)]
    
    for post_instance in post_instances:
        if not overlap(instance, post_instance):
            post_transition = petri_net_utils.get_transition_by_name(trace_net, 't_' + post_instance["name"] + '_' + str(instances.index(post_instance)))
            place = petri.petrinet.PetriNet.Place('p_'+ str(len(trace_net.places)))
            trace_net.places.add(place)
            petri_net_utils.add_arc_from_to(transition, place, trace_net)
            petri_net_utils.add_arc_from_to(place, post_transition, trace_net)

def add_log_orderring_to_event_net(trace_net, instances):
    for i in range(0, len(instances) - 1):
        instance = instances[i]
        add_connections(instance, trace_net, instances)  

def get_trace_activity_instances(trace):
    open_instances = []
    instances = []

    for event in trace:
        if event["lifecycle:transition"] == "start":
            open_instances.append(event["concept:name"])
            instances.append({'name': event["concept:name"], 
                              'timestamps': [event["time:timestamp"], None]})
        elif event["lifecycle:transition"] == "complete":
            if event["concept:name"] in open_instances:
                open_instances.remove(event["concept:name"])
                open_instance = next(instance for instance in instances if instance["timestamps"][1] is None and 
                                instance["name"] == event["concept:name"])
                open_instance["timestamps"][1] = event["time:timestamp"]
            else:
                instances.append({'name': event["concept:name"], 
                                  'timestamps': [event["time:timestamp"],event["time:timestamp"]]})

    return instances

def construct_base_event_net(trace_net, instances):
    artificial_start_transition = petri_net_utils.add_transition(trace_net)
    artificial_end_transition = petri_net_utils.add_transition(trace_net)
    trace_net.transitions.add(artificial_start_transition)
    trace_net.transitions.add(artificial_end_transition)

    place = petri.petrinet.PetriNet.Place("init")
    trace_net.places.add(place)
    petri_net_utils.add_arc_from_to(place, artificial_start_transition, trace_net)

    i = 1
    for index, instance in enumerate(instances):
        place = petri.petrinet.PetriNet.Place('p_'+ str(i))
        trace_net.places.add(place)
        petri_net_utils.add_arc_from_to(artificial_start_transition, place , trace_net)
        transition = petri.petrinet.PetriNet.Transition('t_' + instance["name"] + '_' + str(index), instance["name"])
        trace_net.transitions.add(transition)
        petri_net_utils.add_arc_from_to(place, transition, trace_net)
        place = petri.petrinet.PetriNet.Place('p_'+ str(i+1))
        trace_net.places.add(place)
        petri_net_utils.add_arc_from_to(transition, place , trace_net)
        petri_net_utils.add_arc_from_to(place, artificial_end_transition, trace_net)
        i = i + 2

    place = petri.petrinet.PetriNet.Place('final')
    trace_net.places.add(place)
    petri_net_utils.add_arc_from_to(artificial_end_transition, place, trace_net) 


def get_initial_marking(trace_net):
    initial_place = [place for place in trace_net.places if place.name == "init"][0]
    initial_marking = petri.petrinet.Marking({initial_place:1})

    return initial_marking

def get_final_marking(trace_net):
    final_place = [place for place in trace_net.places if place.name == "final"][0]
    final_marking = petri.petrinet.Marking({final_place:1})

    return final_marking

def construct_partially_ordered_trace_net_cost_aware(trace, instances, costs, trace_name_key=xes_util.DEFAULT_NAME_KEY, activity_key=xes_util.DEFAULT_NAME_KEY):
    trace_net = net = petri.petrinet.PetriNet(
        'trace net of %s' % trace.attributes[trace_name_key] if trace_name_key in trace.attributes else ' ')
    
    instances = get_trace_activity_instances(trace)
    construct_base_event_net(trace_net, instances)
    add_log_orderring_to_event_net(trace_net, instances)
    initial_marking = get_initial_marking(trace_net)
    final_marking = get_final_marking(trace_net)
    cost_map = construct_cost_map(instances, trace_net, costs)
   
    return trace_net, initial_marking, final_marking, cost_map


def construct_cost_map(instances, trace_net, costs):
    cost_map = dict()
    
    for index, instance in enumerate(instances):
        transition = petri_net_utils.get_transition_by_name(trace_net, 't_' + instance["name"] + '_' + str(instances.index(instance)))
        cost_map[transition] = costs[index]
        
    return cost_map

def construct_partially_ordered_trace_net_cost_aware(trace, instances, costs, trace_name_key=xes_util.DEFAULT_NAME_KEY, activity_key=xes_util.DEFAULT_NAME_KEY):
    trace_net = net = petri.petrinet.PetriNet(
        'trace net of %s' % trace.attributes[trace_name_key] if trace_name_key in trace.attributes else ' ')
    
    instances = get_trace_activity_instances(trace)
    construct_base_event_net(trace_net, instances)
    add_log_orderring_to_event_net(trace_net, instances)
    initial_marking = get_initial_marking(trace_net)
    final_marking = get_final_marking(trace_net)
    cost_map = construct_cost_map(instances, trace_net, costs)
   
    return trace_net, initial_marking, final_marking, cost_map

