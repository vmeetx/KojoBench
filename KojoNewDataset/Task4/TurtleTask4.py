import turtle

pentagon_side = 200

t = turtle.Turtle()
t.speed(0)
t.hideturtle()
screen = turtle.Screen()
screen.bgcolor("white")

t.setheading(36)
for i in range(5):
  t.forward(pentagon_side)
  t.right(72)
turtle.done()
