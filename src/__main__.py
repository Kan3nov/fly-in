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
    # try:
    graph = parse(sys.argv[1])
    dists = {zone.name: float("inf") for zone in graph.zones}
    print("map name:", sys.argv[1])
    print("the distance between start and end :",
          graph.ucs(graph.start_hub, graph.end_hub, set(), dists))
    while not graph.next_turn():
        print("turn:", graph.turn_count)
    print("number of turns: ", graph.turn_count)
    for move in graph.moves:
        print(" ".join(move))
    # except Exception as e:
    #     print(e)
    #     exit()
