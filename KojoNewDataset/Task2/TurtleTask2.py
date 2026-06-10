import turtle

triangle_side = 200

t = turtle.Turtle()
t.speed(0)
t.hideturtle()
screen = turtle.Screen()
screen.bgcolor("white")

t.setheading(60)
for i in range(3):
  t.forward(triangle_side)
  t.right(120)
turtle.done()
