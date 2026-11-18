try:
    from parser import parse
    import sys
    from gui import display_simulation
except Exception as e:
    print(e)
    exit()


def main() -> None:
    """Run the map simulation from command-line arguments.

    The first argument is the map file, and the second is the output path
    for the generated moves.

    Returns:
        None: This function writes the moves and displays the simulation.
    """
    if (len(sys.argv) != 3):
        print("Invalid number of arguments, should be 2")
        exit()
    try:
        graph = parse(sys.argv[1])
        dists = {zone.name: float("inf") for zone in graph.zones.values()}
        print("Map name:", sys.argv[1])
        print("Distance between start and end:",
              graph.ucs(graph.start_hub, graph.end_hub, set(), dists))
        while not graph.next_turn():
            ...
        print("Number of turns:", graph.turn_count)
        with open(sys.argv[2], 'w') as f:
            moves = []
            for move in graph.moves:
                moves.append(" ".join(move))
            f.write("\n".join(moves))
        display_simulation(graph)
    except Exception as e:
        print(e)
        exit()


if __name__ == "__main__":
    main()
