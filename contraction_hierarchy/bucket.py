from math import ceil


class Bucket:

    def __init__(self, d, delta, buses):
        self.d = d
        self.delta = delta
        self.buses = buses
        self.size = len(buses)

    def arrival(self, arrival_time):

        start_index = ceil((arrival_time - self.d) / self.delta)
        if start_index < self.size:
            return self.buses[start_index]
        return None
