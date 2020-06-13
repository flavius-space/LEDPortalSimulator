from math import atan, cos, sin


def gradient_sin(gradient):
    """
    get the length of the opposite side of a right unit triangle, angle=θ

       /|
    1 / |
     /  | <- sin θ
    /θ__| <- θ, 90
    |<->| <- cos θ

    gradient = rise / run = tan(theta)
    => theta = atan(gradient)
    sin(theta) = rise / 1
    => rise = sin(atan(gradient))
    """
    return sin(atan(gradient))


def gradient_cos(gradient):
    """
    get the length of the adjacent side of a right unit triangle, angle=θ
       /|
    1 / |
     /  | <- sin θ
    /θ__| <- θ, 90
    |<->| <- cos θ

    gradient = rise / run = tan(theta)
    => theta = atan(gradient)
    cos(theta) = run / 1
    => rise = cos(atan(gradient))
    """
    return cos(atan(gradient))
