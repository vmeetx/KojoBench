clear()
setSpeed(fast)

val side = 200
val r = 40
setHeading(0)
repeat(4) {
  forward((side - r) / 2)
  right(90)
  right(180, r)
  right(90)
  forward((side - r) / 2)
  left(90)
}
