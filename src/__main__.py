try:
    from parser import parse
    import sys
except Exception as e:
    print(e)
    exit()


if __name__ == "__main__":
    if (len(sys.argv) != 3):
        print("Invalid number of arguments, should be 2")
        exit()
    try:
        graph = parse(sys.argv[1])
        dists = {zone.name: float("inf") for zone in graph.zones}
        print(graph.ucs(graph.start_hub, graph.end_hub, set(), dists))
        while not graph.next_turn():
            ...
        print(graph.turn_count)
    except Exception as e:
        print(e)
        exit()
