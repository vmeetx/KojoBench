clear()
setSpeed(fast)

val r = 60

right(90)

// bottom arc: CCW, bulges left (West) — bottom of S
left(180, r)

// top arc: CW, bulges right (East) — top of S
right(180, r)

// vertical center line
penUp()
setPosition(0, 0)
penDown()
setHeading(90)
forward(r * 4)
