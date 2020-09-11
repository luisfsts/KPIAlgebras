from pm4py.objects.process_tree.process_tree import ProcessTree
from pm4py.objects.petri.petrinet import PetriNet
import datetime
from copy import copy


class ExtendedProcessTree(ProcessTree):
    def __init__(self, process_tree):
        super().__init__(process_tree.operator, process_tree.parent, process_tree.children, process_tree.label)
        self._children = [ExtendedProcessTree(n)for n in self._children] if self._children else list()
        self.__kpis = {}
        self.__states = []
        self.__change = {}
    
    def get_leaves(self):
        return [children for children in self.children if not children.children and children.label is not None]

    @property
    def kpis(self):
        return self.__kpis
    
    @kpis.setter
    def kpis(self, value):
        self.__kpis = value
    
    @property
    def states(self):
        return self.__states
    
    @states.setter
    def states(self, value):
        self.__states = value
    
    @property
    def change(self):
        return self.__change
    
    @change.setter
    def change(self, value):
        self.__change = value
    
    def get_nodes_bottom_up(self):
        stack = [iter([self])]
        nodes = []
        while stack:
            for node in stack[-1]:
                if node not in nodes:
                    nodes.append(node)
                    if node.children:
                        stack.append(iter(node.children[::-1]))
                break
            else:
                stack.pop()
        yield from nodes[::-1]
    
    def get_avg_kpi_value(self, kpi):
        if kpi in self.__kpis:
            return sum([(range.end_datetime - range.start_datetime) for range in self.__kpis[kpi]], datetime.timedelta())/len(self.__kpis[kpi])
        t = datetime.datetime.strptime("00:00:00", "%H:%M:%S")
        result = datetime.timedelta(hours=t.hour, minutes=t.minute, seconds=t.second)
        return result

class PetriNet(PetriNet):
    def __init__(self, petri_net):
        super().__init__(petri_net.name, petri_net.places, petri_net.transitions, petri_net.arcs, petri_net.properties)
        self.semantics = PetriNetSemantics(self)
    
    @property
    def semantics(self):
        return self.semantics
    
    @semantics.setter
    def semantics(self, value):
        self.semantics = value
    

class PetriNetSemantics(object):
    def __init__(self, petri_net):
        self.petri_net = petri_net
    
    def is_enabled(self, transition, marking):
        for arc in transition.in_arcs:
            if len(marking[arc.source]) < arc.weight:
                return False
        return True

    def execute_with_timed_token(self, transition, marking, time_stamp):
        resulting_marking = copy(marking)
        current_time_stamp = None
        enabling_tokens = []
        
        for arc in transition.in_arcs:
            enabling_tokens.append(resulting_marking[arc.source])
            del resulting_marking[arc.source]
        
        for arc in transition.out_arcs:
            last_executed_token = max(enabling_tokens, key=(lambda token: token["time"]))
            resulting_marking[arc.target] = {'time': time_stamp, 'delta': last_executed_token["delta"]}
        return resulting_marking
    
    def get_time_from_marking(self, marking):
        return max([place["time"] for place in marking.values()])
