import turtle

semicircle_radius = 70

t = turtle.Turtle()
t.speed(0)
t.hideturtle()
screen = turtle.Screen()
screen.bgcolor("white")

t.circle(semicircle_radius, -180)
t.right(180)
t.circle(semicircle_radius, 180)
t.left(90)
t.forward(4 * semicircle_radius)
turtle.done()
