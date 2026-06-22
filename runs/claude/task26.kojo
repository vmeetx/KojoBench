clear(); setSpeed(fast)
val s = 100
right(90)
repeat(2) { forward(s); right(90); forward(3 * s); right(90) }
penUp(); setPosition(s, 0); penDown(); setHeading(90); forward(s)
penUp(); setPosition(2 * s, 0); penDown(); setHeading(90); forward(s)
