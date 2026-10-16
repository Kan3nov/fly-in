try:
    from pydantic import BaseModel, Field, ConfigDict, model_validator
    from enum import Enum
    from typing import Optional
except Exception as e:
    print(e)


class ZoneType(Enum):
    NORMAL = "normal"
    BLOCKED = "blocked"
    RESTRICTED = "restricted"
    PRIORITY = "priority"


class Network(BaseModel):
    # Enable validation on assignment
    model_config = ConfigDict(validate_assignment=True)

    nb_drones: int = Field(ge=1)
    start_hub: Zone
    end_hub: Zone
    zones: list[Zone]
    cons: list[Connection]

    def __str__(self) -> str:
        return f"nb_drones: {self.nb_drones} " +\
               f"Start: {self.start_hub.name}, End: {self.end_hub.name}" +\
               f"\nzones: {[x.name for x in self.zones]}\n" +\
               f"connections: {[str(x) for x in self.cons]}"


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
