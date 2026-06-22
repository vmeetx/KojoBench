clear(); setSpeed(fast)
val s = 120
val r = 25
repeat(4) { forward(s); right(90) }
penUp(); setPosition(0, r); penDown(); setHeading(0); right(360, r)
penUp(); setPosition(0, s + r); penDown(); setHeading(0); right(360, r)
penUp(); setPosition(s, r); penDown(); setHeading(0); right(360, r)
penUp(); setPosition(s, s + r); penDown(); setHeading(0); right(360, r)
