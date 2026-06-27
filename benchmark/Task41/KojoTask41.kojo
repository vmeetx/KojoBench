cleari()

def shape = Picture {
    val r = 50
    val side = 100
    setHeading(270)
    left(180, r)
    penUp(); hop(r * 3); penDown()
    setHeading(270)
    left(180, r)
    penUp(); hop(r * 3); penDown()
    setHeading(0)
    repeat(3) { forward(side); left(120) }
}

drawCentered(shape)
