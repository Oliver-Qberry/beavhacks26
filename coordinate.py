# A coordinate object that holds an x and y value
class Coordinate:
    x: int
    y: int

    def __init__(self,x,y):
        self.x = x
        self.y = y

    def print(self) -> None:
        print(f"({self.x}, {self.y})")