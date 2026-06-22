cleari()

def shape = Picture {
    val circles_radi = Array(100, 60, 20)
    
    
    setHeading(0)
    
    repeatFor(0 until 3) { i =>
      left(360, circles_radi(2 - i))
      penUp()
      right(90)
      forward(40)
      left(90)
      penDown()
    }
}

drawCentered(shape)
