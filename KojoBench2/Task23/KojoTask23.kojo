cleari()

def shape = Picture {
    val step = 60
    setHeading(0)
    repeat(3) {
        forward(step)
        left(90)
        forward(step)
        right(90)
    }
    right(90)
    forward(3 * step)
    right(90)
    forward(3 * step)
}

drawCentered(shape)
