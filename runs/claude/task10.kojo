clear()
setSpeed(fast)

val side = 200
val r    = side / 2

// square CW from (0,0) heading North
repeat(4) {
  forward(side)
  right(90)
}

// inscribed circle: turtle at left midpoint (0,r) heading North
// right(360,r) puts center at (r,r) = (100,100) = square center
penUp()
setPosition(0, r)
penDown()
right(360, r)
