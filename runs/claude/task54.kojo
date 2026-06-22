clear(); setSpeed(fast)
val s = 60
val cx = 200
val cy = 200
val angles = Array(0, 60, 120, 180, 240, 300)
repeatFor(0 to 5) { i =>
  val a = angles(i)
  val rad = a * math.Pi / 180
  val hx = (cx + 2 * s * math.cos(rad)).toInt
  val hy = (cy + 2 * s * math.sin(rad)).toInt
  penUp(); setPosition(hx, hy); penDown(); setHeading(0)
  repeat(6) { forward(s); left(60) }
}
