import math
from typing import Tuple, List
from functools import total_ordering


@total_ordering
class Bus:

    def __init__(self, nodes: List[int], route_names: List[str], c: Tuple[int, int],
                 arrival_walk: int = 0, departure_walk: int = 0):

        self.nodes = nodes
        self.d, self.a = c
        self.route_names = route_names
        self.departure_walk = departure_walk
        self.arrival_walk = arrival_walk

    def __lt__(self, other):
        return self.d < other.d

    def __eq__(self, other):
        return self.d == other.d


class Walk:

    def __init__(self, nodes: List[int] = None, w: int = math.inf):

        self.nodes = nodes
        self.w = w
        if nodes:
            self.route_names = ['walk'] * (len(nodes) - 1)
        else:
            self.route_names = None

