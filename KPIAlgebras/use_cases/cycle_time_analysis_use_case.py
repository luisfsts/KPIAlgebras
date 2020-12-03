from datetimerange import DateTimeRange
from KPIAlgebras.response_objects import response_objects as response
from pm4py.objects.process_tree import pt_operator
import datetime
import time
from pm4py.algo.filtering.log.variants import variants_filter
from copy import copy, deepcopy

class CycleTimeAnalysisUseCase(object):
    def analyse(self, log, alignments, process_tree, model):
        print("Begining the Cycle time analysis")
        t1 = time.perf_counter()
        time_interval_map = dict()
        self.enablers_map = dict()
        variants = variants_filter.get_variants(log)
        current_trace_variant = None

        for variant in variants:
            self.update_enablers_map(model.transitions, variant)

        for alignment_index, alignment in enumerate(alignments):
            for variant in variants:
                if log[alignment_index] in variants[variant]:
                    current_trace_variant = variant
                    break
            instances = self.get_activities_time_instances(log[alignment_index], alignment, model)
            self.construct_cycle_time_ranges(instances, alignment, time_interval_map, model, current_trace_variant)
            self.construct_cycle_time_ranges_for_Operators(process_tree, time_interval_map)
            if "Send Reminder" in time_interval_map:
                print([str((range.end_datetime - range.start_datetime).total_seconds()) for range in time_interval_map["Send Reminder"]["cycle_times"]])
            self.update_extended_tree(time_interval_map, process_tree, instances)
            time_interval_map.clear()
        t2 = time.perf_counter()
        print(t2-t1)
        return response.ResponseSuccess(process_tree)

    def update_extended_tree(self, time_interval_map, process_tree, instances):
        nodes = process_tree.get_nodes_bottom_up()
        for node in [n for n in nodes if n.__str__() in time_interval_map and n.__str__() != "τ"]:
            if not node.children:
                if node.__str__() in instances:
                    for kpi in time_interval_map[node.__str__()]:
                        if kpi in node.kpis:
                            node.kpis[kpi].extend(time_interval_map[node.__str__()][kpi])
                        else:
                            node.kpis[kpi] = time_interval_map[node.__str__()][kpi]
            else:
                for kpi in time_interval_map[node.__str__()]:
                        if kpi in node.kpis:
                            node.kpis[kpi].extend(time_interval_map[node.__str__()][kpi])
                        else:
                            node.kpis[kpi] = time_interval_map[node.__str__()][kpi]

    def get_activities_time_instances(self, trace, alignment, model):
        open_instances = []
        instances = dict()

        for event in trace:
            if event["lifecycle:transition"] == "start":
                time_range = DateTimeRange()
                time_range.set_start_datetime(event["time:timestamp"])
                open_instances.append(event["concept:name"])
                if event["concept:name"] in instances:
                    instances[event["concept:name"]].append(time_range)
                else:
                    instances[event["concept:name"]] = [time_range]
            elif event["lifecycle:transition"] == "complete":
                if event["concept:name"] in open_instances:
                    open_instances.remove(event["concept:name"])
                    open_instance = next(instance for instance in instances[event["concept:name"]] if instance.end_datetime is None)
                    open_instance.set_end_datetime(event["time:timestamp"])
                else:
                    if event["concept:name"] not in instances:
                        instances[event["concept:name"]]= [DateTimeRange(event["time:timestamp"], event["time:timestamp"])]
                    else:
                        instances[event["concept:name"]].append(DateTimeRange(event["time:timestamp"], event["time:timestamp"]))
        
        return instances

    def get_last_visible_move(self, move, alignment, instances):
        last_moves = [move for move in alignment["alignment"][:alignment["alignment"].index(move)] if self.get_move_label(move) is not None and self.get_move_label(move) != ">>" ]
        sorted_last_moves_list = sorted(last_moves, key=lambda x: instances[self.get_move_label(x)][-1].end_datetime)
        return sorted_last_moves_list[-1]
    
    def get_move_name(self, move):
        return move[0][1]
    
    def get_move_label(self, move):
        return move[1][1]

    def construct_cycle_time_ranges(self, activity_instances, alignment, time_interval_map, model,current_trace_variant):
        self.construct_cycle_time_ranges_for_leafs(activity_instances, alignment, time_interval_map, model, current_trace_variant)
        
    def construct_cycle_time_ranges_for_Operators(self, process_tree, time_interval_map):
        processed_children = dict()
        number_of_executions = None
        
        for node in process_tree.get_nodes_bottom_up():
            if node.children:
                if node.operator != pt_operator.Operator.XOR:
                    executions = [len(time_interval_map[child.__str__()]["cycle_times"]) for child in node.children if child.__str__() in time_interval_map]
                    number_of_executions = executions[0] if executions else 0
                else:
                    number_of_executions = len([time_interval_map[child.__str__()]["cycle_times"] for child in node.children if child.__str__() in time_interval_map]) 
                
                for child in node.children:
                    processed_children[child.__str__()] = False
                
                if node.operator == pt_operator.Operator.XOR:
                    time_ranges = []
                    for child in node.children:
                        if child.__str__() in time_interval_map:
                            if node.__str__() in time_interval_map:
                                time_interval_map[node.__str__()]['cycle_times'].extend(deepcopy(time_interval_map[child.__str__()]['cycle_times']))
                            else:
                                time_interval_map[node.__str__()]={'cycle_times': deepcopy(time_interval_map[child.__str__()]['cycle_times'])}
                    if node.__str__() in time_interval_map:
                        time_interval_map[node.__str__()]['cycle_times'] =  sorted(time_interval_map[node.__str__()]['cycle_times'], key = lambda range: range.start_datetime)
               
                elif node.operator == pt_operator.Operator.PARALLEL and number_of_executions > 0:
                    for index in range(0, number_of_executions):
                        if node.__str__() in time_interval_map:
                            time_interval_map[node.__str__()]["cycle_times"].append(max([time_interval_map[child.__str__()]["cycle_times"][index] 
                                                                                        for child in node.children if child.__str__() in time_interval_map], 
                                                                                        key = lambda range: (range.end_datetime - range.start_datetime)))
                        else:
                            time_interval_map[node.__str__()]={'cycle_times': [max([time_interval_map[child.__str__()]["cycle_times"][index] 
                                                                                        for child in node.children if child.__str__() in time_interval_map], 
                                                                                        key =  lambda range: (range.end_datetime - range.start_datetime))]}
                elif number_of_executions > 0:
                    ranges = []
                    for index in range(0, number_of_executions):
                        for child in node.children:
                            if child.__str__() in time_interval_map and not processed_children[child.__str__()]:
                                ranges.append(time_interval_map[child.__str__()]['cycle_times'][index])
                                if not processed_children[child.__str__()] and index + 1 >= len(time_interval_map[child.__str__()]['cycle_times']):
                                    processed_children[child.__str__()] = True
                        if ranges:            
                            start = min([range.start_datetime for range in ranges])
                            end = max([range.end_datetime for range in ranges])
                            if node.__str__() in time_interval_map:
                                time_interval_map[node.__str__()]['cycle_times'].extend([DateTimeRange(start, end)])
                            else:
                                time_interval_map[node.__str__()]={'cycle_times': [DateTimeRange(start, end)]}
                            ranges = []
                   
    
    def construct_cycle_time_ranges_for_leafs(self, activity_instances, alignment, time_interval_map, model, current_trace_variant):
        processed = []
        for index, move in enumerate(alignment["alignment"]):
            if self.is_model_or_sync_move(move):
                transition = self.get_transition_from_move(move, model.transitions)
                if not self.is_border(transition) and transition.label is not None:
                    if transition.label in activity_instances and move[1][0] != ">>":
                        moves = [m for m in alignment["alignment"] if m[0][1] == move[0][1]]
                        move_index = moves.index(move)
                        self.construct_ranges(transition, time_interval_map, activity_instances, move, current_trace_variant, move_index)
                    else:
                        range_time = time_interval_map[processed[-1]]["cycle_times"][-1].end_datetime
                        if transition.label in time_interval_map:
                            time_interval_map[transition.label]["cycle_times"].append(DateTimeRange(range_time,range_time))
                        else:
                            time_interval_map[transition.label]= {"cycle_times": [DateTimeRange(range_time,range_time)]}
                    processed.append(transition.label)
                
    def construct_ranges(self, transition, time_interval_map, activity_instances, move, current_trace_variant, move_index):
        enabler = self.get_enabling_time_preceding_moves(activity_instances, move, current_trace_variant, time_interval_map)
        start = self.get_time_from_data(enabler, activity_instances, len(time_interval_map[enabler]["cycle_times"]) - 1, time_interval_map).end_datetime if enabler is not None else activity_instances[transition.label][0].start_datetime
        
        end = None
        if transition.label in activity_instances:
            end = activity_instances[transition.label][move_index].end_datetime
        else:
            end = start
            
        if transition.label in time_interval_map:
            time_interval_map[transition.label]['cycle_times'].append(DateTimeRange(start, end))
        else:
            time_interval_map[transition.label]= {'cycle_times': [DateTimeRange(start, end)]}

    def is_model_or_sync_move(self, move):
        return move[0][1] != ">>"
    
    def get_transition_from_move(self, move, transitions):
        return [transition for transition in transitions if transition.name == move[0][1]][0]
        
    def is_border(self, transition):
        return self.is_start(transition) or self.is_end(transition)

    def is_start(self, transition):
        return transition.name.endswith("_start")

    def is_end(self, transition):
        return transition.name.endswith("_end")    
    
    def get_timed_marking(self, marking, time_stamp):
        timed_marking = dict()
        for key, value in marking.items():
            timed_marking[key] = {'time':time_stamp, 'delta': None}
        return timed_marking

    def get_transition_map(self, model, alignment):
        transition_map = dict()
        for move in alignment:
            if self.is_model_or_sync_move(move):
                transition_map[move] = self.get_transition_from_move(move, model.transitions)
        return transition_map
       
    def update_enablers_map(self, transitions,variant):
        self.enablers_map[variant] = dict()
        for transition in transitions:
            visited_silent_transitions = []
            self.enablers_map[variant][transition.name] = self.get_visible_enablers(transitions, transition, variant, visited_silent_transitions)

        
    def get_visible_enablers(self, transitions, transition, variant, visited_silent_transitions):
        input_places = [arc.source for arc in transition.in_arcs]
        enabler_candidates = [arc.source for place in input_places for arc in place.in_arcs]
        enablers = []
        for transition in enabler_candidates:
            if transition.label is not None:
                if transition.label not in enablers:
                    enablers.append(transition.label) 
            else:
                if transition not in visited_silent_transitions:
                    visited_silent_transitions.append(transition)
                    if transition.name in self.enablers_map[variant]:
                        enablers.extend(self.enablers_map[variant][transition.name])
                    else:
                        enablers.extend(self.get_visible_enablers(transitions, transition, variant, visited_silent_transitions))
        return enablers

    def get_enabling_time_preceding_moves(self, activity_instances, move, current_trace_variant, time_interval_map):
        enablers = []
        for enabler in self.enablers_map[current_trace_variant][move[0][1]]:
            if enabler is not None and enabler in time_interval_map:
                enablers.append(enabler)
        if enablers:
            return max(enablers, key = lambda enabler: self.get_time_from_data(enabler, activity_instances, len(time_interval_map[enabler]['cycle_times'])-1, time_interval_map).end_datetime)
        return None

    def get_time_from_data(self, transition, activity_instances, index, time_interval_map):
        if transition in activity_instances:
            return activity_instances[transition][index]
        else:
            if "cycle_times" in time_interval_map[transition]:
                return time_interval_map[transition]["cycle_times"][index]

    # def get_enabling_time_preceding_moves(self, transition, activity_instances):
    #     input_places = [arc.source for arc in transition.in_arcs]
    #     enablers = [arc.source for place in input_places for arc in place.in_arcs]
    #     visible_enablers = [enabler if enabler.label is not None and enabler.label in activity_instances else 
    #                        self.get_enabling_time_preceding_moves(enabler, activity_instances) for enabler in enablers]
    #     visible_enablers = [enabler for enabler in visible_enablers if enabler is not None]                

    #     return max(visible_enablers, key= lambda enabler: self.get_time_from_data(enabler, activity_instances).end_datetime) if visible_enablers else None

    # def get_time_from_data(self, transition, activity_instances):
    #     return activity_instances[transition.label][0]