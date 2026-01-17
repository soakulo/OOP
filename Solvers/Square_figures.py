from math import *
class Shape:
    def __init__(self):
        pass

    @property
    def perimeter(self):
        return self.get_perimeter()
    
    def get_perimeter(self):
        raise NotImplementedError
    
    @property
    def area(self):
        return self.get_area()

    def get_area(self):
        raise NotImplementedError


class Circle(Shape):
    def __init__(self, radius : float):
        super().__init__()
        self.raduis =  radius

    def get_perimeter(self):
        return 2* pi * self.raduis
    
    def get_area(self):
        return pi * (self.radius ** 2)
    
class Triangle(Shape):
    def __init__(self, a : float, b: float, c: float):
        super().__init__()

        self.a = a
        self.b = b
        self.c = c

    def get_perimeter(self):
        return self.a + self.b + self.c
    
    def get_area(self):
        p = self.perimeter / 2
        return sqrt(p * (p - self.a) * (p - self.b) * (p - self.c))
    

class Rectangle(Shape):
    def __init__(self, width : float, height : float):
        super().__init__()

        self.width = width
        self.height = height


    def get_perimeter(self):
        return (self.width + self.height) * 2
    

    def get_area(self):
        return self.width * self.height
    
if __name__ == "__main__":
    circle = Circle(2)

    print(circle.perimeter)