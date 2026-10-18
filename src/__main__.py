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
        # while graph.next_turn():
        #     ...
        # print(graph.moves)
        # print(graph.nb_turns)
    except Exception as e:
        print(e)
        exit()
