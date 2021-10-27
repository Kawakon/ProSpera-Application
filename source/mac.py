import re

class MacAddress:
    """
        Object representation of device MAC address. 
    """
    def __init__(self, mac) -> None:
        self.mac = mac
    def getMAC(self) -> str:
        return self.mac
    def validMac(self):
        return isinstance(self.mac, str) and re.match("[0-9a-f]{2}([:]?)[0-9a-f]{2}(\\1[0-9a-f]{2}){4}$", self.mac.lower())    
