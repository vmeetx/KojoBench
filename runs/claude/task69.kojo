clear()
setSpeed(fast)

val r = 100
setHeading(0)
repeat(4) {
  forward(2 * r)
  left(90)
  right(180, r)
  left(90)
  forward(2 * r)
  right(90)
}
