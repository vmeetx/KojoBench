cleari()

def shape = Picture {
    val radius = 90
    val rectangle_length = 300
    
    
    setHeading(0)
    
    forward(radius)
    left(360, radius)
    forward((rectangle_length - 2 * radius))
    left(360, radius)
    forward(radius)
    left(90)
    forward(2 * radius)
    left(90)
    forward(rectangle_length)
    left(90)
    forward(2 * radius)
}

drawCentered(shape)
