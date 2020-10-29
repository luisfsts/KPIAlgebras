import tempfile
import uuid
import pylab
from graphviz import Digraph
from pm4py.objects.process_tree import pt_operator
import matplotlib

class DecorateExtendedProcessTreeUseCase(object):
    def repr_tree(self, extended_process_tree, viz, current_node, rec_depth, colors):
        for child in extended_process_tree.children:
            if child.operator is None:
                viz.attr('node', shape='box', fixedsize='true', width="2.5",
                        fontsize="8")
                this_trans_id = str(uuid.uuid4())
                if child.label is None:
                    viz.node(this_trans_id, "tau", style='filled', fillcolor='black')
                else:
                    viz.node(this_trans_id, str(child), style='filled', fillcolor=colors[child.__str__()])
                viz.edge(current_node, this_trans_id)
            else:
                condition_wo_operator = child.operator == pt_operator.Operator.XOR and len(
                    child.children) == 1 and child.children[0].operator is None
                if condition_wo_operator:
                    childchild = child.children[0]
                    viz.attr('node', shape='box', fixedsize='true', width="2.5",
                            fontsize="8")
                    this_trans_id = str(uuid.uuid4())
                    if childchild.label is None:
                        viz.node(this_trans_id, str(childchild), style='filled', fillcolor='black')
                    else:
                        viz.node(this_trans_id, str(childchild), style='filled', fillcolor=colors[child.__str__()])
                    viz.edge(current_node, this_trans_id)
                else:
                    viz.attr('node', shape='circle', fixedsize='true', width="0.6",
                            fontsize="14")
                    op_node_identifier = str(uuid.uuid4())
                    viz.node(op_node_identifier, str(child.operator), style='filled', fillcolor=colors[child.__str__()])
                    viz.edge(current_node, op_node_identifier)
                    viz = self.repr_tree(child, viz, op_node_identifier, rec_depth + 1, colors)
        return viz


    def convert_rgba_to_hex(self, rgba):
        return  matplotlib.colors.to_hex([rgba[0], rgba[1], rgba[2], rgba[3]], keep_alpha=True)

    def get_color_map(self, extended_process_tree):
        colors = dict()
        nodes = [node for node in extended_process_tree.get_nodes_bottom_up() if 'cycle_times' in node.kpis and node.__str__() != 'τ']
        values = [node.get_avg_kpi_value('cycle_times') for node in sorted(nodes, key=lambda node: node.get_avg_kpi_value('cycle_times'),reverse=True)]
        color_map =  pylab.get_cmap('RdYlBu')
        
        for index, value in enumerate(values):
            nodes = extended_process_tree.get_nodes_bottom_up()
            color = color_map(1.*index/len(values))
            target_nodes = [node for node in nodes if node.get_avg_kpi_value('cycle_times') == value]
            for target_node in target_nodes:
                colors[target_node.__str__()] = self.convert_rgba_to_hex(color)
        return colors

    def decorate(self, extended_process_tree):
        colors = self.get_color_map(extended_process_tree)
        filename = tempfile.NamedTemporaryFile(suffix='.gv')
        viz = Digraph("pt", filename=filename.name, engine='dot', graph_attr={'bgcolor': 'transparent'})
        image_format = "svg"

        # add first operator
        if extended_process_tree.operator:
            viz.attr('node', shape='circle', fixedsize='true', width="0.6",
                    fontsize="14")
            op_node_identifier = str(uuid.uuid4())
            viz.node(op_node_identifier, str(extended_process_tree.operator), style='filled', fillcolor=colors[extended_process_tree.__str__()])

            viz = self.repr_tree(extended_process_tree, viz, op_node_identifier, 0, colors)
        else:
            viz.attr('node', shape='box', fixedsize='true', width="2.5",
                    fontsize="8")
            this_trans_id = str(uuid.uuid4())
            if extended_process_tree.label is None:
                viz.node(this_trans_id, "tau", style='filled', fillcolor='black')
            else:
                viz.node(this_trans_id, str(extended_process_tree), style='filled',  fillcolor=colors[extended_process_tree.__str__()])

        viz.attr(overlap='false')
        viz.attr(fontsize='11')
        viz.format = image_format

        return viz   