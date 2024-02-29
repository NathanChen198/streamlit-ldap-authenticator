# Author    : Nathan Chen
# Date      : 16-Feb-2024


class DeprecationError(Exception):
    """
    Exceptions raised for possible deprecation.

    ## Attributes
    message: str
        The custom error message to display.
    """
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class AdAttributeError(Exception):
    """ Exceptions raised for Active Directory attribute error.
    
    ## Attributes
    message: str
        The custom error message to display.
    """
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(self.message)


class CookieError(Exception):
    """ Exceptions raised for decode cookie.

    ## Attributes
    message: str
        The custom error message to display.
    """
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(self.message)