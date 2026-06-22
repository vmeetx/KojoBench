clear(); setSpeed(fast)
val side = 200
val r = side / 4
right(90)
repeat(3) { forward(side); left(120) }
penUp(); setPosition(0, 0); penDown(); setHeading(90)
right(180, r)
penUp(); setPosition(side / 2, 0); penDown(); setHeading(90)
right(180, r)
