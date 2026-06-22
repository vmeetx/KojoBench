clear(); setSpeed(fast)
val r = 70
right(90)
repeat(3) { forward(2 * r); left(120) }
penUp(); setPosition(0, 0); penDown()
setHeading(270)
left(180, r)
penUp(); setPosition(0, 2 * r + 20); penDown()
setHeading(270)
left(180, r)
