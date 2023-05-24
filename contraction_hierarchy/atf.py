from typing import List
import math
from bisect import bisect_left

from trip import Walk, Bus


class ATF:
    __slots__ = "walk", 'buses', 'size'

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
                d, a = r[-1].d,  r[-1].a
                if self.buses[i].a > a:
                    if d < self.buses[i].d:
                        r.append(self.buses[i])
                    i += 1
                elif d == self.buses[i].d:
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
            if i + 1 < f.size and f.buses[i + 1].a <= self.buses[j].d:
                if self.walk.w != math.inf:
                    cw_c = (f.buses[i].d, f.buses[i].a + self.walk.w)
                    cw_nodes = f.buses[i].nodes + self.walk.nodes[1:]
                    cw_route_names = f.buses[i].route_names + self.walk.route_names
                    bus = Bus(nodes=cw_nodes, c=cw_c, route_names=cw_route_names)
                    cw.append(bus)

                i += 1
            elif f.buses[i].a <= self.buses[j].d:
                cc_c = (f.buses[i].d, self.buses[j].a)
                cc_nodes = f.buses[i].nodes + self.buses[j].nodes[1:]
                cc_route_names = f.buses[i].route_names + self.buses[j].route_names
                bus = Bus(nodes=cc_nodes, c=cc_c, route_names=cc_route_names)
                cc.append(bus)

                if self.walk.w != math.inf:
                    cw_c = (f.buses[i].d, f.buses[i].a + self.walk.w)
                    cw_nodes = f.buses[i].nodes + self.walk.nodes[1:]
                    cw_route_names = f.buses[i].route_names + self.walk.route_names
                    bus = Bus(nodes=cw_nodes, c=cw_c, route_names=cw_route_names)
                    cw.append(bus)
                i += 1

                if f.walk.w != math.inf:
                    wc_c = (self.buses[j].d - f.walk.w, self.buses[j].a)
                    wc_nodes = f.walk.nodes + self.buses[j].nodes[1:]
                    wc_route_names = f.walk.route_names + self.buses[j].route_names
                    bus = Bus(nodes=wc_nodes, c=wc_c, route_names=wc_route_names)
                    wc.append(bus)
                j += 1
            else:

                if f.walk.w != math.inf:
                    wc_c = (self.buses[j].d - f.walk.w, self.buses[j].a)
                    wc_nodes = f.walk.nodes + self.buses[j].nodes[1:]
                    wc_route_names = f.walk.route_names + self.buses[j].route_names
                    bus = Bus(nodes=wc_nodes, c=wc_c, route_names=wc_route_names)
                    wc.append(bus)
                j += 1

        c = cc + cw + wc
        c.sort()
        g = ATF(walk=walk, buses=c)
        g.cut()
        return g

    def arrival(self, t: int):
        l = math.inf
        sequence_nodes = []
        route_names = []
        start_index = bisect_left(self.buses, t, key=lambda x: x.d)
        if start_index < self.size:
            l = self.buses[start_index].a
            sequence_nodes = self.buses[start_index].nodes
            route_names = self.buses[start_index].route_names
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

    buses = f1.buses + f2.buses
    buses.sort()
    g = ATF(walk=walk, buses=buses)
    g.cut()
    return g
