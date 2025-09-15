"""
Core functionality for the aviro package.
"""


def hello_aviro(name: str = "World") -> str:
    """
    Return a greeting message.
    
    Args:
        name (str, optional): The name to greet. Defaults to "World".
        
    Returns:
        str: A greeting message.
        
    Examples:
        >>> hello_aviro()
        'Hello, World! Welcome to Aviro!'
        >>> hello_aviro("Alice")
        'Hello, Alice! Welcome to Aviro!'
    """
    return f"Hello, {name}! Welcome to Aviro!"


def get_version() -> str:
    """
    Get the version of the aviro package.
    
    Returns:
        str: The version string.
    """
    from . import __version__
    return __version__


class Aviro:
    """
    Main class for Aviro functionality.
    """
    
    def __init__(self, name: str = "Aviro"):
        """
        Initialize the Aviro instance.
        
        Args:
            name (str): The name for this Aviro instance.
        """
        self.name = name
    
    def greet(self, target: str = "World") -> str:
        """
        Generate a greeting from this Aviro instance.
        
        Args:
            target (str): Who to greet.
            
        Returns:
            str: A personalized greeting message.
        """
        return f"{self.name} says: Hello, {target}!"
    
    def __str__(self) -> str:
        return f"Aviro(name='{self.name}')"
    
    def __repr__(self) -> str:
        return f"Aviro(name='{self.name}')"
