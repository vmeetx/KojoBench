clear(); setSpeed(fast)
val bigR = 150
val smallR = 40
val cx = 150
val cy = 150
penUp(); setPosition(cx - bigR, cy); penDown(); setHeading(90); right(360, bigR)
penUp(); setPosition(cx - smallR, cy + bigR / 2); penDown(); setHeading(90); right(360, smallR)
penUp(); setPosition(cx - smallR, cy - bigR / 2); penDown(); setHeading(90); right(360, smallR)
penUp(); setPosition(cx + bigR / 2 - smallR, cy); penDown(); setHeading(90); right(360, smallR)
penUp(); setPosition(cx - bigR / 2 - smallR, cy); penDown(); setHeading(90); right(360, smallR)
