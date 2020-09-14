from datetimerange import DateTimeRange
from KPIAlgebras.response_objects import response_objects as response
from pm4py.objects.process_tree import pt_operator
import datetime
import time


class CycleTimeAnalysisUseCase(object):
    def analyse(self, log, alignments, process_tree, model):
        print("Begining the Cycle time analysis")
        t1 = time.perf_counter()

        for alignment_index, alignment in enumerate(alignments):
            instances = self.get_activities_time_instances(log[alignment_index], alignment, model)
            self.construct_cycle_time_ranges(instances, alignment, process_tree, model)
        self.construct_cycle_time_ranges_for_Operators(process_tree)
        t2 = time.perf_counter()
        print(t2-t1)
        return response.ResponseSuccess(process_tree)


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
        
        return instances

    def get_last_visible_move(self, move, alignment, instances):
        last_moves = [move for move in alignment["alignment"][:alignment["alignment"].index(move)] if self.get_move_label(move) is not None and self.get_move_label(move) != ">>" ]
        sorted_last_moves_list = sorted(last_moves, key=lambda x: instances[self.get_move_label(x)][-1].end_datetime)
        return sorted_last_moves_list[-1]
    
    def get_move_name(self, move):
        return move[0][1]
    
    def get_move_label(self, move):
        return move[1][1]

    def construct_cycle_time_ranges(self, activity_instances, alignment, process_tree, model):
        self.construct_cycle_time_ranges_for_leafs(activity_instances, alignment, process_tree, model)
        
    def construct_cycle_time_ranges_for_Operators(self, process_tree):
        for node in process_tree.get_nodes_bottom_up():
            if node.children:
                if node.operator != pt_operator.Operator.PARALLEL:
                    node.kpis["cycle_times"] = sum([child.get_avg_kpi_value("cycle_times") for child in node.children if "cycle_times" in child.kpis], datetime.timedelta())
                else:
                    node.kpis["cycle_times"] = max([child.get_avg_kpi_value("cycle_times") for child in node.children if "cycle_times" in child.kpis])

    def construct_cycle_time_ranges_for_leafs(self, activity_instances, alignment, process_tree, model):
        for index, move in enumerate(alignment["alignment"]):
            if self.is_model_or_sync_move(move):
                transition = self.get_transition_from_move(move, model.transitions)
                if not self.is_border(transition) and transition.label is not None:
                    #TODO include preceding_moves to deal with loops
                    # preceding_moves = alignment["alignment"][:index]
                    self.construct_ranges(transition, process_tree, activity_instances)
                
    def construct_ranges(self, transition, process_tree, activity_instances):
        enabler = self.get_enabling_time_preceding_moves(transition, activity_instances)
        start = activity_instances[enabler.label][0].end_datetime if enabler is not None else activity_instances[transition.label][0].start_datetime
        end = activity_instances[transition.label][0].end_datetime
        node = [node for node in process_tree.get_nodes_bottom_up() if node.__str__() == transition.label][0]
        
        if 'cycle_times' in node.kpis:
            node.kpis['cycle_times'].append(DateTimeRange(start, end))
        else:
            node.kpis['cycle_times'] = [DateTimeRange(start, end)]
        
    def is_model_or_sync_move(self, move):
        return move[0][1] != ">>"
    
    def get_transition_from_move(self, move, transitions):
        return [transition for transition in transitions if transition.name == move[0][1]][0]

    def get_enabling_time_preceding_moves(self, transition, activity_instances):
        input_places = [arc.source for arc in transition.in_arcs]
        enablers = [arc.source for place in input_places for arc in place.in_arcs]
        visible_enablers = [enabler if enabler.label is not None and enabler.label in activity_instances else 
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