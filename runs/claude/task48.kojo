clear(); setSpeed(fast)
val sizes = Array(40, 80, 120, 160)
repeatFor(0 to 3) { i =>
  val s = sizes(i)
  penUp(); setPosition(0, 0); penDown(); setHeading(90)
  repeat(4) { forward(s); right(90) }
}
