clear(); setSpeed(fast)
val s = 80
repeat(4) { forward(s); right(90) }
penUp(); setPosition(s + 20, 0); penDown(); setHeading(90)
repeat(4) { forward(s); right(90) }
penUp(); setPosition(s / 2 + 10, s + 20); penDown(); setHeading(90)
repeat(4) { forward(s); right(90) }
