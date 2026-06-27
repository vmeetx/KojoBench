cleari()

def shape = Picture {
    val R = 100.0
    val r = 30.0
    penUp(); setPosition(0, -R); setHeading(0); penDown()
    left(360, R)
    val offsets = Array((R/2, R/2), (-R/2, R/2), (-R/2, -R/2), (R/2, -R/2))
    for (c <- offsets) {
        penUp(); setPosition(c._1, c._2 - r); setHeading(0); penDown()
        left(360, r)
    }
}

drawCentered(shape)
