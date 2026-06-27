cleari()

def shape = Picture {
    val r = 100
    penUp(); setPosition(0, -r); setHeading(0); penDown()
    left(360, r)
    penUp(); setPosition(-r, 0); penDown()
    setHeading(0); forward(2 * r)
    penUp(); setPosition(0, -r); penDown()
    setHeading(90); forward(2 * r)
}

drawCentered(shape)
