cleari()

def shape = Picture {
    val r = 100
    setPosition(0, 0)
    setHeading(-45)
    forward(r)
    setHeading(225)
    right(270, r)
    setHeading(225)
    forward(r)
}

drawCentered(shape)
