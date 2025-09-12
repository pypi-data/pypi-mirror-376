import math

def circle_area(radius: float) -> float:
    """
    Calculates area of a circle

    takes only 1 parameter: radius
    """
    return radius**2 * math.pi

def circle_perimeter(radius: float) -> float:
    """
    Calculates perimeter of a circle

    takes only 1 parameter: radius
    """
    return 2*math.pi*radius

def circle_radius(area: float) -> float:
    """
    Calculates radius of a circle

    takes only 1 parameter: area
    """
    return math.sqrt(area/math.pi)

def rectangle_area(base: float, height:float = None) -> float:
    """
    Calculates area of a rectangle or square

    takes 1 or 2 parameters: base, height(optional)
    """
    if height == None:
        return base * base
    else: 
        return base * height
    
def rectangle_perimeter(base: float, height:float = None) -> float:
    """
    Calculates perimeter of a rectangle or square

    takes 1 or 2 parameters: base, height(optional)
    """
    if height == None:
        return base * 4
    else:
        return base * 2 + height * 2

def rectangle_diagonal(base: float, height:float = None) -> float:
    """
    Calculates diagonal of a rectangle or square

    takes 1 or 2 parameters: base, height(optional)
    """
    if height == None:
        return base * math.sqrt(2)
    else:
        return math.sqrt(base**2 + height**2)
    
def triangle_area(base: float, height: float) ->float:
    """
    Calculates area of a triangle

    takes 2 parameters: base, height
    """
    return base * height / 2

def triangle_perimeter(s1:float, s2:float, s3:float) ->float:
    """
    Calculates perimeter of a triangle

    takes 3 parameters: side1, side2, side3
    """
    return s1+s2+s3

def triangle_height(base:float, area:float) ->float:
    """
    Calculates height of a triangle

    takes 2 parameters: base, area
    """
    return 2*area/base 

def polygon_perimeter(sides: list[float]) -> float:
    """
    Calculates perimeter of a polygon

    takes n parameter: side1, side2, ...sideN
    """
    return sum(sides)

def distance_2d(x1:float, y1:float, x2:float, y2:float) -> float:
    """
    Calculates distance between two 2d points 

    takes 4 parameter: x1, y1, x2, y2

    returns 2 values in order: x, y
    """
    x = abs(x1 - x2)
    y = abs(y1 - y2)
    return x, y

def distance_3d(x1:float, y1:float, z1:float, x2:float, y2:float, z2:float) -> float:
    """
    Calculates distance between two 3d points

    takes 6 parameter: x1, y1, z1, x2, y2, z2

    returns 3 values in order: x, y, z
    """
    x = abs(x1 - x2)
    y = abs(y1 - y2)
    z = abs(z1 - z2)
    return x, y, z
