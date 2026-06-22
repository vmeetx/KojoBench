clear(); setSpeed(fast)
val s = 100
repeat(2) {
  repeat(4) { forward(s); right(90) }
  penUp(); setPosition(s, 0); penDown(); setHeading(90)
  repeat(4) { forward(s); right(90) }
  penUp(); setPosition(0, s); penDown(); setHeading(90)
}
penUp(); setPosition(0, 0); penDown(); setHeading(90)
repeat(4) { forward(s); right(90) }
penUp(); setPosition(s, 0); penDown(); setHeading(90)
repeat(4) { forward(s); right(90) }
penUp(); setPosition(0, s); penDown(); setHeading(90)
repeat(4) { forward(s); right(90) }
penUp(); setPosition(s, s); penDown(); setHeading(90)
repeat(4) { forward(s); right(90) }
