import turtle

triangle_side = 100

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

t.setheading(-30)
draw_polygon(3, triangle_side)
t.right(60)
draw_polygon(4, triangle_side)
turtle.done()
