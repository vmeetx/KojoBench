clear()
setSpeed(fast)

val big = 200
val sm  = 70

// large triangle CCW, flat bottom, apex at (100, 173)
right(90)
repeat(3) {
  forward(big)
  left(120)
}

// spike at V1 (0,0): outward bisector points SW at 210 degrees
penUp()
setPosition(0, 0)
penDown()
setHeading(210)
repeat(3) { forward(sm); left(120) }

// spike at V2 (200,0): outward points SE at 330 degrees
penUp()
setPosition(200, 0)
penDown()
setHeading(330)
repeat(3) { forward(sm); left(120) }

// spike at V3 (100,173): outward points straight up at 90 degrees
penUp()
setPosition(100, 173)
penDown()
setHeading(90)
repeat(3) { forward(sm); left(120) }
