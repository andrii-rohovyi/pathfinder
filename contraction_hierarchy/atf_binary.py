from typing import List, Tuple
import math
# from bisect import bisect_left
from binary_search import bisect_right
from bucket import Bucket

from trip import Walk, Bus


class ATF_Uniform:

    def __init__(self, walk: Walk = None, buses: List[Bus] = None):
        """
        Arrival Time Function.
        More detailed you can find
         by link: https://oliviermarty.net/docs/olivier_marty_contraction_hierarchies_rapport.pdf
        :param walk: Walk profile between nodes
        :param buses: List[Bus] , List of Buses between 2 nodes
        """

        self.walk = walk
        self.buses = buses
        self.buckets = []
        self.calculate_buckets()
        self.size = len(self.buckets)
        self.one_bus = len(self.buses) == 1

    def calculate_buckets(self):
        if len(self.buses) > 1:
            delta = self.buses[1].d - self.buses[0].d
            departure = self.buses[0].d
            buses = [self.buses[0]]

            for i, bus in enumerate(self.buses[2:]):
                delta_new = bus.d - self.buses[i + 1].d
                if delta_new != delta:
                    bucket = Bucket(departure, delta, buses)
                    self.buckets.append(bucket)
                    departure = self.buses[i + 1].d
                    delta = delta_new
                    buses = [self.buses[i + 1]]
                else:
                    buses.append(self.buses[i + 1])
            buses.append(self.buses[-1])
            bucket = Bucket(departure, delta, buses)
            self.buckets.append(bucket)

    def arrival(self, t: int) -> Tuple[int, List[int], List[str]]:
        """
        Calculate arrival time to next station
        :param t: start_time
        :return:
        """
        l = math.inf
        sequence_nodes = []
        route_names = []
        bus = None
        if self.buses:
            if not self.one_bus:
                bucket_index = bisect_right(self.buckets, t, key=lambda x: x.d, lo=0, hi=self.size)
                if bucket_index == 0:
                    bus = self.buckets[0].buses[0]
                else:
                    bus = self.buckets[bucket_index-1].arrival(t)
                    if not bus:
                        if bucket_index < self.size:
                            bus = self.buckets[bucket_index].buses[0]
            elif self.buses[0].d >= t:
                bus = self.buses[0]
            if bus:
                l = bus.a
                sequence_nodes = bus.nodes
                route_names = bus.route_names
        if self.walk:
            walk_time = t + self.walk.w
            if walk_time < l:
                return walk_time, self.walk.nodes, self.walk.route_names
        return l, sequence_nodes, route_names
