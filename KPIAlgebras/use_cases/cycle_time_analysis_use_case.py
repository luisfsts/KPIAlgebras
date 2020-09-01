from datetimerange import DateTimeRange
from KPIAlgebras.response_objects import response_objects as response

class CycleTimeAnalysisUseCase(object):
    def analyse(self, log, alignments, process_tree, model):
        cycle_time_ranges =  dict()

        for alignment_index, alignment in enumerate(alignments):
            instances = self.get_activities_time_instances(log[alignment_index], alignment, model)
            self.construct_cycle_time_ranges(instances, alignment, process_tree, model, cycle_time_ranges)
            self.update_extended_tree(cycle_time_ranges, process_tree)
            cycle_time_ranges.clear()
        return response.ResponseSuccess(process_tree)

    def update_extended_tree(self, time_interval_map, extended_process_tree):
        nodes = extended_process_tree.get_nodes_bottom_up()
        for node in nodes:
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

    def construct_cycle_time_ranges(self, activity_instances, alignment, process_tree, model, cycle_time_ranges):
        self.construct_cycle_time_ranges_for_leafs(activity_instances, alignment, process_tree, model, cycle_time_ranges)
        self.construct_cycle_time_ranges_for_Operators(process_tree, cycle_time_ranges)
        
    def construct_cycle_time_ranges_for_Operators(self, process_tree, cycle_time_ranges):
        operators_list = [node for node in process_tree.get_nodes_bottom_up() if node.children]
        ranges = []
        for operator in operators_list:
            for child in operator.children:
                ranges.extend(cycle_time_ranges[child.__str__()]["cycle_times"])
            start = min(ranges, key = lambda range: range.start_datetime).start_datetime
            end = max(ranges, key = lambda range: range.end_datetime).end_datetime
            cycle_time_ranges[operator.__str__()]={'cycle_times': [DateTimeRange(start, end)]}
           
    def construct_cycle_time_ranges_for_leafs(self, activity_instances, alignment, process_tree, model, cycle_time_ranges):
        for index, move in enumerate(alignment["alignment"]):
            if self.is_model_or_sync_move(move):
                transition = self.get_transition_from_move(move, model.transitions)
                if not self.is_border(transition):
                    #TODO include preceding_moves to deal with loops
                    # preceding_moves = alignment["alignment"][:index]
                    self.construct_ranges(transition, cycle_time_ranges, activity_instances)
                
    def construct_ranges(self, transition, cycle_time_ranges, activity_instances):
        enabler = self.get_enabling_time_preceding_moves(transition, activity_instances)
        start = activity_instances[enabler.label][0].end_datetime if enabler is not None else activity_instances[transition.label][0].start_datetime
        end = activity_instances[transition.label][0].end_datetime
        
        if transition.label in cycle_time_ranges:
            if 'cycle_times' in  cycle_time_ranges[transition.label]:
                cycle_time_ranges[transition.label]['cycle_times'].append(DateTimeRange(start, end))
            else:
                time_interval_map[transition.label]['cycle_times'] = [DateTimeRange(start, end)]
        else:
            cycle_time_ranges[transition.label]={'cycle_times': [DateTimeRange(start, end)]}
        
    def is_model_or_sync_move(self, move):
        return move[0][1] != ">>"
    
    def get_transition_from_move(self, move, transitions):
        return [transition for transition in transitions if transition.name == move[0][1]][0]

    def get_enabling_time_preceding_moves(self, transition, activity_instances):
        input_places = [arc.source for arc in transition.in_arcs]
        enablers = [arc.source for place in input_places for arc in place.in_arcs]
        visible_enablers = [enabler if enabler.label is not None else 
                           self.get_enabling_time_preceding_moves(enabler, activity_instances) for enabler in enablers]
        visible_enablers = [enabler for enabler in visible_enablers if enabler is not None]                

        return max(visible_enablers, key= lambda enabler: self.get_time_from_data(enabler, activity_instances).end_datetime) if visible_enablers else None

    def get_time_from_data(self, transition, activity_instances):
        return activity_instances[transition.label][0]
        
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
    
   