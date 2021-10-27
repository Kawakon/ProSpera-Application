class ProgramEndError(Exception):
    """
        Exception that occurs when end_program global variable is set to True. Allows Prospera
        application to continue.

        Attributes:

        message - Details reason for termination of program
    """

    def __init__(self, message = "End of program variable set due to error") -> None:
        self.message = message
        super().__init__(self.message)

    def __str__(self) -> str:
        return self.message