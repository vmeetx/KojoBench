cleari()

def shape = Picture {
    val side = 70.0
    val spacing = side * math.sqrt(3) + 10
    val positions = Array(
        (0.0, 0.0),
        (spacing, 0.0),
        (spacing / 2, spacing * math.sqrt(3) / 2)
    )
    for (pos <- positions) {
        penUp()
        setPosition(pos._1, pos._2)
        setHeading(0)
        penDown()
        repeat(6) { forward(side); right(60) }
    }
}

drawCentered(shape)
