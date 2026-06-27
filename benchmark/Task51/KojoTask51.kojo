cleari()

def shape = Picture {
    val rLarge = 50
    val rSmall = 25
    val dist = 110
    repeatFor(0 until 6) { i =>
        val angle = i * 60.0
        val cx = dist * math.cos(angle.toRadians)
        val cy = dist * math.sin(angle.toRadians)
        val r = if (i % 2 == 0) rLarge else rSmall
        penUp()
        setPosition(cx, cy - r)
        setHeading(0)
        penDown()
        left(360, r)
    }
}

drawCentered(shape)
