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
    mid_of_link: Literal[0, 1] = Field(default=0)
    moved: bool = Field(default=False)
    far_dest: Optional[Zone] = Field(default=None)

    def visit(self, next: Optional[Zone], con: Optional[Connection]) -> str:
        """
        things to update:
            next, cur:
                - drone_count
                - wait
            con:
                - drone_count
            self.cur = ?
            self.mid_of_link
        """
        if self.moved:
            return ""

        # If in the midst of a restricted connection
        if (self.mid_of_link == 1):
            move = f"D{self.id}-{self.cur.name}-{next.name}"
            self.cur = next
            self.mid_of_link = (self.mid_of_link + 1) % 2
            next.drone_count += 1
            return move

        # For drones on the start of a restricted link
        elif (con.drone_count < con.link_cap and
                next.type == ZoneType.RESTRICTED):
            self.visited.add(self.cur.name)
            self.far_dest = next
            if (self.cur.drone_count == self.cur.max_drones):
                self.cur.wait -= 1
            self.cur.drone_count -= 1
            con.drone_count += 1
            if (next.max_drones == next.drone_count):
                next.wait += 1
            self.mid_of_link = (self.mid_of_link + 1) % 2
            return f"D{self.id}-{next.name}"

        # For non-restricted zones
        elif (next.drone_count < next.max_drones and
                con.drone_count < con.link_cap):
            self.visited.add(self.cur.name)
            if (self.cur.drone_count == self.cur.max_drones):
                self.cur.wait -= 1
            self.cur.drone_count -= 1
            con.drone_count += 1
            next.drone_count += 1
            self.cur = next
            if (next.max_drones == next.drone_count):
                next.wait += 1
            return f"D{self.id}-{next.name}"
        return ""


