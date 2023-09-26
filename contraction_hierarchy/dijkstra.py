from typing import Union
import heapdict
import time
import math
import logging

from graph import TransportGraph
from algorithms_wrapper import _check_running_time
from utils import to_milliseconds


class Dijkstra:
    def __init__(self, graph: TransportGraph, start_time: int, start_node: int, end_node: int):
        self.graph = graph

        self.source = start_node
        self.target = end_node
        self.start_time = start_time

        self.candidate_weights = {self.source: start_time}
        self.candidate_priorities = heapdict.heapdict({self.source: start_time})
        self.candidate_sequences = {self.source: [self.source]}
        self.candidate_route_names = {self.source: []}

    def shortest_path(self,
                      duration: Union[float, None] = None,
                      ) -> dict:

        exception = None

        winner_node = self.source
        winner_weight = self.start_time

        start_time = time.monotonic()
        while (winner_node != self.target) and (not exception):

            exception = _check_running_time(start_time, duration, "FCH")

            for node, f in self.graph.graph[winner_node].items():
                self._update_vertex(node, winner_node, winner_weight, f)

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
        if exception:
            return {
                'path': self.candidate_sequences[winner_node],
                'routes': self.candidate_route_names[winner_node],
                'arrival': winner_weight,
                'duration': to_milliseconds(time.monotonic() - start_time)
            }

        return {
            'path': self.candidate_sequences[self.target],
            'routes': self.candidate_route_names[winner_node],
            'arrival': winner_weight,
            'duration': to_milliseconds(time.monotonic() - start_time)
        }

    def _update_vertex(self, node, winner_node, winner_weight, f):
        new_weight, sequence_nodes, route_names = f.arrival(winner_weight)
        if node in self.candidate_weights.keys():
            if new_weight < self.candidate_weights[node]:
                self.candidate_weights[node] = new_weight
                self.candidate_priorities[node] = new_weight
                self.candidate_sequences[node] = self.candidate_sequences[winner_node] + sequence_nodes[1:]
                self.candidate_route_names[node] = self.candidate_route_names[winner_node] + route_names
        elif new_weight != math.inf:
            self.candidate_weights[node] = new_weight
            self.candidate_priorities[node] = new_weight
            self.candidate_sequences[node] = self.candidate_sequences[winner_node] + sequence_nodes[1:]
            self.candidate_route_names[node] = self.candidate_route_names[winner_node] + route_names
