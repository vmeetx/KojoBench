cleari()

def shape = Picture {
    val side = 200
    setHeading(0)
    repeat(5) { forward(side); left(72) }
}

drawCentered(shape)
