class Vector:
    def __init__(self, *args):
        self.data = list(args)

    def __add__(self, other):
        return Vector(*[a+b for a,b in zip(self.data, other.data)])

    def __sub__(self, other):
        return Vector(*[a-b for a,b in zip(self.data, other.data)])

    def __mul__(self, k: float):
        return Vector(*[a*k for a in self.data])

    def __repr__(self):
        return f"Vector({self.data})"

def vec(*args): 
    return Vector(*args)
