import pandas as pd
import math
from copy import deepcopy
from collections import defaultdict
from tqdm import tqdm
import heapdict

from atf import ATF, min_atf
from trip import Bus, Walk


class TransportGraph:

    def __init__(self,
                 transport_connections: pd.DataFrame,
                 walk_connections: pd.DataFrame):

        transport_connections_df = transport_connections.copy(deep=True)
        transport_connections_df = transport_connections_df.sort_values(by='dep_time_ut')
        transport_connections_df['dep_arr'] = list(zip(transport_connections_df['dep_time_ut'],
                                                       transport_connections_df['arr_time_ut']))
        transport_connections_df['route_I'] = transport_connections_df['route_I'].astype(str)
        transport_connections_dict = transport_connections_df.groupby(by=['from_stop_I', 'to_stop_I']
                                                                      ).agg({'dep_arr': list, 'route_I': list}
                                                                            ).to_dict('index')

        walk_connections_dict = walk_connections.set_index(['from_stop_I', 'to_stop_I'])['d_walk'].to_dict()

        self.graph = defaultdict(dict)
        self.in_nodes = defaultdict(dict)
        self.nodes = set()

        for adjacent_node, node in set(transport_connections_dict.keys()).union(set(walk_connections_dict.keys())):
            nodes_sequence = [adjacent_node, node]
            walk = Walk(nodes=nodes_sequence, w=walk_connections_dict.get((adjacent_node, node), math.inf))
            transport_connections_nodes_dict = transport_connections_dict.get((adjacent_node, node),
                                                                              {'dep_arr': [], 'route_I': []})
            buses = [Bus(nodes=nodes_sequence, c=c,
                         route_names=[transport_connections_nodes_dict['route_I'][i]])
                     for i, c in enumerate(transport_connections_nodes_dict['dep_arr'])]
            self.in_nodes[node][adjacent_node] = self.graph[adjacent_node][node] = ATF(walk=walk, buses=buses)
            self.nodes.add(adjacent_node)
            self.nodes.add(node)

    def edge_difference(self, node):
        out_nodes_cnt = len(self.graph[node])
        in_nodes_cnt = len(self.in_nodes[node])

        # TODO: Validate idea with drooping existing shortcuts
        # existing_shortcuts = len({(x, y)
        #                          for (x, y) in product(self.graph[node], self.in_nodes[node])
        #                          if self.graph[y].get(x)})
        # shortcuts_inserted = out_nodes_cnt * in_nodes_cnt - existing_shortcuts

        shortcuts_inserted = out_nodes_cnt * in_nodes_cnt
        edges_removed = out_nodes_cnt + in_nodes_cnt

        return shortcuts_inserted - edges_removed

    @property
    def contraction_hierarchy(self):
        new_graph = ContactionTransportGraph(self.graph, self.in_nodes, self.nodes)
        in_nodes = deepcopy(self.in_nodes)
        graph = deepcopy(self.graph)
        for index in tqdm(range(len(self.nodes))):
            node = new_graph.contraction_priority.popitem()[0]
            new_depth = new_graph.depth[node] + 1
            previous_node_items = in_nodes[node].items()
            if list(previous_node_items):
                in_nodes_last = list(previous_node_items)[-1][0]

                for previous_node, f in previous_node_items:
                    for next_node, g in graph[node].items():
                        if previous_node != next_node:
                            # calculate new connection function

                            new_f = g.composition(f)

                            h = graph[previous_node].get(next_node, None)
                            if h:
                                new_f = min_atf(new_f, h)
                            in_nodes[next_node][previous_node] = graph[previous_node][next_node] = new_f
                            new_graph.in_nodes[next_node][previous_node] = new_graph.graph[previous_node][next_node] = new_f
                            if previous_node == in_nodes_last:
                                new_graph.depth[next_node] = max(new_graph.depth[next_node], new_depth)
                                new_graph.contraction_priority[next_node] = (new_graph.edge_difference(next_node)
                                                                             + new_graph.depth[next_node])
                        if previous_node == in_nodes_last:
                            del in_nodes[next_node][node]
                    new_graph.depth[previous_node] = max(new_graph.depth[previous_node], new_depth)
                    new_graph.contraction_priority[previous_node] = (new_graph.edge_difference(previous_node)
                                                                     + new_graph.depth[previous_node])
                    del graph[previous_node][node]
            else:
                for next_node, g in graph[node].items():
                    new_graph.depth[next_node] = max(new_graph.depth[next_node], new_depth)
                    new_graph.contraction_priority[next_node] = (new_graph.edge_difference(next_node)
                                                                 + new_graph.depth[next_node])
                    del in_nodes[next_node][node]

            del graph[node], in_nodes[node]

            new_graph.hierarchy[node] = index

        return new_graph


class ContactionTransportGraph(TransportGraph):

    def __init__(self, graph, in_nodes, nodes):
        self.graph = deepcopy(graph)
        self.in_nodes = deepcopy(in_nodes)
        self.nodes = deepcopy(nodes)
        self.hierarchy = {}
        self.geometrical_containers = {}
        self.depth = defaultdict(int)
        self.contraction_priority = heapdict.heapdict()
        for x in nodes:
            self.contraction_priority[x] = self.edge_difference(x) + self.depth[x]

    def geometrical_container(self):
        for node in tqdm(self.nodes):
            visited = set()
            self.dfs(visited, node)
            self.geometrical_containers[node] = visited

    def dfs(self, visited, node):
        if node not in visited:
            visited.add(node)
            for neighbour in self.graph[node]:
                if self.hierarchy[neighbour] < self.hierarchy[node]:
                    self.dfs(visited, neighbour)
