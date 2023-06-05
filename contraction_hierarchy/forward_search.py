from typing import Union
import heapdict
import time
import math
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
        self.candidate_route_names = {self.source: []}
        self.candidate_down_move = {self.source: False}

    def shortest_path(self,
                      duration: Union[float, None] = None
                      ) -> dict:

        exception = None
        winner_route = []
        start_time = time.monotonic()

        winner_node = self.source
        winner_weight = self.start_time

        while (winner_node != self.target) and (not exception):

            exception = _check_running_time(start_time, duration, "FCH")

            for node in self.graph.graph[winner_node]:
                if not self.candidate_down_move[winner_node]:
                    if self.graph.hierarchy[node] < self.graph.hierarchy[winner_node]:
                        self._update_vertex(node, winner_node, winner_weight, True, mode='all')
                    else:
                        self._update_vertex(node, winner_node, winner_weight, False, mode='all')
                elif self.graph.hierarchy[node] < self.graph.hierarchy[winner_node]:
                    self._update_vertex(node, winner_node, winner_weight, True, mode='all')
                elif self.candidate_route_names[winner_node][-1] == 'walk':
                    down_move = (self.graph.hierarchy[self.candidate_sequences[winner_node][-2]]
                                 > self.graph.hierarchy[node])
                    self._update_vertex(node, winner_node, winner_weight, down_move=down_move, mode='bus')
                else:
                    down_move = (self.graph.hierarchy[self.candidate_sequences[winner_node][-2]]
                                 > self.graph.hierarchy[node])
                    self._update_vertex(node, winner_node, winner_weight, down_move=down_move, mode='walk')

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
                'path': winner_route,
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

    def _update_vertex(self, node, winner_node, winner_weight, down_move: bool, mode: str):
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
                self.candidate_route_names[node] = self.candidate_route_names[winner_node] + route_names
        elif new_weight != math.inf:
            self.candidate_down_move[node] = down_move
            self.candidate_weights[node] = new_weight
            self.candidate_priorities[node] = new_weight
            self.candidate_sequences[node] = self.candidate_sequences[winner_node] + sequence_nodes[1:]
            self.candidate_route_names[node] = self.candidate_route_names[winner_node] + route_names





