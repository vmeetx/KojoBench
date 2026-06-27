cleari()

def shape = Picture {
    val side = 200
    val r = side * math.sqrt(2) / 2
    setHeading(0)
    repeat(4) { forward(side); right(90) }
    penUp()
    setPosition(100 + r, -100)
    setHeading(90)
    penDown()
    left(360, r)
}

drawCentered(shape)
