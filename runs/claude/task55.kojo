clear(); setSpeed(fast)
val sizes = Array(40, 70, 100, 130, 160)
repeatFor(0 to 4) { i =>
  val s = sizes(i)
  penUp(); setPosition(0, 0); penDown(); setHeading(90)
  repeat(5) { forward(s); right(72) }
}
