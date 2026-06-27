cleari()

def shape = Picture {
    val large = 200
    val small = 100
    setHeading(0)
    repeat(4) { forward(large); right(90) }
    penUp(); setPosition(0, 0); penDown()
    repeat(4) { forward(small); right(90) }
    penUp(); setPosition(small, 0); penDown()
    repeat(4) { forward(small); right(90) }
    penUp(); setPosition(0, -small); penDown()
    repeat(4) { forward(small); right(90) }
    penUp(); setPosition(small, -small); penDown()
    repeat(4) { forward(small); right(90) }
}

drawCentered(shape)
