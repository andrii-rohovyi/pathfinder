from typing import List
from heapq import merge
import math

from trip import Walk, Bus


class ATF:

    def __init__(self, walk: Walk, buses: List[Bus]):
        """

        :param w:
        :param c: List[Tuple[int, int]]) , List of tuples with [departure, arrival time]
        """

        self.walk = walk
        self.buses = buses
        self.size = len(buses)

    def cut(self):
        r = list()
        i = 0
        while i < self.size:
            if r:
                d, a = r[-1].c
                if self.buses[i].c[1] > a:
                    if d < self.buses[i].c[0]:
                        r.append(self.buses[i])
                    i += 1
                elif d == self.buses[i].c[0]:
                    r.pop()
                    r.append(self.buses[i])
                    i += 1
                else:
                    r.pop()
            else:
                r += [self.buses[i]]
                i += 1
        self.buses = r
        self.size = len(r)

    def composition(self, f):
        cc, cw, wc = [], [], []

        w = self.walk.w + f.walk.w
        w_nodes = f.walk.nodes + self.walk.nodes[1:]
        walk = Walk(nodes=w_nodes, w=w)

        i = 0
        j = 0
        while i < f.size and j < self.size:
            if i + 1 < f.size and f.buses[i + 1].c[1] <= self.buses[j].c[0]:
                i += 1
            elif f.buses[i].c[1] <= self.buses[j].c[0]:
                cc_c = (f.buses[i].c[0], self.buses[j].c[1])
                cc_nodes = f.buses[i].nodes + self.buses[j].nodes[1:]
                cc_route_names = f.buses[i].route_names + self.buses[j].route_names
                bus = Bus(nodes=cc_nodes, c=cc_c, route_names=cc_route_names)
                cc.append(bus)
                i += 1
                j += 1
            else:
                j += 1

        if self.walk.w != math.inf:
            for i in range(f.size):
                cw_c = (f.buses[i].c[0], f.buses[i].c[1] + self.walk.w)
                cw_nodes = f.buses[i].nodes + self.walk.nodes[1:]
                cw_route_names = f.buses[i].route_names + self.walk.route_names
                bus = Bus(nodes=cw_nodes, c=cw_c, route_names=cw_route_names)
                cw.append(bus)

        if f.walk.w != math.inf:
            for j in range(self.size):
                wc_c = (self.buses[j].c[0] - f.walk.w, self.buses[j].c[1])
                wc_nodes = f.walk.nodes + self.buses[j].nodes[1:]
                wc_route_names = f.walk.route_names + self.buses[j].route_names
                bus = Bus(nodes=wc_nodes, c=wc_c, route_names=wc_route_names)
                wc.append(bus)

        c = list(merge(cc, cw, wc, key=lambda x: x.c))
        g = ATF(walk=walk, buses=c)
        g.cut()
        return g

    def arrival(self, t: int):
        l = math.inf
        sequence_nodes = []
        route_names = []
        if self.buses:
            i = 0
            while i < self.size:
                if self.buses[i].c[0] >= t:
                    l = self.buses[i].c[1]
                    sequence_nodes = self.buses[i].nodes
                    route_names = self.buses[i].route_names
                    i = self.size
                i += 1
        walk_time = t + self.walk.w
        if walk_time < l:
            return walk_time, self.walk.nodes, self.walk.route_names
        else:
            return l, sequence_nodes, route_names


def min_atf(f1: ATF, f2: ATF):

    if f1.walk.w > f2.walk.w:
        walk = f2.walk
    else:
        walk = f1.walk

    buses = list(merge(f1.buses, f2.buses, key=lambda x: x.c))
    g = ATF(walk=walk, buses=buses)
    g.cut()
    return g
