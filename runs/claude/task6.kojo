clear()
setSpeed(fast)

val side = 200

// right mountain: (0,0) -> (200,0) -> (100,173) -> (0,0)
right(90)
repeat(3) {
  forward(side)
  left(120)
}

// left mountain: (-200,0) -> (0,0) -> (-100,173) -> (-200,0)
penUp()
setPosition(-200, 0)
penDown()
setHeading(0)
repeat(3) {
  forward(side)
  left(120)
}
