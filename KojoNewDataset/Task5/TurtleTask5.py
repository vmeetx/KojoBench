import turtle

small_triangle_side = 50
large_triangle_side = 100

t = turtle.Turtle()
t.speed(0)
t.hideturtle()
screen = turtle.Screen()
screen.bgcolor("white")

def draw_polygon(sides, length):
  t.left(60)
  outer_turn = 360 / sides 
  for _ in range(sides):
    t.forward(length)
    t.right(outer_turn)
  t.right(60)
t.right(60)
for i in range(3):
  draw_polygon(3, small_triangle_side)
  t.right(120)
  t.forward(large_triangle_side)
turtle.done()
