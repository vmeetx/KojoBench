clear(); setSpeed(fast)
val big = 150
val small = 75
right(90)
repeat(3) { forward(big); left(120) }
penUp(); setPosition(big + 20, 0); penDown(); setHeading(0)
repeat(3) { forward(small); left(120) }
penUp(); setPosition(big + small + 40, 0); penDown(); setHeading(0)
repeat(3) { forward(big); left(120) }
