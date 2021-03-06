# ps0.py
# by Alexander Breen
# A perfect solution to a problem set from an introductory CS course.

PI = 3.14

def hello():
    print("Hello, world!")


def meet():
    name = input("What's your name? ")
    print("Nice to meet you, " + name + "!")


def greetings(name):
    print("Greetings, " + name + "!")


def my_add(a, b):
    return a + b


def my_mult(a, b):
    return a * b


def double(x):
    return x * 2


def series_sum(x):
    if x <= 0:
        return 0

    return x + series_sum(x - 1)
