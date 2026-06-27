cleari()

def shape = Picture {
    val r = 60
    setHeading(270)
    left(180, r)
    penUp(); setPosition(r, 0); penDown()
    setHeading(270)
    left(180, r)
    penUp(); setPosition(2 * r, 0); penDown()
    setHeading(270)
    left(180, r)
}

drawCentered(shape)
