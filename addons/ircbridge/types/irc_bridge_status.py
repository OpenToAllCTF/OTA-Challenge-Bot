from enum import Enum
class IrcBridgeStatus(Enum):
    """Enumeration for the possible states of an IRC bridge."""
    DISCONNECTED = 1    
    CONNECTED = 2       
    
    