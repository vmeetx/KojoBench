cleari()

def shape = Picture {
    val r1 = 60.0
    val r2 = 100.0
    penUp(); setPosition(0, -r1); setHeading(0); penDown()
    left(360, r1)
    penUp(); setPosition(0, -r2); setHeading(0); penDown()
    left(360, r2)
}

drawCentered(shape)
