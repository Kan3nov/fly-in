try:
    from utils import ParsingError
    from models import Network, Zone, ZoneType, Connection, Drone
    from pydantic import ValidationError
except Exception as e:
    print("=" * 5, "Import Error", '=' * 5)
    print(e)
    exit()


def validate_hub(values: str, line_no: int) -> Zone:
    """Parse and validate a hub declaration's name, coordinates, and metadata.

    Args:
        values: Text following the hub directive.
        line_no: Source line number used in error messages.

    Returns:
        Zone: The zone described by the declaration.

    Raises:
        ParsingError: If the declaration has invalid syntax or values.
    """
    atts = values.split()
    if (len(atts) < 3):
        raise ParsingError(f"Syntax error at line {line_no}, " +
                           "hub attributes should be 3 at least")
    try:
        hub = Zone(name=atts[0], x=atts[1], y=atts[2])
    except Exception as e:
        raise ParsingError(f"Line #{line_no}: " +
                           "Invalid values in zone declaration" +
                           "\n" + str(e))
    if (len(atts) == 3):
        return hub
    if ("[" != atts[3][0]):
        raise ParsingError(f"Syntax error at line {line_no}, " +
                           "meta data should start with '['")
    if ("]" != atts[-1][-1]):
        raise ParsingError(f"Syntax error at line {line_no}, " +
                           "line should end with ']'")
    atts[3] = atts[3][1:]
    if (atts[3] == ""):
        atts.pop(3)
    atts[-1] = atts[-1][:-1]
    if (atts[-1] == ""):
        atts.pop(-1)
    for att in atts[3:]:
        if (len(att.split("=")) != 2):
            raise ParsingError(f"Syntax error at line {line_no}, " +
                               "meta data should be in key=value format")
        key, value = att.split("=")
        try:
            if (key == "zone"):
                hub.type = ZoneType[value.upper()]
            elif (key == "color"):
                hub.color = value
            elif (key == "max_drones"):
                hub.max_drones = value
            else:
                raise KeyError
        except KeyError as e:
            raise ParsingError(f"Syntax error at line {line_no}, " +
                               f"Invalid meta-data key '{key}'\n" + str(e))
        except ValidationError as e:
            raise ParsingError(f"Syntax error at line {line_no}, " +
                               f"Invalid value {value} for key {key}\n" +
                               str(e))
    return hub


def validate_con(values: str, line_no: int,
                 zones: dict[str, Zone]) -> Connection:
    """Parse a connection declaration and link its endpoint zones.

    Args:
        values: Text following the connection directive.
        line_no: Source line number used in error messages.
        zones: Known zones indexed by name.

    Returns:
        Connection: The connection described by the declaration.

    Raises:
        ParsingError: If endpoints or connection metadata are invalid.
    """
    atts = values.split()
    if (len(atts) < 1):
        raise ParsingError(f"Syntax error at line {line_no}, " +
                           "connection is not assigned a value")
    if (len(atts[0].split("-")) != 2):
        raise ParsingError(f"Syntax error at line {line_no}, " +
                           "invalid connection declaration")
    zone1 = atts[0].split("-")[0]
    zone2 = atts[0].split("-")[1]

    if (zone1 not in zones.keys()):
        raise ParsingError(f"Undefined zone name '{zone1}' in line {line_no}")
    elif (zone2 not in zones.keys()):
        raise ParsingError(f"Undefined zone name '{zone2}' in line {line_no}")
    con = Connection(zone1=zones[zone1], zone2=zones[zone2])
    con.zone1.neighbors.append(con.zone2)
    con.zone2.neighbors.append(con.zone1)
    if (len(atts) == 1):
        return con

    if ("[" != atts[1][0]):
        raise ParsingError(f"Syntax error at line {line_no}, " +
                           "meta data should start with '['")
    if ("]" != atts[-1][-1]):
        raise ParsingError(f"Syntax error at line {line_no}, " +
                           "line should end with ']'")
    atts[1] = atts[1][1:]
    atts[-1] = atts[-1][:-1]
    for att in atts[1:]:
        if (len(att.split("=")) != 2):
            raise ParsingError(f"Syntax error at line {line_no}, " +
                               "meta data should be in key=value format")
        key, value = att.split("=")
        if (key != "max_link_capacity"):
            raise ParsingError(f"Syntax error at line {line_no}, " +
                               f"Invalid key {key}")
        try:
            con.link_cap = int(value)
        except Exception as e:
            raise ParsingError(f"Invalid int value at line {line_no}" +
                               '\n' + str(e))
    return con


