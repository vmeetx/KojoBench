cleari()

def shape = Picture {
    // Example code that draws a triangle pointing up.
    repeat(3) {
      forward(80)
      left(120)
    }
}

drawCentered(shape)
