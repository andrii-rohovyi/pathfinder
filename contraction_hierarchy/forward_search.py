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
        self.walk_duration = {self.source: 0}

    def shortest_path(self,
                      duration: Union[float, None] = None,
                      search_with_switching_graphs=True,
                      geometrical_containers=True,
                      max_walk_duration: float = math.inf
                      ) -> dict:

        exception = None

        winner_node = self.source
        winner_weight = self.start_time

        if search_with_switching_graphs:
            start_time = time.monotonic()
            while (winner_node != self.target) and (not exception):

                exception = _check_running_time(start_time, duration, "FCH")

                for node in self.graph.graph[winner_node]:
                    if not self.candidate_down_move[winner_node]:
                        if self.graph.hierarchy[node] > self.graph.hierarchy[winner_node]:
                            self._update_vertex_with_mode(node, winner_node, winner_weight, False,
                                                          mode='all',
                                                          max_walk_duration=max_walk_duration)
                        else:
                            self._update_vertex_with_mode(node, winner_node, winner_weight, True,
                                                          mode='all',
                                                          max_walk_duration=max_walk_duration)
                    elif self.graph.hierarchy[node] < self.graph.hierarchy[winner_node]:
                        self._update_vertex_with_mode(node, winner_node, winner_weight, True,
                                                      mode='all',
                                                      max_walk_duration=max_walk_duration)
                    elif self.candidate_route_names[winner_node][-1] == 'walk':
                        self._update_vertex_with_mode(node, winner_node, winner_weight, down_move=False,
                                                      mode='bus',
                                                      max_walk_duration=max_walk_duration)
                    else:
                        self._update_vertex_with_mode(node, winner_node, winner_weight, down_move=False,
                                                      mode='walk',
                                                      max_walk_duration=max_walk_duration)

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
                    if not self.candidate_down_move[winner_node]:
                        if self.graph.hierarchy[node] > self.graph.hierarchy[winner_node]:
                            self._update_vertex(node, winner_node, winner_weight, False,
                                                max_walk_duration=max_walk_duration)
                        elif self.target in self.graph.geometrical_containers[node]:
                            self._update_vertex(node, winner_node, winner_weight, True,
                                                max_walk_duration=max_walk_duration)
                    elif ((self.graph.hierarchy[node] < self.graph.hierarchy[winner_node]) &
                          (self.target in self.graph.geometrical_containers[node])):
                        self._update_vertex(node, winner_node, winner_weight, True,
                                            max_walk_duration=max_walk_duration)
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
                            self._update_vertex(node, winner_node, winner_weight, False,
                                                max_walk_duration=max_walk_duration)
                        else:
                            self._update_vertex(node, winner_node, winner_weight, True,
                                                max_walk_duration=max_walk_duration)
                    elif self.graph.hierarchy[node] < self.graph.hierarchy[winner_node]:
                        self._update_vertex(node, winner_node, winner_weight, True,
                                            max_walk_duration=max_walk_duration)

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

    def _update_vertex_with_mode(self,
                                 node,
                                 winner_node,
                                 winner_weight,
                                 down_move: bool,
                                 mode: str = 'all',
                                 max_walk_duration: float = math.inf):
        f = self.graph.graph[winner_node][node]
        if mode == 'bus':
            new_weight, sequence_nodes, route_names, arrival_walk = f.arrival_bus(winner_weight,
                                                                                  walk_duration=self.walk_duration[
                                                                                      winner_node],
                                                                                  max_walk_duration=max_walk_duration)
        elif mode == 'walk':
            new_weight, sequence_nodes, route_names, arrival_walk = f.arrival_walk(winner_weight,
                                                                                   walk_duration=self.walk_duration[
                                                                                       winner_node],
                                                                                   max_walk_duration=max_walk_duration)
        else:
            new_weight, sequence_nodes, route_names, arrival_walk = f.arrival(winner_weight,
                                                                              walk_duration=self.walk_duration[
                                                                                  winner_node],
                                                                              max_walk_duration=max_walk_duration)
        if node in self.candidate_weights.keys():
            if new_weight < self.candidate_weights[node]:
                self.candidate_down_move[node] = down_move
                self.candidate_weights[node] = new_weight
                self.candidate_priorities[node] = new_weight
                self.candidate_sequences[node] = self.candidate_sequences[winner_node] + sequence_nodes[1:]
                self.candidate_route_names[node] = self.candidate_route_names[winner_node] + route_names
                self.walk_duration[node] = arrival_walk
        elif new_weight != math.inf:
            self.candidate_down_move[node] = down_move
            self.candidate_weights[node] = new_weight
            self.candidate_priorities[node] = new_weight
            self.candidate_sequences[node] = self.candidate_sequences[winner_node] + sequence_nodes[1:]
            self.candidate_route_names[node] = self.candidate_route_names[winner_node] + route_names
            self.walk_duration[node] = arrival_walk

    def _update_vertex(self, node, winner_node, winner_weight, down_move: bool, max_walk_duration: float = math.inf):
        f = self.graph.graph[winner_node][node]
        new_weight, sequence_nodes, route_names, arrival_walk = f.arrival(winner_weight,
                                                                          walk_duration=self.walk_duration[winner_node],
                                                                          max_walk_duration=max_walk_duration)
        if node in self.candidate_weights.keys():
            if new_weight < self.candidate_weights[node]:
                self.candidate_down_move[node] = down_move
                self.candidate_weights[node] = new_weight
                self.candidate_priorities[node] = new_weight
                self.candidate_sequences[node] = self.candidate_sequences[winner_node] + sequence_nodes[1:]
                self.candidate_route_names[node] = self.candidate_route_names[winner_node] + route_names
                self.walk_duration[node] = arrival_walk
        elif new_weight != math.inf:
            self.candidate_down_move[node] = down_move
            self.candidate_weights[node] = new_weight
            self.candidate_priorities[node] = new_weight
            self.candidate_sequences[node] = self.candidate_sequences[winner_node] + sequence_nodes[1:]
            self.candidate_route_names[node] = self.candidate_route_names[winner_node] + route_names
            self.walk_duration[node] = arrival_walk
