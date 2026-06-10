import turtle

square_side = 200

t = turtle.Turtle()
t.speed(0)
t.hideturtle()
screen = turtle.Screen()
screen.bgcolor("white")

t.setheading(0)
for i in range(4):
  t.forward(square_side)
  t.right(90)
turtle.done()
