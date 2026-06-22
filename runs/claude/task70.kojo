clear(); setSpeed(fast)
val s = 80
repeatFor(0 to 2) { row =>
  repeatFor(0 to 2) { col =>
    penUp()
    setPosition(col * s, row * s)
    penDown()
    setHeading(0)
    repeat(3) { forward(s); left(120) }
  }
}
