clear(); setSpeed(fast)
val sizes = Array(50, 80, 110, 140)
var x = 0
repeatFor(0 to 3) { i =>
  val s = sizes(i)
  penUp(); setPosition(x, 0); penDown(); setHeading(0)
  repeat(3) { forward(s); left(120) }
  x = x + s + 20
}
