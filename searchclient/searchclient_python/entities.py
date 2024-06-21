class Agent:
    def __init__(self, type, color, row, col):
        self.type = type
        self.color = color
        self.row = row
        self.col = col

    def __eq__(self, other):
        if not isinstance(other, Agent):
            return False
        return (self.type, self.color, self.row, self.col) == (other.type, other.color, other.row, other.col)

class Box:
    def __init__(self, id, color, row, col, type):
        self.id = id
        self.color = color
        self.row = row
        self.col = col
        self.type = type

    def __eq__(self, other):
        if not isinstance(other, Box):
            return False
        return (self.color, self.row, self.col, self.type) == (other.color, other.row, other.col, other.type)

class Goal:
    def __init__(self, id, type, row, col):
        self.id = id
        self.type = type
        self.row = row
        self.col = col

    def __eq__(self, other):
        if not isinstance(other, Goal):
            return False
        return (self.type, self.row, self.col) == (other.type, other.row, other.col)
