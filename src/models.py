try:
    from pydantic import BaseModel, Field, ConfigDict, model_validator
    from enum import Enum
    from typing import Optional, Literal, Any, cast
    import heapq
    from itertools import count
except Exception as e:
    print(e)
    exit()


class ZoneType(Enum):
    """Types of zones and their traversal costs."""

    NORMAL = 1
    BLOCKED = -1
    RESTRICTED = 2
    PRIORITY = 1


class Drone(BaseModel):
    """Track a drone's location, route history, and movement state."""

    id: int = Field(ge=0)
    visited: set[str]
    cur: Zone
    mid_of_link: Literal[0, 1] = Field(default=0)
    moved: bool = Field(default=False)
    far_dest: Optional[Zone] = Field(default=None)

    def visit(self, next: Optional[Zone], con: Optional[Connection]) -> str:
        """Attempt to move the drone to its next zone.

        Args:
            next: Destination zone, or the far end of a restricted link.
            con: Connection being traversed; unused while completing a
                restricted-link crossing.

        Returns:
            str: Encoded move when movement succeeds, or an empty string
                when the drone cannot move.
        """
        if self.moved:
            return ""

        if (not next):
            return ""
        # If in the midst of a restricted connection
        elif (self.mid_of_link == 1):
            move = f"D{self.id}-{next.name}"
            self.cur = next
            self.mid_of_link = 0
            return move

        if (not con):
            return ""

        # For drones on the start of a restricted link
        elif (con.drone_count < con.link_cap and
                next.type == ZoneType.RESTRICTED and
                next.drone_count < next.max_drones):
            self.visited.add(self.cur.name)
            self.far_dest = next
            if (self.cur.drone_count == self.cur.max_drones):
                self.cur.wait -= 1
            self.cur.drone_count -= 1
            con.drone_count += 1
            next.drone_count += 1
            if (next.max_drones == next.drone_count):
                next.wait += 1
            self.mid_of_link = 1
            move = f"D{self.id}-{self.cur.name}-{next.name}"
            return move

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
    """Represent a drone network and coordinate its turn-by-turn simulation.

    Attributes:
        nb_drones: Number of drones in the network.
        start_hub: Starting zone shared by the drones.
        end_hub: Destination zone.
        zones: Zones indexed by name.
        cons: Connections indexed by their endpoint names.
        drones: Drones simulated in the network.
        turn_count: Number of turns processed.
        moves: Encoded moves recorded for each turn.
    """

    # Enable validation on assignment
    model_config = ConfigDict(validate_assignment=True)

    nb_drones: int = Field(ge=1)
    start_hub: Zone
    end_hub: Zone
    zones: dict[str, Zone]
    cons: dict[tuple[str, str], Connection]
    drones: list[Drone]
    turn_count: int = Field(default=0, ge=0)
    moves: list[list[str]] = Field(default_factory=list)

    def __init__(self, **kwargs: Any) -> None:
        """Initialize the network and calculate each zone's distance to goal.

        Args:
            **kwargs: Network fields accepted by the Pydantic model.

        Returns:
            None.
        """
        super().__init__(**kwargs)
        dists = {zone: float("inf") for zone in kwargs["zones"].keys()}
        dists = Network.dijkstra(kwargs["end_hub"], set(), dists)
        for zone in kwargs["zones"].values():
            zone.dist = dists[zone.name]

    @model_validator(mode="after")
    def check(self) -> "Zone":
        """Ensure the start and end zones are connected.

        Returns:
            Network: The validated network instance.

        Raises:
            ValueError: If no traversable path connects the start and end.
        """
        dists = {zone: float("inf") for zone in self.zones.keys()}
        if (Network.ucs(self.start_hub, self.end_hub, set(), dists)
                == float("inf")):
            raise ValueError("The network is disconnected; " +
                             "there's no path from start to end")
        return self

    def __str__(self) -> str:
        """Return a concise description of the network.

        Returns:
            str: Network summary including its hubs, zones, and connections.
        """
        return f"nb_drones: {self.nb_drones} " +\
               f"Start: {self.start_hub.name}, End: {self.end_hub.name}" +\
               f"\nzones: {[x for x in self.zones.keys()]}\n" +\
               f"connections: {[str(x) for x in self.cons.values()]}"

    # A*
    @staticmethod
    def a_star(start: Zone, end: Zone, visited: set[str],
               dists: dict[str, float]) -> float:
        """Find a path cost from a start zone to an end zone using A*.

        The stored distance-to-goal values act as a heuristic for the search.

        Args:
            start: Zone from which the search begins.
            end: Goal zone.
            visited: Zone names already explored and not to revisit.
            dists: Mutable mapping of zone names to tentative path costs.

        Returns:
            float: Cost of the path, or infinity if no path is found.
        """
        dists[start.name] = 0
        unvisited: list[tuple[Any, Any, Any]] = []  # minimum heap
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
    def ucs(start: Zone, end: Zone, visited: set[str],
            dists: dict[str, float]) -> float:
        """Find the least-cost path from a start zone to an end zone.

        Args:
            start: Zone from which the search begins.
            end: Goal zone.
            visited: Zone names already explored and not to revisit.
            dists: Mutable mapping of zone names to tentative path costs.

        Returns:
            float: Cost of the path, or infinity if no path is found.
        """
        dists[start.name] = 0
        unvisited: Any = []  # minimum heap
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
    def dijkstra(start: Zone, visited: set[str],
                 dists: dict[str, float]) -> dict[str, float]:
        """Find shortest path costs from a start zone to reachable zones.

        Args:
            start: Zone from which distances are computed.
            visited: Zone names already explored and not to revisit.
            dists: Mutable mapping of zone names to tentative path costs.

        Returns:
            dict[str, float]: Updated mapping of zone names to path costs.
        """
        dists[start.name] = 0
        unvisited: Any = []  # minimum heap
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

    def next_turn(self) -> Optional[int]:
        """Advance the network simulation by one turn.

        Drones are moved subject to zone and connection capacities, and the
        resulting moves are appended to the network's move history.

        Returns:
            int | None: 1 if all drones reached the end zone, 0 if the
                simulation can continue, or None if no available route exists.
        """
        dists = {zone: float("inf") for zone in self.zones.keys()}
        changed = 1
        finish = 0
        path_cache: dict[Any, Any] = {}
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
                paths: Any = []
                prio_path = [None, float("inf")]
                next_zone: Any = None
                for nebr in drone.cur.neighbors:
                    if (path_cache.get(nebr.name)):
                        paths.append(path_cache.get(nebr.name))
                    else:
                        paths.append([nebr,
                                     Network.a_star(nebr,
                                                    self.end_hub,
                                                    drone.visited.copy(),
                                                    dists.copy())]
                                     )
                        path_cache[nebr.name] = paths[-1]
                    if (nebr.type == ZoneType.PRIORITY and
                            paths[-1][1] < prio_path[1]):
                        prio_path = [nebr, paths[-1][1]]
                for path in paths:
                    path[1] += path[0].wait
                min_path = min(paths, key=lambda x: x[1])
                if (min_path[1] == float("inf")):  # If all paths are blocked
                    return None
                elif (min_path[1] == prio_path[1]):  # Prefer priority path
                    next_zone = prio_path[0]
                else:
                    next_zone = min_path[0]
                con = cast(Connection,
                           self.cons.get((drone.cur.name, next_zone.name)))
                if (not con):
                    con = cast(Connection,
                               self.cons.get((next_zone.name, drone.cur.name)))
                move = drone.visit(next_zone, con)
                if (move):
                    drone.moved = True
                    changed = 1
                    self.moves[-1].append(move)
        self.turn_count += 1
        return finish


