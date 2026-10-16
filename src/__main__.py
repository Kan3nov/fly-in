try:
    from parser import parse
    import sys
except Exception as e:
    print(e)


if __name__ == "__main__":
    if (len(sys.argv) != 3):
        print("Invalid number of arguments, should be 3")
        exit()
    try:
        print(parse(sys.argv[1]))
    except Exception as e:
        print(e)
        exit()
