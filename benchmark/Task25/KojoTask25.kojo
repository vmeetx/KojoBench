cleari()

def shape = Picture {
    def tri() {
        repeat(3) {
            forward(80)
            left(120)
        }
    }
    setHeading(0)
    tri()
    penUp()
    forward(80)
    penDown()
    tri()
    penUp()
    forward(80)
    penDown()
    tri()
}

drawCentered(shape)