class Network(BaseModel):
    # Enable validation on assignment
    model_config = ConfigDict(validate_assignment=True)

    nb_drones: int = Field(ge=1)
    start_hub: Zone
    end_hub: Zone
    zones: list[Zone]
    cons: dict[tuple[str, str], Connection]
    drones: list[Drone]
    turn_count: int = Field(default=0, ge=0)
    moves: list[list[str]] = Field(default_factory=list)

    @model_validator(mode="after")
    def check(self) -> "Zone":
        dists = {zone.name: float("inf") for zone in self.zones}
        if (Network.ucs(self.start_hub, self.end_hub, set(), dists)
                == float("inf")):
            raise ValueError("The network is disconnected; " +
                             "there's no path from start to end")
        dists = Network.dijkstra(self.end_hub, set(), dists)
        for zone in self.zones:
            zone.dist = dists[zone.name]
        return self

    def __str__(self) -> str:
        return f"nb_drones: {self.nb_drones} " +\
               f"Start: {self.start_hub.name}, End: {self.end_hub.name}" +\
               f"\nzones: {[x.name for x in self.zones]}\n" +\
               f"connections: {[str(x) for x in self.cons.values()]}"

    # A*
    @staticmethod
    def a_star(start: Zone, end: Zone, visited: set[Zone],
               dists: dict[str, float]) -> float:
        """
        Find the shortest path from a start node to the end node.

        Adds the distance heuristc to the search which reduces the number
        of searchs needed.

        Args:
            start: the node from which the path starts
            end: the goal node where the path ends.
            visited: already visited nodes which don't need to be explored.
            dists: dictionary of all zones with their relative distance values.
        Returns:
            dict[str, float]: the overall distance from the start to the end.
        """
        dists[start.name] = 0
        unvisited = []  # minimum heap
        counter = count()
        while start != end:
            for nebr in start.neighbors:
                if nebr.name in visited or nebr.type == ZoneType.BLOCKED:
                    continue
                else:
                    nebr_dist = dists[start.name] + nebr.type.value + nebr.dist
                    if nebr_dist < dists[nebr.name]:
                        dists[nebr.name] = nebr_dist
                heapq.heappush(unvisited,
                               (dists[nebr.name], next(counter), nebr))
            if (len(unvisited) == 0):
                break
            visited.add(start.name)
            start = heapq.heappop(unvisited)[-1]
        if start == end:
            return dists[end.name]
        else:
            return float("inf")

    # Uniform Cost Search
    @staticmethod
    def ucs(start: Zone, end: Zone, visited: set[Zone],
            dists: dict[str, float]) -> float:
        """
        Find the shortest path from a start node to the end node.

        Args:
            start: the node from which the path starts
            end: the goal node where the path ends.
            visited: already visited nodes which don't need to be explored.
            dists: dictionary of all zones with their relative distance values.
        Returns:
            dict[str, float]: the overall distance from the start to the end.
        """
        dists[start.name] = 0
        unvisited = []  # minimum heap
        counter = count()
        while start != end:
            for nebr in start.neighbors:
                if nebr.name in visited or nebr.type == ZoneType.BLOCKED:
                    continue
                else:
                    nebr_dist = dists[start.name] + nebr.type.value
                    if nebr_dist < dists[nebr.name]:
                        dists[nebr.name] = nebr_dist
                heapq.heappush(unvisited,
                               (dists[nebr.name], next(counter), nebr))
            if (len(unvisited) == 0):
                break
            visited.add(start.name)
            start = heapq.heappop(unvisited)[-1]
        if start == end:
            return dists[end.name]
        else:
            return float("inf")

    @staticmethod
    def dijkstra(start: Zone, visited: set[Zone],
                 dists: dict[str, float]) -> dict[str, float]:
        """
        Find the shortest path from a start node to all other accesible nodes.

        Args:
            start: the node from which each distance is computed.
            visited: already visited nodes which don't need to be explored.
            dists: dictionary of all zones with their relative distance values.
        Returns:
            dict[str, float]: an updated distances dictionary; from start to
                each corresponding node (zone).
        """
        dists[start.name] = 0
        unvisited = []  # minimum heap
        counter = count()
        heapq.heappush(unvisited, (0, next(counter), start))
        while len(unvisited):
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
            visited.add(start.name)
        return dists

    def next_turn(self) -> int:
        """
        Move all drones to their next zone.

        Returns:
            int: if all drones reached end; return 1, otherwise 0.
        """
        dists = {zone.name: float("inf") for zone in self.zones}
        changed = 1
        finish = 0
        self.moves.append([])
        for con in self.cons.values():
            con.drone_count = 0
        for drone in self.drones:
            drone.moved = False
        while (changed and not finish):
            finish = 1
            changed = 0
            for drone in self.drones:
                if (drone.cur == self.end_hub):
                    continue
                finish = 0
                if (drone.mid_of_link == 1):
                    move = drone.visit(drone.far_dest, None)
                    self.moves[-1].append(move)
                    drone.moved = bool(move)
                    changed = int(drone.moved)
                    continue
                paths: list[list[Optional[Zone], float]] = []
                prio_path = [None, float("inf")]
                next_zone = None
                for nebr in drone.cur.neighbors:
                    paths.append([nebr,
                                  Network.ucs(nebr,
                                              self.end_hub,
                                              drone.visited.copy(),
                                              dists.copy())]
                                 )
                    if (nebr.type == ZoneType.PRIORITY and
                            paths[-1][1] < prio_path[1]):
                        prio_path = [nebr, paths[-1][1]]
                for path in paths:
                    path[1] += path[0].wait
                min_path = min(paths, key=lambda x: x[1])
                if (min_path[1] == float("inf")):  # If all paths are blocked
                    return
                elif (min_path[1] == prio_path[1]):  # Prefer priority path
                    next_zone: Zone = prio_path[0]
                else:
                    next_zone = min_path[0]
                con = self.cons.get((drone.cur.name, next_zone.name))
                if (not con):
                    con = self.cons.get((next_zone.name, drone.cur.name))
                move = drone.visit(next_zone, con)
                if (move):
                    drone.moved = True
                    changed = 1
                    self.moves[-1].append(move)
        self.turn_count += 1
        return finish


class Zone(BaseModel):
    # Enable validation on assignment
    model_config = ConfigDict(validate_assignment=True)

    name: str
    x: int
    y: int
    start: bool = Field(default=False)
    end: bool = Field(default=False)
    drone_count: int = Field(default=0, ge=0)
    max_drones: int = Field(default=1, ge=1)
    color: Optional[str] = Field(default=None)
    type: ZoneType = Field(default=ZoneType.NORMAL)
    neighbors: list[Zone] = Field(default_factory=list)
    wait: int = Field(default=0)
    dist: float = Field(default=float("inf"))

    @model_validator(mode="after")
    def check(self) -> "Zone":
        if ("-" in self.name):
            raise ValueError("Zone name shouldn't include a '-'")
        elif (self.drone_count > self.max_drones):
            raise ValueError("Drone count exceeded max capacity of the " +
                             f"'{self.name}' zone")
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

    zone1: Zone
    zone2: Zone
    link_cap: int = Field(default=1, ge=1)
    drone_count: int = Field(default=0)

    @model_validator(mode="after")
    def check(self) -> "Zone":
        if (self.drone_count > self.link_cap):
            raise ValueError(f"Drone count exceeded {self} link capacity")
        return self

    def __eq__(self, other) -> bool:
        if (not isinstance(other, Connection)):
            return False
        return self.zone1 == other.zone1 and \
            self.zone2 == other.zone2

    def __str__(self) -> str:
        return f"{self.zone1.name}-{self.zone2.name}"

    def __repr__(self):
        return f"{self.zone1.name}-{self.zone2.name} cap: {self.link_cap}"
