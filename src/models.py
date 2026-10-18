try:
    from pydantic import BaseModel, Field, ConfigDict, model_validator
    from enum import Enum
    from typing import Optional, Literal
    import heapq
    from itertools import count
except Exception as e:
    print(e)
    exit()


class ZoneType(Enum):
    NORMAL = 1
    BLOCKED = -1
    RESTRICTED = 2
    PRIORITY = 1


class Drone(BaseModel):
    id: int = Field(ge=0)
    visited: set[str]
    cur: Zone
    move: Literal[0, 1] = Field(default=0)

    def visit(self, next_zone: Zone):  # TBM
        self.cur.wait -= 1
        next_zone.wait += 1
        self.cur = next_zone


class Network(BaseModel):
    # Enable validation on assignment
    model_config = ConfigDict(validate_assignment=True)

    nb_drones: int = Field(ge=1)
    moves: int = Field(default=0, ge=0)
    start_hub: Zone
    end_hub: Zone
    zones: list[Zone]
    cons: list[Connection]
    drones: list[Drone]

    @model_validator(mode="after")
    def check(self) -> "Zone":
        dists = {zone.name: float("inf") for zone in self.zones}
        if (Network.dijkstra(self.start_hub, self.end_hub, set(), dists)
                == float("inf")):
            raise ValueError("The network is disconnected; " +
                             "there's no path from start to end")
        return self

    def __str__(self) -> str:
        return f"nb_drones: {self.nb_drones} " +\
               f"Start: {self.start_hub.name}, End: {self.end_hub.name}" +\
               f"\nzones: {[x.name for x in self.zones]}\n" +\
               f"connections: {[str(x) for x in self.cons]}"

    @staticmethod
    def dijkstra(start: Zone, end: Zone, visited: set[Zone],
                 dists: dict[str, float]) -> float:
        dists[start.name] = 0
        unvisited = []
        counter = count()
        # min heap
        heapq.heappush(unvisited, (dists[start.name], next(counter), start))
        while start != end and len(unvisited):
            start = heapq.heappop(unvisited)[-1]
            for nebr in start.neighbors:
                if nebr.name in visited or nebr.type == ZoneType.BLOCKED:
                    continue
                else:
                    nebr_dist = dists[start.name] + nebr.type.value
                    if nebr_dist < dists[nebr.name]:
                        dists[nebr.name] = nebr_dist
                heapq.heappush(unvisited,
                               (dists[nebr.name], next(counter), nebr))
                print(unvisited)
            visited.add(start.name)
        if start == end:
            return dists[end.name]
        else:
            return float("inf")

    def next_turn(self) -> None:
        dists = {zone.name: float("inf") for zone in self.zones}
        for zone in self.zones:
            zone.wait = 0
        for drone in self.drones:
            paths = []
            prio_path = (None, float("inf"))
            next_zone = None
            for nebr in drone.cur.neighbors:
                paths.append((nebr,
                              Network.dijkstra(nebr,
                                               self.end_hub,
                                               drone.visited.copy(),
                                               dists.copy()))
                             )
                if nebr.type == (ZoneType.PRIORITY and
                                 paths[-1][1] < prio_path[1]):
                    prio_path = (nebr, paths[-1][1])
            for path in paths:
                path[1] += path[0].wait
            min_path = min(paths, key=lambda x: x[1])
            if (min_path[1] == float("inf")):  # all paths is blocked
                return
            elif (min_path[1] == prio_path[1]):  # Prefer priority path
                next_zone = prio_path[0]
            else:
                next_zone = min_path[0]
            drone.visit(next_zone)


class Zone(BaseModel):
    # Enable validation on assignment
    model_config = ConfigDict(validate_assignment=True)

    name: str
    x: int
    y: int
    start: bool = Field(default=False)
    end: bool = Field(default=False)
    max_drones: int = Field(default=1, ge=1)
    color: Optional[str] = Field(default=None)
    type: ZoneType = Field(default=ZoneType.NORMAL)
    neighbors: list[Zone] = Field(default_factory=list)
    wait: int = Field(default=0)

    @model_validator(mode="after")
    def check(self) -> "Zone":
        if ("-" in self.name):
            raise ValueError("Zone name shouldn't include a '-'")
        return self

    def __str__(self) -> str:
        return f"{self.name}" +\
               f":({self.x}, {self.y})"

    def __repr__(self) -> str:
        return f"Zone {self.name}" +\
               f"\nCoordinates:({self.x}, {self.y})" +\
               f"\nMax_drones: {self.max_drones}" +\
               f"\nType: {self.type.value}" +\
               f"\nColor: {self.color}"


class Connection(BaseModel):
    # Enable validation on assignment
    model_config = ConfigDict(validate_assignment=True)

    link_cap: int = Field(default=1, ge=1)
    zone1: Zone
    zone2: Zone

    def __eq__(self, other) -> bool:
        return self.zone1 == other.zone1 and \
            self.zone2 == other.zone2

    def __str__(self) -> str:
        return f"{self.zone1.name}-{self.zone2.name}"

    def __repr__(self):
        return f"{self.zone1.name}-{self.zone2.name} cap: {self.link_cap}"
