cleari()

def shape = Picture {
    val bW = 200
    val bH = 50
    val sW = 60
    val sH = 150
    val o = (bW - sW) / 2

    lineTo(sW, 0)
    lineTo(sW, sH)
    lineTo(sW + o, sH)
    lineTo(sW + o, sH + bH)
    lineTo(-o, sH + bH)
    lineTo(-o, sH)
    lineTo(0, sH)
    lineTo(0, 0)
}

drawCentered(shape)
