clear(); setSpeed(fast)
val s = 80
right(90)
repeat(6) { forward(s); left(60) }
val cx = s
val cy = s
val bigR = 30
val smallR = 15
penUp(); setPosition(cx - bigR, cy); penDown(); setHeading(90); right(360, bigR)
penUp(); setPosition(cx + s - smallR, cy); penDown(); setHeading(90); right(360, smallR)
penUp(); setPosition(cx - bigR + s / 2, cy + 87); penDown(); setHeading(90); right(360, bigR)
penUp(); setPosition(cx - smallR - s / 2, cy + 87); penDown(); setHeading(90); right(360, smallR)
penUp(); setPosition(cx - bigR, cy + 2 * 87); penDown(); setHeading(90); right(360, bigR)
penUp(); setPosition(cx + s - smallR, cy + 2 * 87); penDown(); setHeading(90); right(360, smallR)
