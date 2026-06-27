cleari()

def shape = Picture {
    val side = 200
    val r = side / 4
    setHeading(270)
    left(180, r)
    setHeading(270)
    left(180, r)
    setHeading(120)
    forward(side)
    setHeading(240)
    forward(side)
}

drawCentered(shape)
