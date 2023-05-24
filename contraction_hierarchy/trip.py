import math
from typing import Tuple, List
from functools import total_ordering


@total_ordering
class Bus:

    def __init__(self, nodes: List[int], route_names: List[str], c: Tuple[int, int] = None):
        if not c:
            c = []

        self.nodes = nodes
        self.d, self.a = c
        self.route_names = route_names

    def __lt__(self, other):
        return self.d < other.d

    def __eq__(self, other):
        return self.d == other.d


class Walk:

    def __init__(self, nodes: List[int], w: int = None):
        if not w:
            w = math.inf

        self.nodes = nodes
        self.w = w
        self.route_names = ['walk'] * (len(nodes) - 1)

