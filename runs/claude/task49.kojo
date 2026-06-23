clear()
setSpeed(fast)

val r = 80
setHeading(0)
repeat(4) {
  left(360, r)
  right(90)
}
left(180, r)
left(360, 2 * r)
