cleari()

def shape = Picture {
    val sizes = Array(40.0, 80.0, 120.0, 160.0, 200.0)
    repeatFor(0 until 5) { i =>
        val s = sizes(i)
        val cr = s / (2 * math.sin(math.Pi / 5))
        penUp()
        setPosition(0, -cr)
        setHeading(0)
        penDown()
        repeat(5) { forward(s); left(72) }
    }
}

drawCentered(shape)
