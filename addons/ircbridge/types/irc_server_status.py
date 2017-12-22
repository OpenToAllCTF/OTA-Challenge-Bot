from enum import Enum
class IrcServerStatus(Enum):
    DISCONNECTED = 1
    CONNECTING = 2
    AUTHENTICATING = 3
    CONNECTED = 4
    
    