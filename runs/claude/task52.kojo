clear()
setSpeed(fast)

val side = 200.0
val s = side / math.sqrt(2)
setHeading(0)
repeat(8) {
  forward(s)
  right(45)
  forward(s)
  right(90)
}
