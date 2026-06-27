cleari()

def shape = Picture {
    val side = 200
    val r = side / 4
    setHeading(0)
    repeat(4) {
        forward(side / 2 - r)
        left(90)
        left(180, r)
        right(90)
        forward(side / 2 - r)
        right(90)
    }
}

drawCentered(shape)
