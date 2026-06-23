clear()
setSpeed(fast)

val arm = 80
setHeading(0)
repeat(4) {
  forward(arm)
  left(90)
  forward(arm)
  right(90)
  forward(arm)
  right(90)
}
