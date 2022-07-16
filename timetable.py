from __future__ import annotations
from typing import List
try:
    from station import StationNode
except ImportError as e:
    print('[!]Module Unavailable : {}'.format(str(e)))
    exit(1)
class Timing(object):
    def __init__(self, stationNode: StationNode, arrival: str, departure: str):
        self.stationNode = stationNode
        self.arrival = arrival
        self.departure = departure
    @staticmethod
    def __parseTime__(tmString: str) -> int:
        return -1 if tmString == '00:00:00' else \
            sum([int(j, base=10)*(60**i)
                 for i, j in enumerate(reversed(tmString.split(':')))])
    @property
    def stopsFor(self) -> int:
        tmpArr, tmpDept = self.__parseTime__(
            self.arrival), self.__parseTime__(self.departure)
        return -1 if tmpArr == -1 or tmpDept == -1 else abs(tmpDept - tmpArr)
class TimeTable(object):
    def __init__(self, table: List[Timing]):
        self.table = table
if __name__ == '__main__':
    exit(0)