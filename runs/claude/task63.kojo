clear(); setSpeed(fast)
val s = 80
val r = s / 2
right(90)
repeat(6) { forward(s); left(60) }
penUp(); setPosition(0, 0); penDown(); setHeading(270); left(180, r)
penUp(); setPosition(s, 0); penDown(); setHeading(270); left(180, r)
penUp(); setPosition(3 * s / 2, 87); penDown(); setHeading(330); left(180, r)
penUp(); setPosition(s, 173); penDown(); setHeading(90); left(180, r)
penUp(); setPosition(0, 173); penDown(); setHeading(90); left(180, r)
penUp(); setPosition(-s / 2, 87); penDown(); setHeading(210); left(180, r)
