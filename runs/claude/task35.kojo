clear(); setSpeed(fast)
val r = 100
val h = 173
penUp(); setPosition(r, 0); penDown()
setHeading(60)
forward(2 * r)
setHeading(180)
forward(2 * r)
lineTo(r, 0)
penUp(); setPosition(0, h); penDown()
setHeading(270)
left(180, r)
