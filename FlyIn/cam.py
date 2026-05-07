class Cam:
    def __init__(
            self,
            x: int = 0,
            y: int = 0,
            zoom: float = 1
    ) -> None:
        """Initialize a cam object"""
        self.x = x
        self.y = y
        self.zoom = zoom