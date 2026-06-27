cleari()

def shape = Picture {
    val side = 100
    setHeading(0)
    repeat(3) { forward(side); right(120) }
    penUp(); forward(side + 20); penDown()
    setHeading(0)
    repeat(3) { forward(side); right(120) }
    penUp(); forward(side + 20); penDown()
    setHeading(0)
    repeat(3) { forward(side); right(120) }
}

drawCentered(shape)
