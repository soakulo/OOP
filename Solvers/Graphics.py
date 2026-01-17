import tkinter as tk

class Graphic:
    def __init__(self, color='black'):
        self.color = color
    
    def draw(self, canvas):
        pass

class Point(Graphic):
    def __init__(self, x, y, color='black'):
        super().__init__(color)
        self.x = x
        self.y = y
    
    def draw(self, canvas):
        canvas.create_oval(self.x - 2, self.y - 2, self.x + 2, self.y + 2, fill=self.color)

class Line(Graphic):
    def __init__(self, x1, y1, x2, y2, color='black'):
        super().__init__(color)
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2
    
    def draw(self, canvas):
        canvas.create_line(self.x1, self.y1, self.x2, self.y2, fill=self.color)

root = tk.Tk()

canvas = tk.Canvas(root, width=400, height=400, bg='white')
canvas.pack()

figures = [
    Point(50, 50, 'red'),
    Point(100, 100, 'blue'),
    Line(50, 50, 150, 150, 'green'),
]

for figure in figures:
    figure.draw(canvas)

root.mainloop()