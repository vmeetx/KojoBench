clear()
setSpeed(fast)

val r = 50
setHeading(0)
repeat(4) {
  left(180, r)
  right(90)
}
left(90)
repeat(4) {
  forward(2 * r)
  left(90)
}
