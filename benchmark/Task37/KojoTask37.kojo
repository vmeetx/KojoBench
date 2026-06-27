cleari()

def shape = Picture {
    val w = 150
    val h = 100
    val r = 20
    setHeading(0)
    forward(w - 2 * r); right(90, r)
    forward(h - 2 * r); right(90, r)
    forward(w - 2 * r); right(90, r)
    forward(h - 2 * r); right(90, r)
}

drawCentered(shape)
