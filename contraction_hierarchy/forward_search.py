from typing import Union
import heapdict
import time
import math
import logging
from bisect import bisect_left

from graph import ContactionTransportGraph
from algorithms_wrapper import _check_running_time
from utils import to_milliseconds


class FCH:
    def __init__(self, graph: ContactionTransportGraph, start_time: int, start_node: int, end_node: int):
        self.graph = graph

        self.source = start_node
        self.target = end_node
        self.start_time = start_time

        self.candidate_weights = {self.source: start_time}
        self.candidate_priorities = heapdict.heapdict({self.source: start_time})
        self.candidate_sequences = {self.source: [self.source]}
        self.candidate_roots = {self.source: [self.source]}
        self.candidate_route_names = {self.source: []}
        self.candidate_down_move = {self.source: False}
        self.lower_upper_index = {self.source: (0, None)}
        self.lower_index = {self.source: 0}
        self.candidate_schedule = {self.source: self.graph.nodes_schedule[start_node]}

    def shortest_path(self,
                      duration: Union[float, None] = None,
                      geometrical_containers=True,
                      optimized_binary_search: bool = True,
                      next_index_optimization=True
                      ) -> dict:

        exception = None

        winner_node = self.source
        winner_weight = self.start_time

        position_in_edge = self.graph.position_in_edge
        nodes_schedule = self.graph.nodes_schedule

        if geometrical_containers:
            if optimized_binary_search:
                if not next_index_optimization:

                    start_time = time.monotonic()
                    while (winner_node != self.target) and (not exception):
                        exception = _check_running_time(start_time, duration, "FCH")
                        departure = bisect_left(nodes_schedule[winner_node], winner_weight)
                        nodes_indexes = position_in_edge[winner_node].get(departure)
                        for node in self.graph.graph[winner_node]:
                            if not self.candidate_down_move[winner_node]:
                                if self.graph.hierarchy[node] > self.graph.hierarchy[winner_node]:
                                    self._update_vertex_with_node_index(node, winner_node, winner_weight, False,
                                                                        nodes_indexes)
                                elif self.target in self.graph.geometrical_containers[node]:
                                    self._update_vertex_with_node_index(node, winner_node, winner_weight, True,
                                                                        nodes_indexes)
                            elif ((self.graph.hierarchy[node] < self.graph.hierarchy[winner_node]) &
                                  (self.target in self.graph.geometrical_containers[node])):
                                self._update_vertex_with_node_index(node, winner_node, winner_weight, True,
                                                                    nodes_indexes)

                        try:
                            winner_node, winner_weight = self.candidate_priorities.popitem()
                        except IndexError:
                            message = f"Target {self.target} not reachable from node {self.source}"
                            logging.warning(message)
                            return {
                                'path': [],
                                'routes': [],
                                'arrival': math.inf,
                                'duration': to_milliseconds(time.monotonic() - start_time)
                            }

                else:
                    start_time = time.monotonic()
                    while (winner_node != self.target) and (not exception):
                        exception = _check_running_time(start_time, duration, "FCH")

                        departure = (self.lower_index[winner_node]
                                     + bisect_left(self.candidate_schedule[winner_node], winner_weight))
                        nodes_indexes = position_in_edge[winner_node].get(departure)
                        for node in self.graph.graph[winner_node]:

                            if not self.candidate_down_move[winner_node]:
                                if self.graph.hierarchy[node] > self.graph.hierarchy[winner_node]:
                                    self._update_vertex_with_node_index_new(node, winner_node, winner_weight, False,
                                                                            nodes_indexes,
                                                                            self.graph.nodes_schedule[node]
                                                                            )
                                elif self.target in self.graph.geometrical_containers[node]:
                                    self._update_vertex_with_node_index_new(node, winner_node, winner_weight, True,
                                                                            nodes_indexes,
                                                                            self.graph.nodes_schedule_down[node])
                            elif ((self.graph.hierarchy[node] < self.graph.hierarchy[winner_node]) &
                                  (self.target in self.graph.geometrical_containers[node])):
                                self._update_vertex_with_node_index_new(node, winner_node, winner_weight, True,
                                                                        nodes_indexes,
                                                                        self.graph.nodes_schedule_down[node])

                        try:
                            winner_node, winner_weight = self.candidate_priorities.popitem()
                        except IndexError:
                            message = f"Target {self.target} not reachable from node {self.source}"
                            logging.warning(message)
                            return {
                                'path': [],
                                'routes': [],
                                'arrival': math.inf,
                                'duration': to_milliseconds(time.monotonic() - start_time)
                            }

            else:
                start_time = time.monotonic()
                while (winner_node != self.target) and (not exception):

                    exception = _check_running_time(start_time, duration, "FCH")
                    for node in self.graph.graph[winner_node]:
                        if not self.candidate_down_move[winner_node]:
                            if self.graph.hierarchy[node] > self.graph.hierarchy[winner_node]:
                                self._update_vertex(node, winner_node, winner_weight, False)
                            elif self.target in self.graph.geometrical_containers[node]:
                                self._update_vertex(node, winner_node, winner_weight, True)
                        elif ((self.graph.hierarchy[node] < self.graph.hierarchy[winner_node]) &
                              (self.target in self.graph.geometrical_containers[node])):
                            self._update_vertex(node, winner_node, winner_weight, True)
                    try:
                        winner_node, winner_weight = self.candidate_priorities.popitem()
                    except IndexError:
                        message = f"Target {self.target} not reachable from node {self.source}"
                        logging.warning(message)
                        return {
                            'path': [],
                            'routes': [],
                            'arrival': math.inf,
                            'duration': to_milliseconds(time.monotonic() - start_time)
                        }

        else:
            start_time = time.monotonic()
            while (winner_node != self.target) and (not exception):

                exception = _check_running_time(start_time, duration, "FCH")
                for node in self.graph.graph[winner_node]:
                    if not self.candidate_down_move[winner_node]:
                        if self.graph.hierarchy[node] > self.graph.hierarchy[winner_node]:
                            self._update_vertex(node, winner_node, winner_weight, False)
                        else:
                            self._update_vertex(node, winner_node, winner_weight, True)
                    elif self.graph.hierarchy[node] < self.graph.hierarchy[winner_node]:
                        self._update_vertex(node, winner_node, winner_weight, True)

                try:
                    winner_node, winner_weight = self.candidate_priorities.popitem()
                except IndexError:
                    message = f"Target {self.target} not reachable from node {self.source}"
                    logging.warning(message)
                    return {
                        'path': [],
                        'routes': [],
                        'roots': [],
                        'arrival': math.inf,
                        'duration': to_milliseconds(time.monotonic() - start_time)
                    }
        if exception:
            return {
                'path': self.candidate_sequences[winner_node],
                'routes': self.candidate_route_names[winner_node],
                'roots': self.candidate_roots[winner_node],
                'arrival': winner_weight,
                'duration': to_milliseconds(time.monotonic() - start_time)
            }

        return {
            'path': self.candidate_sequences[self.target],
            'routes': self.candidate_route_names[winner_node],
            'roots': self.candidate_roots[winner_node],
            'arrival': winner_weight,
            'duration': to_milliseconds(time.monotonic() - start_time)
        }

    def _update_vertex(self, node, winner_node, winner_weight, down_move: bool):

        new_weight, sequence_nodes, route_names = self.graph.graph[winner_node][node].arrival(winner_weight)
        if node in self.candidate_weights.keys():
            if new_weight < self.candidate_weights[node]:
                self.candidate_down_move[node] = down_move
                self.candidate_weights[node] = new_weight
                self.candidate_priorities[node] = new_weight
                self.candidate_sequences[node] = self.candidate_sequences[winner_node] + sequence_nodes[1:]
                self.candidate_roots[node] = self.candidate_roots[winner_node] + [node]
                self.candidate_route_names[node] = self.candidate_route_names[winner_node] + route_names
        elif new_weight != math.inf:
            self.candidate_down_move[node] = down_move
            self.candidate_weights[node] = new_weight
            self.candidate_priorities[node] = new_weight
            self.candidate_roots[node] = self.candidate_roots[winner_node] + [node]
            self.candidate_sequences[node] = self.candidate_sequences[winner_node] + sequence_nodes[1:]
            self.candidate_route_names[node] = self.candidate_route_names[winner_node] + route_names

    def _update_vertex_with_node_index(self, node, winner_node, winner_weight, down_move: bool, nodes_indexes):

        l = walk_time = math.inf
        sequence_nodes = []
        route_names = []
        f = self.graph.graph[winner_node][node]
        if nodes_indexes:
            start_index = nodes_indexes[node]
            if start_index < f.size:
                l = f.buses[start_index].a
                sequence_nodes = f.buses[start_index].nodes
                route_names = f.buses[start_index].route_names
        if f.walk:
            walk_time = winner_weight + f.walk.w
        if walk_time < l:
            new_weight, sequence_nodes, route_names = walk_time, f.walk.nodes, f.walk.route_names
        else:
            new_weight, sequence_nodes, route_names = l, sequence_nodes, route_names

        if node in self.candidate_weights.keys():
            if new_weight < self.candidate_weights[node]:
                self.candidate_down_move[node] = down_move
                self.candidate_weights[node] = new_weight
                self.candidate_priorities[node] = new_weight
                self.candidate_sequences[node] = self.candidate_sequences[winner_node] + sequence_nodes[1:]
                self.candidate_roots[node] = self.candidate_roots[winner_node] + [node]
                self.candidate_route_names[node] = self.candidate_route_names[winner_node] + route_names
        elif new_weight != math.inf:
            self.candidate_down_move[node] = down_move
            self.candidate_weights[node] = new_weight
            self.candidate_priorities[node] = new_weight
            self.candidate_roots[node] = self.candidate_roots[winner_node] + [node]
            self.candidate_sequences[node] = self.candidate_sequences[winner_node] + sequence_nodes[1:]
            self.candidate_route_names[node] = self.candidate_route_names[winner_node] + route_names

    def _update_vertex_with_node_index_new(self, node, winner_node, winner_weight, down_move: bool, nodes_indexes,
                                           schedule):

        l = walk_time = math.inf
        sequence_nodes = []
        route_names = []
        lower_index = 0
        f = self.graph.graph[winner_node][node]
        if nodes_indexes:
            start_index = nodes_indexes[node]
            if start_index < f.size:
                bus = f.buses[start_index]
                schedule = bus.next_nodes_schedule
                lower_index = bus.lower_index
                l = bus.a
                sequence_nodes = bus.nodes
                route_names = bus.route_names
            # elif f.size:
            #    lower_index = f.buses[-1].lower_index
            #    schedule = f.buses[-1].next_nodes_schedule

        if f.walk:
            walk_time = winner_weight + f.walk.w
        if walk_time < l:
            new_weight, sequence_nodes, route_names = walk_time, f.walk.nodes, f.walk.route_names
        else:
            new_weight, sequence_nodes, route_names = l, sequence_nodes, route_names

        if node in self.candidate_weights:
            if new_weight < self.candidate_weights[node]:
                self.candidate_down_move[node] = down_move
                self.candidate_weights[node] = new_weight
                self.candidate_priorities[node] = new_weight
                self.candidate_sequences[node] = self.candidate_sequences[winner_node] + sequence_nodes[1:]
                self.candidate_roots[node] = self.candidate_roots[winner_node] + [node]
                self.candidate_route_names[node] = self.candidate_route_names[winner_node] + route_names
                self.candidate_schedule[node] = schedule
                self.lower_index[node] = lower_index
        elif new_weight != math.inf:
            self.candidate_down_move[node] = down_move
            self.candidate_weights[node] = new_weight
            self.candidate_priorities[node] = new_weight
            self.candidate_roots[node] = self.candidate_roots[winner_node] + [node]
            self.candidate_sequences[node] = self.candidate_sequences[winner_node] + sequence_nodes[1:]
            self.candidate_route_names[node] = self.candidate_route_names[winner_node] + route_names
            self.candidate_schedule[node] = schedule
            self.lower_index[node] = lower_index

    def _update_vertex_with_node_index_test(self, node, winner_node, winner_weight, down_move: bool, nodes_indexes):
        # todo: work slower then the main method
        start_index = None
        if nodes_indexes:
            start_index = nodes_indexes[node]
        new_weight, sequence_nodes, route_names = self.graph.graph[winner_node][node].arrival_with_know_index(
            winner_weight, start_index)

        if node in self.candidate_weights.keys():
            if new_weight < self.candidate_weights[node]:
                self.candidate_down_move[node] = down_move
                self.candidate_weights[node] = new_weight
                self.candidate_priorities[node] = new_weight
                self.candidate_sequences[node] = self.candidate_sequences[winner_node] + sequence_nodes[1:]
                self.candidate_roots[node] = self.candidate_roots[winner_node] + [node]
                self.candidate_route_names[node] = self.candidate_route_names[winner_node] + route_names
        elif new_weight != math.inf:
            self.candidate_down_move[node] = down_move
            self.candidate_weights[node] = new_weight
            self.candidate_priorities[node] = new_weight
            self.candidate_roots[node] = self.candidate_roots[winner_node] + [node]
            self.candidate_sequences[node] = self.candidate_sequences[winner_node] + sequence_nodes[1:]
            self.candidate_route_names[node] = self.candidate_route_names[winner_node] + route_names
