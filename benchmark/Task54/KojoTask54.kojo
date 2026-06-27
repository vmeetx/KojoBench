cleari()

def shape = Picture {
    val side = 50
    val ringRadius = 110
    repeatFor(0 until 6) { i =>
        val angle = i * 60.0
        val cx = ringRadius * math.cos(angle.toRadians)
        val cy = ringRadius * math.sin(angle.toRadians)
        penUp()
        setPosition(cx, cy)
        setHeading(0)
        penDown()
        repeat(6) { forward(side); right(60) }
    }
}

drawCentered(shape)
