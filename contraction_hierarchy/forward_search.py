from typing import Union
import heapdict
import time
import math
from bisect import bisect_right
import logging

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

    def shortest_path(self,
                      duration: Union[float, None] = None,
                      search_with_switching_graphs=True,
                      geometrical_containers=True,
                      reach=None
                      ) -> dict:

        exception = None
        if reach:
            reach = {}

        winner_node = self.source
        winner_weight = self.start_time

        if search_with_switching_graphs:
            start_time = time.monotonic()
            while (winner_node != self.target) and (not exception):

                exception = _check_running_time(start_time, duration, "FCH")

                for node in self.graph.graph[winner_node]:
                    if not self.candidate_down_move[winner_node]:
                        if self.graph.hierarchy[node] > self.graph.hierarchy[winner_node]:
                            self._update_vertex_with_mode(node, winner_node, winner_weight, False, mode='all')
                        else:
                            self._update_vertex_with_mode(node, winner_node, winner_weight, True, mode='all')
                    elif self.graph.hierarchy[node] < self.graph.hierarchy[winner_node]:
                        self._update_vertex_with_mode(node, winner_node, winner_weight, True, mode='all')
                    elif self.candidate_route_names[winner_node][-1] == 'walk':
                        self._update_vertex_with_mode(node, winner_node, winner_weight, down_move=False, mode='bus')
                    else:
                        self._update_vertex_with_mode(node, winner_node, winner_weight, down_move=False, mode='walk')

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
        elif geometrical_containers:
            start_time = time.monotonic()
            while (winner_node != self.target) and (not exception):

                exception = _check_running_time(start_time, duration, "FCH")

                for node in self.graph.graph[winner_node]:
                    t = True
                    if reach:
                        s = reach.get((node, winner_weight, winner_node))
                        if s:
                            t = self.target in s
                    if t:
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

    def _update_vertex_with_mode(self, node, winner_node, winner_weight, down_move: bool, mode: str = 'all'):
        if mode == 'bus':
            new_weight, sequence_nodes, route_names = self.graph.graph[winner_node][node].arrival_bus(winner_weight)
        elif mode == 'walk':
            new_weight, sequence_nodes, route_names = self.graph.graph[winner_node][node].arrival_walk(winner_weight)
        else:
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
            self.candidate_sequences[node] = self.candidate_sequences[winner_node] + sequence_nodes[1:]
            self.candidate_roots[node] = self.candidate_roots[winner_node] + [node]
            self.candidate_route_names[node] = self.candidate_route_names[winner_node] + route_names

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
