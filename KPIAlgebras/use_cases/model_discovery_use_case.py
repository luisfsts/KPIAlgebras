from pm4py.algo.discovery.inductive import factory as inductive_miner
from KPIAlgebras.entities import model 

class ModelDiscoveryUseCase(object):
        def discover(self, event_log):
            process_tree = inductive_miner.apply_tree(event_log)
            return model.ExtendedProcessTree(process_tree)
