try:
    from typing import Any, Callable
    from time import time
    from functools import wraps
except Exception as e:
    print(e)
    exit()


class ParsingError(Exception):
    def __init__(self, msg: str):
        super().__init__(self)
        self.msg = msg

    def __str__(self) -> str:
        return '=' * 5 + "Parsing Error" + '=' * 5 + '\n' + self.msg


class GraphError(Exception):
    def __init__(self, msg: str):
        super().__init__(self)
        self.msg = msg

    def __str__(self) -> str:
        return '=' * 5 + "Graph Error" + '=' * 5 + '\n' + self.msg


# tbd
def compute_time(func: Callable[..., Any]) -> Callable[..., Any]:
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        print("Executing ", func.__name__, "...", sep="")
        time1 = time()
        result = func(*args, **kwargs)
        time2 = time()
        print(f"Execution took {time2 - time1:.3f} seconds")
        return result
    return wrapper
