cleari()

def shape = Picture {
    val r = 150

    setHeading(90)
    forward(r)
    right(90)
    right(90, r)
    right(90)
    forward(r)
}

drawCentered(shape)
