from __future__ import annotations
try:
    from station import StationNode
    from timetable import TimeTable
except ImportError as e:
    print('[!]Module Unavailable : {}'.format(str(e)))
    exit(1)
class Train(object):
    def __init__(self, number: int, name: str, startAt: StationNode, endAt: StationNode, timeTable: TimeTable):
        self.number = number
        self.name = name
        self.source = startAt
        self.destination = endAt
        self.timeTable = timeTable
if __name__ == '__main__':
    print('handler')
    exit(0)