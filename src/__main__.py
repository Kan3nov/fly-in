try:
    from parser import parse
    import sys
    from utils import compute_time
    from gui import display_simulation
except Exception as e:
    print(e)
    exit()


@compute_time
def main():
    if (len(sys.argv) != 3):
        print("Invalid number of arguments, should be 2")
        exit()
    try:
        graph = parse(sys.argv[1])
        dists = {zone.name: float("inf") for zone in graph.zones.values()}
        print("Map name:", sys.argv[1])
        print("The distance between start and end:",
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
