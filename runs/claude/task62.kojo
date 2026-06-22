clear(); setSpeed(fast)
val r = 80
val cx1 = 60
val cx2 = 140
val cy = 100
penUp(); setPosition(cx1 - r, cy); penDown(); setHeading(90); right(360, r)
penUp(); setPosition(cx2 - r, cy); penDown(); setHeading(90); right(360, r)
penUp(); setPosition(cx1 - r, cy - r); penDown()
lineTo(cx2 + r, cy - r)
lineTo(cx2 + r, cy + r)
lineTo(cx1 - r, cy + r)
lineTo(cx1 - r, cy - r)
