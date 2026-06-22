clear(); setSpeed(fast)
val outer = 160
val inner = 113
repeat(4) { forward(outer); right(90) }
penUp()
setPosition(outer / 2, 0)
penDown()
setHeading(135)
repeat(4) { forward(inner); right(90) }