class Zone(BaseModel):
    """Represent a location in the network and its occupancy constraints.

    Attributes:
        name: Unique zone name.
        x: Horizontal grid coordinate.
        y: Vertical grid coordinate.
        start: Whether this is the starting zone.
        end: Whether this is the destination zone.
        drone_count: Number of drones currently occupying the zone.
        max_drones: Maximum number of drones allowed in the zone.
        color: Optional display color.
        type: Traversal type and associated cost.
        neighbors: Zones connected to this zone.
        wait: Additional path cost caused by zone capacity.
        dist: Estimated distance to the destination.
    """

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
        """Validate the zone name and current occupancy.

        Returns:
            Zone: The validated zone instance.

        Raises:
            ValueError: If the name contains a hyphen or occupancy exceeds
                the zone's capacity.
        """
        if ("-" in self.name):
            raise ValueError("Zone name shouldn't include a '-'")
        elif (self.drone_count > self.max_drones):
            raise ValueError("Drone count exceeded max capacity of the " +
                             f"'{self.name}' zone")
        return self

    def __str__(self) -> str:
        """Return the zone name and grid coordinates.

        Returns:
            str: Concise zone description.
        """
        return f"{self.name}" +\
               f":({self.x}, {self.y})"

    def __repr__(self) -> str:
        """Return a detailed representation of the zone.

        Returns:
            str: Zone details including coordinates and configuration.
        """
        return f"Zone {self.name}" +\
               f"\nCoordinates:({self.x}, {self.y})" +\
               f"\nMax_drones: {self.max_drones}" +\
               f"\nType: {self.type.value}" +\
               f"\nColor: {self.color}"


class Connection(BaseModel):
    """Represent a capacity-limited link between two zones.

    Attributes:
        zone1: First endpoint.
        zone2: Second endpoint.
        link_cap: Maximum number of drones allowed on the link per turn.
        drone_count: Number of drones currently using the link.
    """

    # Enable validation on assignment
    model_config = ConfigDict(validate_assignment=True)

    zone1: Zone
    zone2: Zone
    link_cap: int = Field(default=1, ge=1)
    drone_count: int = Field(default=0)

    @model_validator(mode="after")
    def check(self) -> "Zone":
        """Validate the current number of drones on the connection.

        Returns:
            Connection: The validated connection instance.

        Raises:
            ValueError: If the current drone count exceeds link capacity.
        """
        if (self.drone_count > self.link_cap):
            raise ValueError(f"Drone count exceeded {self} link capacity")
        return self

    def __eq__(self, other: Any) -> bool:
        """Compare connections by their ordered endpoint zones.

        Args:
            other: Object to compare with this connection.

        Returns:
            bool: Whether ``other`` is a connection with matching endpoints.
        """
        if (not isinstance(other, Connection)):
            return False
        return (self.zone1 == other.zone1 and
                self.zone2 == other.zone2)

    def __str__(self) -> str:
        """Return the connection's endpoint names.

        Returns:
            str: Endpoint names joined by a hyphen.
        """
        return f"{self.zone1.name}-{self.zone2.name}"

    def __repr__(self) -> str:
        """Return a representation of the connection and its capacity.

        Returns:
            str: Endpoint names and link capacity.
        """
        return f"{self.zone1.name}-{self.zone2.name} cap: {self.link_cap}"
