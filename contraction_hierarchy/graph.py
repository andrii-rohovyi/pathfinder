import pandas as pd
import numpy as np
from copy import deepcopy
from collections import defaultdict
from tqdm import tqdm
import heapdict
import math
from bisect import bisect_left

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
        self.node_time = defaultdict(set)
        self.nodes_schedule = defaultdict(list)
        self.position_in_edge = defaultdict(dict)

        for adjacent_node, node in set(transport_connections_dict.keys()).union(set(walk_connections_dict.keys())):
            nodes_sequence = [adjacent_node, node]
            walk_duration = walk_connections_dict.get((adjacent_node, node))
            walk = None
            if walk_duration:
                walk = Walk(nodes=nodes_sequence, w=walk_duration)
            transport_connections_nodes_dict = transport_connections_dict.get((adjacent_node, node),
                                                                              {'dep_arr': [], 'route_I': []})
            buses = [Bus(nodes=nodes_sequence, c=c,
                         route_names=[transport_connections_nodes_dict['route_I'][i]])
                     for i, c in enumerate(transport_connections_nodes_dict['dep_arr'])]
            g = ATF(walk=walk, buses=buses)
            g.cut()
            self.in_nodes[node][adjacent_node] = self.graph[adjacent_node][node] = g
            self.nodes.add(adjacent_node)
            self.nodes.add(node)

    @property
    def edges_cnt(self):
        edges_sum = 0
        for i, v in self.graph.items():
            edges_sum += len(v)
        return edges_sum

    @property
    def nodes_cnt(self):
        return len(self.nodes)

    def calculate_node_times(self):
        for node1 in self.nodes:
            for node in self.graph[node1]:
                f = self.graph[node1][node]
                f.edge_sectors()
                for sector in f.sectors:
                    if sector != math.inf:
                        self.node_time[node1].add(sector)

    @property
    def timetable_stats(self):
        timetables = []
        for i, v in self.graph.items():
            for i0, v0 in v.items():
                timetables += [len(v0.buses)]
        timetables = np.array(timetables)
        return {'min_size': timetables.min(),
                'mean_size': timetables.mean(),
                'std_size': timetables.std(),
                'max_size': timetables.max()}

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

    def contraction_hierarchy(self, just_buses=True):
        new_graph = ContactionTransportGraph(self.graph, self.in_nodes, self.nodes)
        in_nodes = deepcopy(self.in_nodes)
        graph = deepcopy(self.graph)
        for index in tqdm(range(len(self.nodes))):
            node = new_graph.contraction_priority.popitem()[0]
            new_depth = new_graph.depth[node] + 1
            if in_nodes[node]:

                while in_nodes[node]:
                    previous_node, f = in_nodes[node].popitem()
                    for next_node, g in graph[node].items():
                        if previous_node != next_node:
                            # calculate new connection function

                            if just_buses:
                                new_f = g.composition_buses(f)
                            else:
                                new_f = g.composition(f)
                            if new_f:
                                h = graph[previous_node].get(next_node, None)
                                if h:
                                    new_f = min_atf(new_f, h)
                                in_nodes[next_node][previous_node] = graph[previous_node][next_node] = new_f
                                new_graph.in_nodes[next_node][previous_node] = new_graph.graph[previous_node][
                                    next_node] = new_f
                            if not in_nodes[node]:
                                new_graph.depth[next_node] = max(new_graph.depth[next_node], new_depth)
                                new_graph.contraction_priority[next_node] = (new_graph.edge_difference(next_node)
                                                                             + new_graph.depth[next_node])
                        if not in_nodes[node]:
                            del in_nodes[next_node][node]
                    new_graph.depth[previous_node] = max(new_graph.depth[previous_node], new_depth)
                    new_graph.contraction_priority[previous_node] = (new_graph.edge_difference(previous_node)
                                                                     + new_graph.depth[previous_node])
                    del graph[previous_node][node]
            else:
                while graph[node]:
                    next_node, g = graph[node].popitem()
                    new_graph.depth[next_node] = max(new_graph.depth[next_node], new_depth)
                    new_graph.contraction_priority[next_node] = (new_graph.edge_difference(next_node)
                                                                 + new_graph.depth[next_node])
                    del in_nodes[next_node][node]

            del graph[node], in_nodes[node]

            new_graph.hierarchy[node] = index

        return new_graph

    def optimize_binary_search(self):
        for node1, out in tqdm(self.graph.items()):
            self.position_in_edge[node1] = {}
            full_list = []
            for node2, f in out.items():
                full_list += [bus.d for bus in f.buses]

            full_list = list(set(full_list))
            full_list.sort()
            self.nodes_schedule[node1] = full_list
            for i, dep in enumerate(full_list):
                self.position_in_edge[node1][i] = {}
                for node2, f in out.items():
                    self.position_in_edge[node1][i][node2] = bisect_left(f.buses, dep, key=lambda x: x.d)


class ContactionTransportGraph(TransportGraph):

    def __init__(self, graph, in_nodes, nodes):
        self.graph = deepcopy(graph)
        self.in_nodes = deepcopy(in_nodes)
        self.nodes = deepcopy(nodes)
        self.hierarchy = {}
        self.geometrical_containers = {}
        self.nodes_schedule_down = defaultdict(list)
        self.position_in_edge_down = defaultdict(dict)
        self.nodes_schedule = defaultdict(list)
        self.position_in_edge = defaultdict(dict)
        self.depth = defaultdict(int)
        self.node_time = defaultdict(set)
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

    def optimize_binary_search(self):
        for node1, out in tqdm(self.graph.items()):
            self.position_in_edge[node1] = {}
            self.position_in_edge_down[node1] = {}
            full_list = []
            down_list = []
            for node2, f in out.items():
                full_list += [bus.d for bus in f.buses]
                if self.hierarchy[node2] < self.hierarchy[node1]:
                    down_list += [bus.d for bus in f.buses]

            full_list = list(set(full_list))
            full_list.sort()
            self.nodes_schedule[node1] = full_list
            for i, dep in enumerate(full_list):
                self.position_in_edge[node1][i] = {}
                for node2, f in out.items():
                    self.position_in_edge[node1][i][node2] = bisect_left(f.buses, dep, key=lambda x: x.d)

            down_list = list(set(down_list))
            down_list.sort()
            self.nodes_schedule_down[node1] = down_list
            for i, dep in enumerate(down_list):
                self.position_in_edge_down[node1][i] = {}
                for node2, f in out.items():
                    self.position_in_edge_down[node1][i][node2] = bisect_left(f.buses, dep, key=lambda x: x.d)
