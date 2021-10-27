class InvalidMACError(Exception):
    """
        Exception that occurs when a given MAC address is invalid.

        Attributes:

        message - Details that MAC address is incorrect
    """
    
    def __init__(self, message = "Invalid MAC address") -> None:
        self.message = message
        super().__init__(self.message)
    
    def __str__(self) -> str:
        return super().__str__()