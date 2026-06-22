clear(); setSpeed(fast)
val s = 80
right(90)
repeat(6) { forward(s); left(60) }
penUp(); setPosition(s + 10, 0); penDown(); setHeading(0)
repeat(6) { forward(s); left(60) }
penUp(); setPosition(s / 2 + 5, s + 10); penDown(); setHeading(0)
repeat(6) { forward(s); left(60) }
