cleari()

def shape = Picture {
    val large = 150.0
    val small = 75.0
    setHeading(0)
    repeat(3) { forward(large); right(120) }
    penUp()
    setPosition(large + 20, 0)
    setHeading(0)
    penDown()
    repeat(3) { forward(small); right(120) }
    penUp()
    setPosition(large * 2 + 40, 0)
    setHeading(0)
    penDown()
    repeat(3) { forward(large); right(120) }
}

drawCentered(shape)
