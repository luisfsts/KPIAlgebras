class CycleTimeAnalysisUseCase(object):
    def analyse(self, log, alignments, model):
        cycle_time_ranges =  dict()

        for alignment_index, alignment in enumerate(alignments):
            self.construct_cycle_time_ranges_recursively(log, alignment, alignment_index, model, cycle_time_ranges)

        return cycle_time_ranges
    
    def construct_cycle_time_ranges_recursively(self, log, alignment, alignment_index, model, cycle_time_ranges):
        
        pass

    def traverse(self, tree):
        stack = [iter([tree])]
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