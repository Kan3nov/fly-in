class ParsingError(Exception):
    """Report invalid map-file syntax or values."""

    def __init__(self, msg: str):
        """Create a parsing error with a descriptive message.

        Args:
            msg: Explanation of the parsing failure.

        Returns:
            None.
        """
        super().__init__(self)
        self.msg = msg

    def __str__(self) -> str:
        """Format the parsing error for display.

        Returns:
            str: Error heading followed by the stored message.
        """
        return '=' * 5 + "Parsing Error" + '=' * 5 + '\n' + self.msg


class GraphError(Exception):
    """Report an invalid or unusable network graph."""

    def __init__(self, msg: str):
        """Create a graph error with a descriptive message.

        Args:
            msg: Explanation of the graph failure.

        Returns:
            None.
        """
        super().__init__(self)
        self.msg = msg

    def __str__(self) -> str:
        """Format the graph error for display.

        Returns:
            str: Error heading followed by the stored message.
        """
        return '=' * 5 + "Graph Error" + '=' * 5 + '\n' + self.msg
