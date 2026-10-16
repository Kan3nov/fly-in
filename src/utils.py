class ParsingError(Exception):
    def __init__(self, msg: str):
        super().__init__(self)
        self.msg = msg

    def __str__(self) -> str:
        return '=' * 5 + "Parsing Error" + '=' * 5 + '\n' + self.msg
