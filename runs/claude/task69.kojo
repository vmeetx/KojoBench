clear(); setSpeed(fast)
val s = 120
val r = s / 2
repeat(4) { forward(s); right(90) }
penUp(); setPosition(0, r); penDown(); setHeading(180); right(180, r)
penUp(); setPosition(r, 0); penDown(); setHeading(270); right(180, r)
penUp(); setPosition(s, r); penDown(); setHeading(0); right(180, r)
penUp(); setPosition(r, s); penDown(); setHeading(90); right(180, r)
