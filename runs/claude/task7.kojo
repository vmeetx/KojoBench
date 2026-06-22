clear()
setSpeed(fast)

val side = 150

// square CW from (0,0) heading North
repeat(4) {
  forward(side)
  right(90)
}

// triangle on right edge: start (150,0) heading North
// right(120) turns make apex point East at (280,75)
penUp()
setPosition(side, 0)
penDown()
setHeading(90)
repeat(3) {
  forward(side)
  right(120)
}
