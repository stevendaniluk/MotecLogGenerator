#!/usr/bin/env python3

class CanByteStats():
    def __init__(self, initial_val: int = 0):
        self.min: int = initial_val
        self.max: int = initial_val
        self.range: int = 0

    def update(self, val: int):
        self.min = min(self.min, val)
        self.max = max(self.max, val)
        self.range = self.max - self.min


class CanFrameStats():
    def __init__(self, id: str, start_time: float, data: str):
        n_bytes = int(len(data) / 2)

        self.id = id
        self.msgs: int = 0
        self.bytes_min: int = n_bytes
        self.bytes_max: int = n_bytes
        self.start_time: float = start_time
        self.end_time: float = start_time
        self.byte_stats: list[CanByteStats] = []

        self._update_byte_stats(data)

    def update(self, stamp: float, data: str):
        n_bytes = int(len(data) / 2)

        self.msgs += 1
        self.end_time = stamp
        self.bytes_min = min(n_bytes, self.bytes_min)
        self.bytes_max = max(n_bytes, self.bytes_max)

        self._update_byte_stats(data)

    def avg_frequency(self):
        if self.msgs > 1:
            return self.msgs / (self.end_time - self.start_time)
        else:
            return 0.0

    def _update_byte_stats(self, data: str):
        n_bytes = int(len(data) / 2)

        for i in range(n_bytes):
            name = f"byte_{str(i)}"
            val = int(f"0x{data[2*i:2*i + 2]}", 16)

            if i + 1 > len(self.byte_stats):
                self.byte_stats.append(CanByteStats(val))
            else:
                self.byte_stats[i].update(val)

    def __str__(self):
        return "{:10} | {:9} |  {:6.2f}".format(self.id, self.msgs, self.avg_frequency())


def parse_can_line(line):
    stamp, bus, msg = line.split()
    stamp = float(stamp[1:-1])
    id, data = msg.split("#")

    return stamp, id, data


def get_id_stats_from_lines(lines):
    id_stats = {}
    for line in lines:
        stamp, id, data = parse_can_line(line)
        bytes = int(len(data) / 2)

        if id not in id_stats:
            id_stats[id] = CanFrameStats(id, float(stamp), data)
        else:
            id_stats[id].update(float(stamp), data)

    return id_stats
