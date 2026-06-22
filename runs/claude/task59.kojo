clear(); setSpeed(fast)
val big = 200
val small = 80
repeat(4) { forward(big); right(90) }
val off = (big - small) / 2
penUp(); setPosition(off, off); penDown(); setHeading(90)
repeat(4) { forward(small); right(90) }