def parse(input_file: str) -> Network:
    """Parse a map file and construct its validated network.

    Args:
        input_file: Path to the map file.

    Returns:
        Network: Network defined by the map file.

    Raises:
        ParsingError: If the file cannot be read or its contents are invalid.
    """
    try:
        with open(input_file, 'r') as f:
            content = f.read()
    except Exception as e:
        raise ParsingError("Error reading map file\n" + str(e))
    lines = content.split("\n")
    # Check for nb_drones
    for line_no, line in enumerate(lines):
        line = line.strip()
        if (line == "" or line[0] == '#'):
            continue
        elif (len(line.split(":")) != 2):
            raise ParsingError(f"Syntax error in line #{line_no}")
        elif (line.split(":")[0] != "nb_drones"):
            raise ParsingError("nb_drones should be the first line")
        else:
            try:
                nb_drones = int(line.split(":")[1])
            except Exception:
                raise ParsingError("nb_drones is an invalid int")
            break
    else:
        raise ParsingError("No nb_drones line was found")
    if nb_drones <= 0:
        raise ParsingError("nb_drones must be a positive int")

    # Check for zone definitions
    zones: dict[str, Zone] = {}
    start_hub = None
    end_hub = None
    for l_num in range(line_no + 1, len(lines)):
        if (lines[l_num] == "" or lines[l_num].lstrip()[0] == "#"):
            continue
        try:
            key, value = lines[l_num].split(":")
        except Exception:
            raise ParsingError(f"Syntax error in line #{l_num}")
        if (key == "connection"):
            break
        elif (key == "hub"):
            hub = validate_hub(value, l_num)
            if hub.name in zones.keys():
                raise ParsingError(
                    f"Found duplicates for zone name: \"{hub.name}\""
                    )
            zones[hub.name] = hub
        elif (key == "start_hub"):
            if (start_hub):
                raise ParsingError("No more than one start_hub " +
                                   "should be defined")
            elif start_hub and start_hub.name in zones.keys():
                raise ParsingError(
                    f"Found duplicates for zone name: \"{start_hub.name}\""
                    )
            start_hub = validate_hub(value, l_num)
            zones[start_hub.name] = start_hub
        elif (key == "end_hub"):
            if (end_hub):
                raise ParsingError("No more than one end_hub " +
                                   "should be defined")
            elif end_hub and end_hub.name in zones.keys():
                raise ParsingError(
                    f"Found duplicates for zone name: \"{end_hub.name}\""
                    )
            end_hub = validate_hub(value, l_num)
            zones[end_hub.name] = end_hub
        else:
            raise ParsingError(f"Undefined directive at line #{l_num}")
    for zone1 in zones.values():
        for zone2 in zones.values():
            if (zone1.name == zone2.name):
                continue
            if (zone1.x == zone2.x and zone1.y == zone2.y):
                raise ParsingError(
                    f"Zones '{zone1.name}' and '{zone2.name}'"
                    " have the same coordinates"
                    )

    if (not start_hub):
        raise ParsingError("start_hub is not declared")
    elif (not end_hub):
        raise ParsingError("end_hub is not declared")

    # Check for connection definitions
    connections: list[Connection] = []
    line_no = l_num
    for l_num in range(line_no, len(lines)):
        if (lines[l_num] == "" or lines[l_num].lstrip()[0] == "#"):
            continue
        try:
            key, value = lines[l_num].split(":")
        except Exception:
            raise ParsingError(f"Syntax error in line #{l_num}")
        if (key == "connection"):
            connections.append(validate_con(value, line_no, zones))
        elif (key == "hub" and key == "start_hub" and key == "end_hub"):
            raise ParsingError("Hub declarations must be above connections " +
                               f"at line {l_num}")
        else:
            raise ParsingError("Expected 'connection' directive " +
                               f"at line {l_num}")
    for idx1 in range(len(connections)):
        for idx2 in range(idx1 + 1, len(connections)):
            if (connections[idx1] == connections[idx2]):
                raise ParsingError(
                    "Duplicate connection declarations found for " +
                    f"{str(connections[idx1])}"
                    )
    drones = []
    for x in range(1, nb_drones + 1):
        drones.append(Drone(id=x, visited=set([start_hub.name]),
                            cur=start_hub))

    start_hub.max_drones = nb_drones
    start_hub.start = True
    start_hub.drone_count = nb_drones
    start_hub.wait = nb_drones

    end_hub.max_drones = nb_drones
    end_hub.end = True
    end_hub.drone_count = 0
    cons = {}
    for meow in connections:
        cons[(meow.zone1.name, meow.zone2.name)] = meow
    return Network(
        nb_drones=nb_drones,
        start_hub=start_hub,
        end_hub=end_hub,
        zones=zones,
        cons=cons,
        drones=drones
        )
