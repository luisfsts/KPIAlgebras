from KPIAlgebras.entities.model import ExtendedProcessTree
from pm4py.objects.process_tree.pt_operator import Operator as pt_opt


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


def unfold_leafs(tree, log, parameters=None):
    if "classifier_name" in parameters and (parameters["classifier_name"] == "MXML Legacy Classifier" or
                                            parameters["classifier_name"] == "customClassifier"):                                   
        atomic_leafs = []
        for leaf in tree.get_leafs():
            index = tree.children.index(leaf)
            tree.children.remove(leaf)
            if not is_atomic(leaf.label, log):
                if tree.operator == pt_opt.SEQUENCE:
                    tree.children[index:index] = [ExtendedProcessTree(None, tree, None, (leaf.label + "+start")),
                                                  ExtendedProcessTree(None, tree, None, (leaf.label + "+complete"))]
                else:
                    children = [ExtendedProcessTree(None, tree, None, (leaf.label + "+start")),
                                ExtendedProcessTree(None, tree, None, (leaf.label + "+complete"))]
                    tree.children[index:index] = [ExtendedProcessTree(pt_opt.SEQUENCE, tree, children, None)]
            else:
                atomic_leafs.append(leaf.label)
                tree.children[index:index] = [ExtendedProcessTree(None, tree, None, (leaf.label + "+complete"))]
        if atomic_leafs:
            if "atomic_leafs" in parameters:
                for leaf in atomic_leafs:
                    if leaf not in parameters["atomic_leafs"]:
                        parameters["atomic_leafs"].append(leaf)
            else:
                parameters["atomic_leafs"] = atomic_leafs
        for node in nodes:
            node = unfold_leafs(node, log, parameters)

    return tree
