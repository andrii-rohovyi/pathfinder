from bisect import bisect_left
from typing import List
import math
from functools import total_ordering

from atf import ATF


@total_ordering
class Transportation:

    def __init__(self, nodes: List[int], route_names: List[str], k: int, b: int, d: int):
        self.nodes = nodes
        self.k = k
        self.b = b
        self.d = d
        self.route_names = route_names

    def travel_time(self, t: int):
        return self.k * t + self.b

    def __lt__(self, other):
        return self.d < other.d

    def __eq__(self, other):
        return self.d == other.d


def populate_transports(buses, walk):
    d = 0
    transports = []

    for i, bus in enumerate(buses):
        if walk:
            if d < bus.a - walk.w:
                d = bus.a - walk.w
                transports.append(Transportation(nodes=walk.nodes,
                                                 route_names=walk.route_names,
                                                 k=0,
                                                 b=walk.w,
                                                 d=d
                                                 ))
                d = bus.d
                transports.append(Transportation(nodes=bus.nodes,
                                                 route_names=bus.route_names,
                                                 k=-1,
                                                 b=bus.a,
                                                 d=d
                                                 ))
            else:
                d = bus.d
                transports.append(Transportation(nodes=bus.nodes,
                                                 route_names=bus.route_names,
                                                 k=-1,
                                                 b=bus.a,
                                                 d=d
                                                 ))

        else:
            transports.append(Transportation(nodes=bus.nodes,
                                             route_names=bus.route_names,
                                             k=-1,
                                             b=bus.a,
                                             d=bus.d
                                             ))
    if walk:
        transports.append(Transportation(nodes=walk.nodes,
                                         route_names=walk.route_names,
                                         k=0,
                                         b=walk.w,
                                         d=math.inf
                                         ))
    else:
        transports.append(Transportation(nodes=[],
                                         route_names=[],
                                         k=math.inf,
                                         b=math.inf,
                                         d=math.inf
                                         ))

    return transports


class TTF:

    def __init__(self, atf: ATF = None):
        """

        :param w:
        :param c: List[Tuple[int, int]]) , List of tuples with [departure, arrival time]
        """

        self.transports = populate_transports(atf.buses, atf.walk)
        self.size = len(self.transports)

    def arrival(self, t: int):
        start_index = bisect_left(self.transports, t, key=lambda x: x.d, lo=0, hi=self.size)
        l = t + self.transports[start_index].travel_time(t)
        sequence_nodes = self.transports[start_index].nodes
        route_names = self.transports[start_index].route_names

        return l, sequence_nodes, route_names
