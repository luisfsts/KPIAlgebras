from KPIAlgebras.entities.data import EventLog as log
from KPIAlgebras.entities.model import PetriNet, PetriNetSemantics
from datetimerange import DateTimeRange
from datetime import datetime, timedelta
import re


class TimeRangesConstructionUseCase(object):
    def __init__(self, log, extended_process_tree, model, initial_marking, final_marking, alignments):
        self.log = log
        self.model = model
        self.initial_marking = initial_marking
        self.final_marking = final_marking
        self.alignments = alignments
        self.shiftting_amount = timedelta()
        self.target_node = None
        self.extended_process_tree = extended_process_tree
        
    def construct_time_ranges(self, log, alignment, model, initial_marking, final_marking):
        time_interval_map = dict()
        for index, trace in enumerate(log):
            instances = self.get_activities_time_instances(trace, alignment[index], model)
            timed_marking = self.get_timed_marking(initial_marking, trace[0]["time:timestamp"])
            self.construct_ranges(instances, alignment[index], model, timed_marking, time_interval_map)
            self.update_extended_tree(time_interval_map)
        return time_interval_map
    
    def shift_time_ranges(self, node, kpi, delta):
        time_interval_map = dict()
        for index, trace in enumerate(self.log):
            instances = self.get_activities_time_instances(trace, self.alignments[index], self.model)
            timed_marking = self.get_timed_marking(self.initial_marking, trace[0]["time:timestamp"])
            self.construct_ranges(instances, self.alignments[index], self.model, timed_marking, time_interval_map, node, kpi, delta)
            self.update_extended_tree(time_interval_map)
        return time_interval_map

    def update_extended_tree(self, time_interval_map):
        nodes = self.extended_process_tree.get_nodes_bottom_up()
        for node in nodes:
            node.kpis = time_interval_map[node.__str__()]

    def get_activities_time_instances(self, trace, alignment, model):
        open_instances = []
        instances = dict()

        for event in trace:
            if event["lifecycle:transition"] == "start":
                time_range = DateTimeRange()
                time_range.set_start_datetime(event["time:timestamp"])
                open_instances.append(event["concept:name"])
                instances[event["concept:name"]] = [time_range] if event["concept:name"] not in instances else instances[event["concept:name"]].append(time_range)
            elif event["lifecycle:transition"] == "complete":
                if event["concept:name"] in open_instances:
                    open_instances.remove(event["concept:name"])
                    open_instance = next(instance for instance in instances[event["concept:name"]] if instance.end_datetime is None)
                    open_instance.set_end_datetime(event["time:timestamp"])
                else:
                    instances[event["concept:name"]]= [DateTimeRange(event["time:timestamp"], event["time:timestamp"])]
        
        border_moves = [move for move in alignment["alignment"] if move[0][0] == ">>"] 

        for index, border_move in enumerate(border_moves):
            move_name = self.get_move_name(border_move)
            if index == 0:
                instances[move_name] = [DateTimeRange(instances[trace[0]["concept:name"]][0].start_datetime, instances[trace[0]["concept:name"]][0].start_datetime)]
            else:
                last_move = self.get_last_visible_move(border_move, alignment, instances)
                last_move_label = self.get_move_label(last_move)
                instances[move_name] = [DateTimeRange(instance.end_datetime, instance.end_datetime) for instance in instances[last_move_label]]
        return instances
    
    def get_last_visible_move(self, move, alignment, instances):
        last_moves = [move for move in alignment["alignment"][:alignment["alignment"].index(move)] if self.get_move_label(move) is not None and self.get_move_label(move) != ">>" ]
        sorted_last_moves_list = sorted(last_moves, key=lambda x: instances[self.get_move_label(x)][-1].end_datetime)
        return sorted_last_moves_list[-1]

    def get_move_name(self, move):
        return move[0][1]
    
    def get_move_label(self, move):
        return move[1][1]

    def get_timed_marking(self, marking, time_stamp):
        timed_marking = dict()
        for key, value in marking.items():
            timed_marking[key] = {'time':time_stamp, 'delta': None}
        return timed_marking

    def construct_ranges(self, activities_time_instances, alignment, model, initial_marking, time_interval_map, node=None, kpi=None, delta=None):
        border_transitions_map = self.construct_border_transitions_map(model)
        timed_marking = initial_marking
        active_subtrees = []
        self.target_node = node
        
        for move in alignment["alignment"]:
            if self.is_model_or_sync_move(move):
                transition = self.get_transition_from_move(move, model.transitions)
                name = transition.name if self.is_border(transition) else transition.label
                time = None

                if name == node:
                    last_enabling_token = self.get_last_timed_enabling_token(transition, timed_marking)
                    last_enabling_token["delta"] = delta
                    last_enabling_token["kpi"] = kpi
                    if kpi == "waiting_time":
                        start = self.get_enabling_time_from_timed_marking(timed_marking, transition)
                        end = activities_time_instances[name][0].start_datetime
                    else:
                        start = activities_time_instances[name][0].start_datetime
                        end = activities_time_instances[name][0].end_datetime
                    duration = end - start 
                    self.shiftting_amount = timedelta(seconds = duration.total_seconds() * delta)
                    
                if self.is_border(transition) and self.is_start(transition):
                    active_subtrees.append(border_transitions_map[transition.name])
                    time_interval_map[border_transitions_map[transition.name]] = dict()
                
                if not self.is_border(transition):
                    self.construct_waiting_time_ranges(transition, activities_time_instances, timed_marking, time_interval_map, active_subtrees)
                    self.construct_service_time_ranges(transition, activities_time_instances, time_interval_map, active_subtrees, timed_marking)
                
                if self.is_border(transition) and self.is_end(transition):
                    self.construct_idle_time_ranges(time_interval_map, active_subtrees)
                    active_subtrees.remove(border_transitions_map[transition.name])
                
                if name in time_interval_map:
                    time = time_interval_map[name]["service_times"][0].end_datetime
                else:
                    last_enabling_token = self.get_last_timed_enabling_token(transition, timed_marking)
                    if last_enabling_token["delta"] is not None:
                        time = activities_time_instances[name][0].start_datetime - self.shiftting_amount
                    else:
                        time = activities_time_instances[name][0].start_datetime
                semantics = PetriNetSemantics(model)
                timed_marking = semantics.execute_with_timed_token(transition, timed_marking, time)

        return time_interval_map

    def construct_idle_time_ranges(self, time_interval_map, active_subtrees):
        for active_subtree in active_subtrees:
            idle_times = []
            for index, time_range in enumerate(time_interval_map[active_subtree]["service_times"]):
                size= len(time_interval_map[active_subtree]["service_times"]) - 1
                if index < size:
                    idle_times.append(DateTimeRange(time_range.end_datetime, 
                                                   time_interval_map[active_subtree]["service_times"][index+1].start_datetime))
            time_interval_map[active_subtree]["idle_times"] = idle_times

    def construct_service_time_ranges(self, transition, activities_time_instances, time_interval_map, active_subtrees, timed_marking):
        activity_instances = activities_time_instances[transition.name] if self.is_border(transition) else activities_time_instances[transition.label]
        activity_name = transition.name if self.is_border(transition) else transition.label
        activity_label = self.get_subtree_name_from_border_transition(transition) if self.is_border(transition) else transition.label
        start = activities_time_instances[activity_name][0].start_datetime
        end = activities_time_instances[activity_name][0].end_datetime
        last_enabling_token =  self.get_last_timed_enabling_token(transition, timed_marking)

        if transition.label == self.target_node:
            if last_enabling_token["kpi"] == "waiting_time":
               start = start - self.shiftting_amount
               end = end - self.shiftting_amount
            else:
                end = end - self.shiftting_amount
        elif last_enabling_token["delta"] is not None:
            start = start - self.shiftting_amount
            end = end - self.shiftting_amount


        if activity_label in time_interval_map:
            if 'service_times' in  time_interval_map[activity_label]:
                time_interval_map[activity_label]['service_times'].append(DateTimeRange(start, end))
            else:
                time_interval_map[activity_label]['service_times'] = [DateTimeRange(start, end)]
        else:
            time_interval_map[activity_label]={'service_times': [DateTimeRange(start, end)]}
       
        for active_subtree in active_subtrees:
            if 'service_times' in time_interval_map[active_subtree]:
                #TODO refactor: the union method is already modifiying the list
                time_interval_map[active_subtree]["service_times"] = self.union(time_interval_map[active_subtree]["service_times"], 
                                                                            time_interval_map[activity_label]['service_times'])
            else:
                time_interval_map[active_subtree]["service_times"] = time_interval_map[activity_label]['service_times'].copy()
        
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
                time_interval_map_subtree.append(time_interval_map_activity[0])
        return sorted(time_interval_map_subtree, key= lambda x: x.start_datetime)

    def getIntersections(self, time_range, time_interval_map_subtree):
        return [range for range in time_interval_map_subtree if range.is_intersection(time_range) or time_range.is_intersection(range)]
    
    def merge_intervals(self, time_range, intersection_set):
        merged_intervals = []
        for range in intersection_set:
            if time_range.encompass(range) not in merged_intervals:
                merged_intervals.append(time_range.encompass(range))

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
                end = end - self.shiftting_amount
        elif last_enabling_token["delta"] is not None:
             end = end - self.shiftting_amount
        
        if activity_label in time_interval_map:
            if 'waiting_times' in  time_interval_map[activity_label]:
                time_interval_map[activity_label]['waiting_times'].append(DateTimeRange(start, end))
            else:
                time_interval_map[activity_label]['waiting_times'] = [DateTimeRange(start, end)]
        else:
            time_interval_map[activity_label]={'waiting_times': [DateTimeRange(start, end)]}

        for active_subtree in active_subtrees:
            if 'waiting_times' not in time_interval_map[active_subtree]:
                time_interval_map[active_subtree]["waiting_times"] = time_interval_map[activity_label]['waiting_times'].copy()

    def get_last_timed_enabling_token(self, transition, timed_marking):
        enabling_timed_tokens = []
        for arc in transition.in_arcs:
            if arc.source in timed_marking:
                enabling_timed_tokens.append(timed_marking[arc.source])
        return max(enabling_timed_tokens, key=(lambda token: token["time"]))
        
    def get_enabling_time_from_timed_marking(self, timed_marking, transition):
        input_arcs_sources = [arc.source for arc in transition.in_arcs]
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

 

   

    
    
   
    
   