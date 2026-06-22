clear(); setSpeed(fast)
val s = 100
right(90)
repeat(3) { forward(s); left(120) }
penUp(); setPosition(s + 20, 0); penDown(); setHeading(0)
repeat(3) { forward(s); left(120) }
penUp(); setPosition(2 * s + 40, 0); penDown(); setHeading(0)
repeat(3) { forward(s); left(120) }
