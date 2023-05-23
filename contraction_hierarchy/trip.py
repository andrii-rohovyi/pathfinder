import math
from typing import Tuple, List


class Bus:

    def __init__(self, nodes: List[int], route_names: List[str], c: Tuple[int, int] = None):
        if not c:
            c = []

        self.nodes = nodes
        self.c = c
        self.route_names = route_names


class Walk:

    def __init__(self, nodes: List[int], w: int = None):
        if not w:
            w = math.inf

        self.nodes = nodes
        self.w = w
        self.route_names = ['walk'] * (len(nodes) - 1)

