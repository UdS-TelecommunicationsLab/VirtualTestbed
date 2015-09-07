from topology import Topology


class SimpleTopology(Topology):
    def generate(self):
        graph = {}

        switches = range(self.switches)
        while len(switches) > 1:
            endpoints = self.rnd.sample(switches, 2)
            left = endpoints[0]
            right = endpoints[1]

            if left not in graph:
                graph[left] = set()
            if right not in graph:
                graph[right] = set()

            graph[left].add(right)
            graph[right].add(left)

            switches.remove(left)
        return graph
