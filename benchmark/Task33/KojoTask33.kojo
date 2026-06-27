cleari()

def shape = Picture {
    val side = 100
    setHeading(0)
    repeat(4) { forward(side); right(90) }
    penUp()
    forward(50)
    right(90)
    forward(50)
    left(90)
    penDown()
    repeat(4) { forward(side); right(90) }
}

drawCentered(shape)
