import turtle

triangle_side = 200

t = turtle.Turtle()
t.speed(0)
t.hideturtle()
screen = turtle.Screen()
screen.bgcolor("white")

def draw_polygon(sides, length):
  outer_turn = 360 / sides 
  for _ in range(sides):
    t.forward(length)
    t.right(outer_turn)

t.setheading(60)
for i in range(2):
  draw_polygon(3, triangle_side)
  t.left(120)
turtle.done()
