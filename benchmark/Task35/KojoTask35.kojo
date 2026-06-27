cleari()

def shape = Picture {
    val side = 200
    val r = side / 2
    setHeading(0)
    repeat(3) { forward(side); left(120) }
    penUp()
    setPosition(0, 0)
    setHeading(270)
    penDown()
    left(180, r)
}

drawCentered(shape)
