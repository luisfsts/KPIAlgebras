import re
from datetimerange import DateTimeRange
from datetime import datetime, timedelta
from KPIAlgebras.entities.data import EventLog as log
from KPIAlgebras.entities.model import PetriNet, PetriNetSemantics
from KPIAlgebras.response_objects import response_objects as response
from pm4py.objects.process_tree import pt_operator
import time
from copy import copy, deepcopy

class TimeRangesConstructionUseCase(object):
    def __init__(self, log, extended_process_tree, model, initial_marking, final_marking, alignments):
        self.log = log
        self.model = model
        self.initial_marking = initial_marking
        self.final_marking = final_marking
        self.alignments = alignments
        self.target_nodes = dict()
        self.shiftting_amount = timedelta()
        self.target_node = None
        self.extended_process_tree = extended_process_tree
        
    def construct_time_ranges(self, log, alignment, model, initial_marking, final_marking):
        print("Begining the fine grained analysis")
        t1 = time.perf_counter()
        time_interval_map = dict()
        for index, trace in enumerate(log):
            # print(index)
            instances = self.get_activities_time_instances(trace, alignment[index], model)
            timed_marking = self.get_timed_marking(initial_marking, trace[0]["time:timestamp"])
            self.construct_ranges(instances, alignment[index], model, timed_marking, time_interval_map)
            self.update_extended_tree(time_interval_map)
            time_interval_map.clear()
        t2 = time.perf_counter()
        print(t2-t1)
        return response.ResponseSuccess(self.extended_process_tree)
    
    def shift_time_ranges(self, request_object):
        node = request_object.parameters['target_node']
        kpi =  request_object.parameters['kpi']
        delta = float(request_object.parameters['delta'])
        time_interval_map = dict()
        self.clear_tree_kpis()
        
        for index, trace in enumerate(self.log):
            # print(index)
            instances = self.get_activities_time_instances(trace, self.alignments[index], self.model)
            timed_marking = self.get_timed_marking(self.initial_marking, trace[0]["time:timestamp"])
            self.construct_ranges(instances, self.alignments[index], self.model, timed_marking, time_interval_map, node, kpi, delta)
            self.update_extended_tree(time_interval_map, node, kpi, delta)
            self.update_leaf_cycle_times(self.extended_process_tree, time_interval_map)
            # self.print_operators_cycle_times(self.extended_process_tree)
            time_interval_map.clear()
        
        self.update_operators_cycle_times(self.extended_process_tree)
        return response.ResponseSuccess(self.extended_process_tree)

    def clear_tree_kpis(self):
        nodes = self.extended_process_tree.get_nodes_bottom_up()
        for node in nodes:
            node.kpis.clear()

    def update_extended_tree(self, time_interval_map, target_node=None, param_kpi=None, delta=None):
        nodes = self.extended_process_tree.get_nodes_bottom_up()
        for node in [n for n in nodes if n.__str__() in time_interval_map and n.__str__() != "τ"]:
            for kpi in time_interval_map[node.__str__()]:
                if kpi in node.kpis:
                    node.kpis[kpi].extend(time_interval_map[node.__str__()][kpi])
                else:
                    node.kpis[kpi] = time_interval_map[node.__str__()][kpi]
        if target_node is not None and param_kpi is not None and delta is not None:
            change = {'node':target_node, 'kpi':param_kpi, 'delta':delta}
            self.extended_process_tree.change = change

    def update_leaf_cycle_times(self, extended_process_tree, time_interval_map):
        nodes = extended_process_tree.get_nodes_bottom_up()
        for node in nodes:
            waiting_ranges = []
            service_ranges = []
            if not node.children:
                start = min(time_interval_map[node.__str__()]["waiting_times"], key = lambda range: range.start_datetime).start_datetime
                end = max(time_interval_map[node.__str__()]["service_times"], key = lambda range: range.end_datetime).end_datetime
                if "cycle_times" not in node.kpis:
                    node.kpis["cycle_times"]=[DateTimeRange(start, end)]
                else:
                    node.kpis["cycle_times"].append(DateTimeRange(start, end)) 
    
    def update_operators_cycle_times(self, extended_process_tree):
        nodes = extended_process_tree.get_nodes_bottom_up()
        for node in nodes:
            waiting_ranges = []
            service_ranges = []
            if node.children:
                if node.operator != pt_operator.Operator.PARALLEL:
                    node.kpis["cycle_times"] = sum([child.get_avg_kpi_value("cycle_times") for child in node.children if "cycle_times" in child.kpis], timedelta())
                else:
                    node.kpis["cycle_times"] = max([child.get_avg_kpi_value("cycle_times") for child in node.children if "cycle_times" in child.kpis]) 

    def get_activities_time_instances(self, trace, alignment, model):
        open_instances = []
        instances = dict()

        for event in trace:
            if event["lifecycle:transition"] == "start":
                time_range = DateTimeRange()
                time_range.set_start_datetime(event["time:timestamp"])
                open_instances.append(event["concept:name"])
                if event["concept:name"] not in instances:
                    instances[event["concept:name"]] = [time_range]
                else:
                    instances[event["concept:name"]].append(time_range)
            elif event["lifecycle:transition"] == "complete":
                if event["concept:name"] in open_instances:
                    open_instances.remove(event["concept:name"])
                    open_instance = next(instance for instance in instances[event["concept:name"]] if instance.end_datetime is None)
                    open_instance.set_end_datetime(event["time:timestamp"])
                else:
                    instances[event["concept:name"]]= [DateTimeRange(event["time:timestamp"], event["time:timestamp"])]
        return instances
    
    def get_move_name(self, move):
        return move[0][1]
    
    def get_move_label(self, move):
        return move[1][1]

    def get_timed_marking(self, marking, time_stamp):
        timed_marking = dict()
        for key, value in marking.items():
            timed_marking[str(key)] = {'time':time_stamp, 'delta': None}
        return timed_marking

    def construct_ranges(self, activities_time_instances, alignment, model, initial_marking, time_interval_map, node=None, kpi=None, delta=None):
        border_transitions_map = self.construct_border_transitions_map(model)
        timed_marking = initial_marking
        active_subtrees = []
        self.target_node = node
        semantics = PetriNetSemantics(model)

        for move in alignment["alignment"]:
            if self.is_model_or_sync_move(move):
                transition = self.get_transition_from_move(move, model.transitions)
                name = transition.name if self.is_border(transition) else transition.label
                time = None

                if node is not None and name == node:
                    last_enabling_token = self.get_last_timed_enabling_token(transition, timed_marking)
                    if kpi == "waiting_time":
                        start = self.get_enabling_time_from_timed_marking(timed_marking, transition)
                        end = activities_time_instances[name][0].start_datetime
                    else:
                        start = activities_time_instances[name][0].start_datetime
                        end = activities_time_instances[name][0].end_datetime
                        
                    duration = end - start 
                    if last_enabling_token["delta"]:
                        last_enabling_token["delta"].append(delta)
                    else:
                        last_enabling_token["delta"]= [delta]
                    last_enabling_token["kpi"] = kpi
                    if last_enabling_token["shifting_amount"]:
                        last_enabling_token["shifting_amount"].append(timedelta(seconds = duration.total_seconds() * delta))
                    else:
                       last_enabling_token["shifting_amount"] = [timedelta(seconds = duration.total_seconds() * delta)]
                    
                    timed_marking[last_enabling_token["id"]] = last_enabling_token

                if self.is_border(transition) and self.is_start(transition):
                    active_subtrees.append(border_transitions_map[transition.name])
                    start = semantics.get_time_from_marking(timed_marking)
                    end = self.get_startinh_time_from_next_sync_move(move, alignment["alignment"], activities_time_instances)
                    last_enabling_token = self.get_last_timed_enabling_token(transition, timed_marking)
                    if last_enabling_token["delta"]:
                        for index, delta in enumerate(last_enabling_token["delta"]):
                            end = end - last_enabling_token["shifting_amount"][index]
                   
                    if border_transitions_map[transition.name] not in time_interval_map:
                        time_interval_map[border_transitions_map[transition.name]] = {"waiting_times": [DateTimeRange(start, end)]}
                    else:
                        time_interval_map[border_transitions_map[transition.name]]["waiting_times"].append(DateTimeRange(start, end))
                
                if not self.is_border(transition) and transition.label is not None:
                    self.construct_waiting_time_ranges(transition, activities_time_instances, timed_marking, time_interval_map, active_subtrees)
                    self.construct_service_time_ranges(transition, activities_time_instances, time_interval_map, active_subtrees, timed_marking)
                    activities_time_instances[name].remove(activities_time_instances[name][0])
                
                if self.is_border(transition) and self.is_end(transition):
                    active_subtree = active_subtrees.pop(active_subtrees.index(border_transitions_map[transition.name]))
                    self.construct_idle_time_ranges(time_interval_map, active_subtree)
                
                if name in time_interval_map:
                    time = time_interval_map[name]["service_times"][-1].end_datetime
                else:
                    time = semantics.get_time_from_marking(timed_marking)
                
                timed_marking = semantics.execute_with_timed_token(transition, timed_marking, time)
        # print(str(time_interval_map["d"]["waiting_times"][0].end_datetime - time_interval_map["d"]["waiting_times"][0].start_datetime))
        return time_interval_map
    
    def get_startinh_time_from_next_sync_move(self, border_move, alignments, activities_time_instances):
        for move in alignments[alignments.index(border_move):]:
            if move[0][0] != ">>" and move[0][1] != ">>":
                moves = [m for m in alignments if m[0][1] == move[0][1]]
                move_index = moves.index(move)
                return  activities_time_instances[move[1][1]][move_index].start_datetime

    def construct_idle_time_ranges(self, time_interval_map, active_subtree):
        if "service_times" in time_interval_map[active_subtree]:
            idle_times = []
            for index, time_range in enumerate(time_interval_map[active_subtree]["service_times"]):
                size= len(time_interval_map[active_subtree]["service_times"]) - 1
                if index < size:
                    range = DateTimeRange(time_range.end_datetime, time_interval_map[active_subtree]["service_times"][index+1].start_datetime)
                    if range not in time_interval_map[active_subtree]["waiting_times"]:
                        idle_times.append(range)
            
            time_interval_map[active_subtree]['idle_times'] = idle_times

    def construct_service_time_ranges(self, transition, activities_time_instances, time_interval_map, active_subtrees, timed_marking):
        activity_instances = activities_time_instances[transition.name] if self.is_border(transition) else activities_time_instances[transition.label]
        activity_name = transition.name if self.is_border(transition) else transition.label
        activity_label = self.get_subtree_name_from_border_transition(transition) if self.is_border(transition) else transition.label
        start = activities_time_instances[activity_name][0].start_datetime
        end = activities_time_instances[activity_name][0].end_datetime
        last_enabling_token =  self.get_last_timed_enabling_token(transition, timed_marking)

        if transition.label == self.target_node:
            if last_enabling_token["kpi"] == "waiting_time":
               start = start - last_enabling_token["shifting_amount"][-1]
               end = end - last_enabling_token["shifting_amount"][-1]
            else:
                end = end - last_enabling_token["shifting_amount"][-1]
              
            if last_enabling_token["delta"]:
                for index, delta in enumerate(last_enabling_token["delta"][:-1]):
                    start = start - last_enabling_token["shifting_amount"][index]
                    end = end - last_enabling_token["shifting_amount"][index]
        elif last_enabling_token["delta"]:
            for index, delta in enumerate(last_enabling_token["delta"]):
                start = start - last_enabling_token["shifting_amount"][index]
                end = end - last_enabling_token["shifting_amount"][index]
        
        time_range = DateTimeRange(start, end)
        
        for state in self.extended_process_tree.states:
            if bool(state.change):
                if transition.label == state.change["node"]:
                    shifting_amount = self.get_shifting_amount(state.change["kpi"], state.change["delta"], timed_marking, transition, time_range)
                    if state.change["kpi"] == "waiting_time":
                        time_range.set_start_datetime(start - shifting_amount)
                        time_range.set_end_datetime(end - shifting_amount)
                    else:
                        time_range.set_end_datetime(end - shifting_amount)
                    
                    if last_enabling_token["shifting_amount"]:
                        last_enabling_token["shifting_amount"].append(shifting_amount)
                    else:
                        last_enabling_token["shifting_amount"] = [shifting_amount]
                    if last_enabling_token["delta"]:
                        last_enabling_token["delta"].append(state.change["delta"])
                    else:
                        last_enabling_token["delta"] = [state.change["delta"]]
                    timed_marking[last_enabling_token["id"]] = last_enabling_token

        if activity_label in time_interval_map:
            if 'service_times' in  time_interval_map[activity_label]:
                time_interval_map[activity_label]['service_times'].append(time_range)
            else:
                time_interval_map[activity_label]['service_times'] = [time_range]
        else:
            time_interval_map[activity_label]={'service_times': [time_range]}
       
        for active_subtree in active_subtrees:
            if self.are_related(transition, active_subtree):
                if 'service_times' in time_interval_map[active_subtree]:
                    #TODO refactor: the union method is already modifiying the list
                    time_interval_map[active_subtree]["service_times"] = self.union(time_interval_map[active_subtree]["service_times"], 
                                                                                time_interval_map[activity_label]['service_times'])
                else:
                    time_interval_map[active_subtree]["service_times"] = time_interval_map[activity_label]['service_times'].copy()
    
    def are_related(self, transition, sub_tree_rep):
        sub_tree = [tree for tree in self.extended_process_tree.get_nodes_bottom_up() if tree.__str__() == sub_tree_rep][0]
        nodes = [node for node in sub_tree.get_nodes_bottom_up() if node.__str__() == transition.label]
        return bool(nodes)
        
    def get_shifting_amount(self, kpi, delta, timed_marking, transition, time_range):
        if kpi == "waiting_time":
            start = self.get_enabling_time_from_timed_marking(timed_marking, transition)
            end = time_range.start_datetime
        else:
            start = time_range.start_datetime
            end = time_range.end_datetime
        duration = end - start 
        return timedelta(seconds = duration.total_seconds() * delta)
    
    def union(self, time_interval_map_subtree, time_interval_map_activity):
        for time_range in time_interval_map_activity:
            intersection_set = self.getIntersections(time_range, time_interval_map_subtree)
            if intersection_set:
                merged_ranges = self.merge_intervals(time_range, intersection_set)
                for range in merged_ranges:
                    time_interval_map_subtree.append(range)
                for intersecting_range in intersection_set:
                    time_interval_map_subtree.remove(intersecting_range)
            else:
                time_interval_map_subtree.append(time_range)
        return sorted(time_interval_map_subtree, key= lambda x: x.start_datetime)

    def getIntersections(self, time_range, time_interval_map_subtree):
        return [range for range in time_interval_map_subtree if range.is_intersection(time_range) or time_range.is_intersection(range)]
    
    def merge_intervals(self, time_range, intersection_set):
        merged_intervals = []
        for range in intersection_set:
            merged_range = time_range.encompass(range)
            for merged_interval in merged_intervals:
                if merged_range.is_intersection(merged_interval) or merged_interval.is_intersection(merged_range):
                    merged_range = merged_range.encompass(merged_interval)
                    merged_intervals.remove(merged_interval)
            if merged_range not in merged_intervals:
                merged_intervals.append(merged_range)

        return merged_intervals

    def construct_waiting_time_ranges(self, transition, activities_time_instances, timed_marking, time_interval_map, active_subtrees):
        activity_instances = activities_time_instances[transition.name] if self.is_border(transition) else activities_time_instances[transition.label]
        start = self.get_enabling_time_from_timed_marking(timed_marking, transition)
        activity_name = transition.name if self.is_border(transition) else transition.label
        activity_label = self.get_subtree_name_from_border_transition(transition) if self.is_border(transition) else transition.label
        end = activities_time_instances[activity_name][0].start_datetime
        last_enabling_token =  self.get_last_timed_enabling_token(transition, timed_marking)

        if transition.label == self.target_node:
            if last_enabling_token["kpi"] == "waiting_time":
                end = end - last_enabling_token["shifting_amount"][-1]
            if last_enabling_token["delta"]:
                for index, delta in enumerate(last_enabling_token["delta"][:-1]):
                    end = end - last_enabling_token["shifting_amount"][index]
        elif last_enabling_token["delta"]:
            for index, delta in enumerate(last_enabling_token["delta"]):
                end = end - last_enabling_token["shifting_amount"][index]
        
        time_range = DateTimeRange(start, end)

        for state in self.extended_process_tree.states:
            if bool(state.change):
                if transition.label == state.change["node"]:
                    if state.change["kpi"] == "waiting_time":
                        shifting_amount = self.get_shifting_amount(state.change["kpi"], state.change["delta"], timed_marking, transition, time_range)
                        time_range.set_end_datetime(end - shifting_amount)
                        if last_enabling_token["shifting_amount"]:
                            last_enabling_token["shifting_amount"].append(shifting_amount)
                        else:
                            last_enabling_token["shifting_amount"] = [shifting_amount]
                        if last_enabling_token["delta"]:
                            last_enabling_token["delta"].append(state.change["delta"])
                        else:
                            last_enabling_token["delta"] = [state.change["delta"]]
                        timed_marking[last_enabling_token["id"]] = last_enabling_token
        
        if activity_label in time_interval_map:
            if 'waiting_times' in  time_interval_map[activity_label]:
                time_interval_map[activity_label]['waiting_times'].append(time_range)
            else:
                time_interval_map[activity_label]['waiting_times'] = [time_range]
        else:
            time_interval_map[activity_label]={'waiting_times': [time_range]}

        # for active_subtree in active_subtrees:
        #     if self.are_related(transition, active_subtree):
        #         if 'waiting_times' not in time_interval_map[active_subtree]:
        #             time_interval_map[active_subtree]["waiting_times"] = time_interval_map[activity_label]['waiting_times'].copy()
        #         elif time_interval_map[activity_label]['waiting_times'].index(time_interval_map[activity_label]['waiting_times'][-1]) > (len(time_interval_map[active_subtree]["waiting_times"])-1): 
        #             time_interval_map[active_subtree]["waiting_times"].append(time_interval_map[activity_label]['waiting_times'][-1])
        #         elif time_interval_map[activity_label]['waiting_times'][-1].end_datetime < time_interval_map[active_subtree]["waiting_times"][-1].end_datetime: 
        #             index =  time_interval_map[active_subtree]["waiting_times"].index(time_interval_map[active_subtree]["waiting_times"][-1])
        #             time_interval_map[active_subtree]["waiting_times"][index] = time_interval_map[activity_label]['waiting_times'][-1]
                
    def get_last_timed_enabling_token(self, transition, timed_marking):
        enabling_timed_tokens = []
        for arc in transition.in_arcs:
            if str(arc.source) in timed_marking:
                enabling_timed_tokens.append(timed_marking[str(arc.source)])
        return deepcopy(max(enabling_timed_tokens, key=(lambda token: token["time"])))
        
    def get_enabling_time_from_timed_marking(self, timed_marking, transition):
        input_arcs_sources = [str(arc.source) for arc in transition.in_arcs]
        time_list = [timed_marking[source]['time'] for source in input_arcs_sources if source in timed_marking]
        return max(time for time in time_list)

    def construct_border_transitions_map(self, model):
        map = dict()
        
        for transition in model.transitions:
            if transition.label is None and self.is_border(transition):
                sub_tree_name = self.get_subtree_name_from_border_transition(transition)
                map[transition.name] = sub_tree_name

        return map

    def is_border(self, transition):
        return self.is_start(transition) or self.is_end(transition)

    def is_start(self, transition):
        return transition.name.endswith("_start")

    def is_end(self, transition):
        return transition.name.endswith("_end")    
    
    def get_subtree_name_from_border_transition(self, transition):
        if self.is_start(transition):
            suffix = "_start"
            suffix_index = re.search(suffix, transition.name).start()
            return transition.name[:suffix_index]
        else:
            suffix = "_end"
            suffix_index = re.search(suffix, transition.name).start()
            return transition.name[:suffix_index]
    
    def is_model_or_sync_move(self, move):
        return move[0][1] != ">>"

    def get_transition_from_move(self, move, transitions):
        return [transition for transition in transitions if transition.name == move[0][1]][0]

 

   

    
    
   
    
   