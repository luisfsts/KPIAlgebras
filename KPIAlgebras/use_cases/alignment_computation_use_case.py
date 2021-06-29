from pm4py.algo.conformance.alignments import algorithm as alignments_factory
from pm4py.objects.conversion.process_tree.converter import to_petri_net_transition_bordered as converter
# from pm4py.objects.petri import utils as petri_net_utils
from pm4py.objects.petri import align_utils 
from pm4py.objects.petri import synchronous_product
from pm4py.algo.conformance.alignments.variants import state_equation_a_star as alignment_algorithm
from pm4py.algo.conformance.alignments import algorithm
from pm4py.algo.filtering.log.attributes import attributes_filter
from KPIAlgebras.util import util

class AlignmentComputationUseCase(object):
    def compute(self, model, initial_marking, final_marking, event_log):
        alignments = []

        for trace in event_log.log:
            instances = util.get_trace_activity_instances(trace)
            costs = list(map(lambda i: align_utils.STD_MODEL_LOG_MOVE_COST, instances))
            partially_ordered_trace_net, trace_net_initial_marking, trace_net_final_marking, cost_map = util.construct_partially_ordered_trace_net_cost_aware(trace, instances,costs)    
            sync_prod, sync_initial_marking, sync_final_marking = synchronous_product.construct(partially_ordered_trace_net, 
                                                                                                      trace_net_initial_marking,
                                                                                                      trace_net_final_marking, 
                                                                                                      model,
                                                                                                      initial_marking,
                                                                                                      final_marking,
                                                                                                      '>>')                                                                                     
            cost_function = self.construct_standard_cost_function(sync_prod, '>>')
            trace_alignment = alignment_algorithm.apply_sync_prod(sync_prod, sync_initial_marking, sync_final_marking, cost_function, '>>', True)
            alignments.append(trace_alignment)
       
        return alignments

    def construct_standard_cost_function(self, synchronous_product_net, skip):
        costs = {}
        for t in synchronous_product_net.transitions:
            if (skip == t.label[0] or skip == t.label[1]) and (t.label[0] is not None and t.label[1] is not None):
                costs[t] = 10000
            else:
                if (skip == t.label[0] and t.label[1] is None) or (skip == t.label[1] and t.label[0] is None): 
                    costs[t] = 1
                else:
                    costs[t] = 0
        return costs