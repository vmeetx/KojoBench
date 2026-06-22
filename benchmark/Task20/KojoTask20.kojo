cleari()

def shape = Picture {
    setHeading(0)
    repeat(4) {
        forward(200)
        right(90)
    }
    penUp()
    setPosition(40, -40)
    setHeading(0)
    penDown()
    repeat(4) {
        forward(120)
        right(90)
    }
}

drawCentered(shape)
