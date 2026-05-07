class Drone:
    """represents a Drone that can use connections to move between hubs"""
    
    def __init__(
        self,
        id: str,
        pos: str,
    ) -> None:
        """initialize drone instance"""
        self.id = id
        self.pos = pos