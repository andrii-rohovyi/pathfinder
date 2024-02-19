from bisect import bisect_left
from typing import List
import math
from functools import total_ordering

from atf import ATF


@total_ordering
class Transportation:

    def __init__(self, nodes: List[int], route_names: List[str], k: int, b: int, d: int):
        """
        Class responsible to different ways of transportation from node1 to node2
        Global formula looks in the next way:
                        travel_time = k * start_time + b

        :param nodes: [start_node, end_node] of transportation
        :param route_names: Names of sequence of public transport or "walk" in case of walking, which we need to use
                            for transferring from start_node to end_node
        :param k: k in formula for calculation travel_time
        :param b: b in formula for calculation travel_time
        :param d: Departure time of the sector for which we use calculation formula
        """
        self.nodes = nodes
        self.k = k
        self.b = b
        self.d = d
        self.route_names = route_names

    def travel_time(self, t: int) -> int:
        """
        Calculation of the travel time in seconds needed to move from start_node to end_node
        Global formula looks in the next way: travel_time = k * start_time + b
        :param t: start_time of the function activation
        :return:
        """
        return self.k * t + self.b

    def __lt__(self, other) -> bool:
        return self.d < other.d

    def __eq__(self, other) -> bool:
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
        Travel Time Function profile. Init converts ATF to TTF
        :param atf: ATF : ATF which we would like to convert into TTF
        """

        self.transports = populate_transports(atf.buses, atf.walk)
        self.size = len(self.transports)

    def arrival(self, t: int):
        """
        Calculate arrival time

        :param t: start time in unix-time
        :return: arrival time in unix-time
        """

        start_index = bisect_left(self.transports, t, key=lambda x: x.d, lo=0, hi=self.size)
        l = t + self.transports[start_index].travel_time(t)
        sequence_nodes = self.transports[start_index].nodes
        route_names = self.transports[start_index].route_names

        return l, sequence_nodes, route_names
