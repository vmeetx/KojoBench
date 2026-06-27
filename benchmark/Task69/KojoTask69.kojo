cleari()

def shape = Picture {
    val r = 100.0
    penUp(); setPosition(0, 0); setHeading(90); penDown()
    right(180, r)
    penUp(); setPosition(200, 0); setHeading(0); penDown()
    right(180, r)
    penUp(); setPosition(200, -200); setHeading(270); penDown()
    right(180, r)
    penUp(); setPosition(0, -200); setHeading(180); penDown()
    right(180, r)
}

drawCentered(shape)
