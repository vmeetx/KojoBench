cleari()

def shape = Picture {
    setHeading(0)
    repeat(2) {
        forward(200)
        right(90)
        forward(100)
        right(90)
    }
}

drawCentered(shape)
