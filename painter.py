import abc
from abc import abstractmethod, ABC
import pygame, math
pygame.init()

def rect(x1, y1, x2, y2):
    w, h = abs(x2 - x1), abs(y2 - y1)
    x, y = min(x1, x2), min(y1, y2)
    return x, y, w, h

class Shape(ABC):
    def __init__(self, x, y, w, h, colour, outline_colour):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.colour = colour
        self.outline_colour = outline_colour
    
    def normalize(self):
        if self.w < 0:
            self.x += self.w
            self.w = -self.w
        if self.h < 0:
            self.y += self.h
            self.h = -self.h
    
    def get_rect(self) -> pygame.Rect:
        x, y, w, h = self.x, self.y, self.w, self.h
        if w < 0:
            x += w
            w = -w
        if h < 0:
            y += h
            h = -h
        return pygame.Rect(x, y, w, h)
    
    def move(self, dx, dy):
        self.x += dx
        self.y += dy
    
    def resize(self, dx, dy):
        self.w += dx
        self.h += dy
    
    @abstractmethod
    def draw(self, canvas):
        pass

    def draw_focus(self, canvas):
        pass

class Rect(Shape):
    def draw(self, canvas):
        canvas.draw_rect(self.get_rect(), self.colour)
        canvas.draw_rect(self.get_rect(), self.outline_colour, 2)
    
    def draw_focus(self, canvas):
        canvas.draw_rect(self.get_rect(), (255, 128, 0), 2)

class Ellipse(Shape):
    def draw(self, canvas):
        canvas.draw_ellipse(self.x, self.y, self.w, self.h, self.colour)
        canvas.draw_ellipse(self.get_rect(), self.outline_colour, 2)
    
    def draw_focus(self, canvas):
        canvas.draw_ellipse(self.x, self.y, self.w, self.h, (255, 128, 0), 2)

class Tool:
    def draw_icon(self, canvas, x, y, w, h):
        raise "draw_icon not implemented"

    def draw(self, canvas):
        pass

    def handle_input(self, canvas, event):
        pass

class SelectTool(Tool):
    shape: Shape
    dragging: bool
    def __init__(self):
        self.pointer = pygame.transform.scale(pygame.image.load("assets/mouse_pointer.png"), (80, 80))
        self.dragging = False
        self.drag_handle = None
        self.shape = None
    
    def get_handles(self):
        rect = self.shape.get_rect()
        x, y, w, h = rect.x, rect.y, rect.w, rect.h
        handles = [
            (x-5, y-5, 10, 10),
            (x-5, y+h-5, 10, 10),
            (x+w-5, y-5, 10, 10),
            (x+w-5, y+h-5, 10, 10),
        ]
        return handles

    def get_handle(self, x, y):
        handles = self.get_handles()
        for i in range(len(handles)):
            handle = handles[i]
            if pygame.Rect(*handle).collidepoint(x, y):
                return i
    
    def resize(self, handle, dx, dy):
        print(dx, dy)
        if handle == 0:
            self.shape.move(dx, dy)
            self.shape.resize(-dx, -dy)
        elif handle == 1:
            self.shape.move(dx, 0)
            self.shape.resize(-dx, dy)
        elif handle == 2:
            self.shape.move(0, dy)
            self.shape.resize(dx, -dy)
        elif handle == 3:
            self.shape.resize(dx, dy)

    def change_colour(self, colour):
        self.shape.colour = colour

    def draw_handles(self, canvas):
        for x, y, w, h in self.get_handles():
            canvas.draw_rect((x, y, w, h), (255, 255, 255))
            canvas.draw_rect((x, y, w, h), (0, 0, 0), 1)

    def draw(self, canvas):
        if self.shape:
            self.shape.draw_focus(canvas)
            self.draw_handles(canvas)

    def draw_icon(self, canvas, x, y, w, h):
        canvas.draw_image(x+5, y+5, self.pointer)

    def handle_input(self, canvas, event):
        if self.shape:
            self.change_colour(canvas.colour)
            if event.type == pygame.MOUSEBUTTONDOWN:
                x, y = pygame.mouse.get_pos()
                handle = self.get_handle(x, y)
                if handle is not None:
                    print("handle:", handle)
                    self.dragging = True
                    self.drag_handle = handle
                    self.x, self.y = x, y
                    return
            elif event.type == pygame.MOUSEMOTION:
                if self.drag_handle is not None:
                    x, y = pygame.mouse.get_pos()
                    dx, dy = x - self.x, y - self.y
                    self.resize(self.drag_handle, dx, dy)
                    self.x, self.y = x, y
                    return
            elif event.type == pygame.MOUSEBUTTONUP:
                if self.drag_handle is not None:
                    self.shape.normalize()
                    self.dragging = False
                    self.drag_handle = None
                    return

        if event.type == pygame.MOUSEBUTTONDOWN:
            self.dragging = True
            x, y = pygame.mouse.get_pos()
            self.dragging, self.shape = canvas.select(x, y)
            self.x, self.y = x, y
        elif event.type == pygame.MOUSEMOTION:
            if not self.dragging or not self.shape:
                return
            x, y = pygame.mouse.get_pos()
            dx, dy = x - self.x, y - self.y
            self.shape.move(dx, dy)
            self.x, self.y = x, y
        elif event.type == pygame.MOUSEBUTTONUP:
            self.dragging = False
        elif event.type == pygame.KEYUP:
            if event.key == pygame.K_DELETE or event.key == pygame.K_BACKSPACE:
                canvas.remove_shape(self.shape)
                self.shape = None



class EllipseTool(Tool):
    def __init__(self):
        self.drawing = False

    def draw_icon(self, canvas, x, y, w, h):
        canvas.draw_ellipse(x+5, y+5, w-10, h-10)
    
    def draw(self, canvas):
        if not self.drawing:
            return
        x, y, w, h = rect(self.x, self.y, self.mx, self.my)
        canvas.draw_ellipse(x, y, w, h, (128, 128, 128))

    def handle_input(self, canvas, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            x, y = pygame.mouse.get_pos()
            self.drawing = True
            self.x = x
            self.y = y
            self.mx = x
            self.my = y
        elif event.type == pygame.MOUSEMOTION:
            if not self.drawing:
                return
            x, y = pygame.mouse.get_pos()
            self.mx, self.my = x, y
        elif event.type == pygame.MOUSEBUTTONUP:
            if not self.drawing:
                return
            self.drawing = False
            x, y = pygame.mouse.get_pos()
            x, y, w, h = rect(x, y, self.x, self.y)
            shape = Ellipse(x, y, w, h, canvas.colour, canvas.outline_colour)
            canvas.add_shape(shape)

class RectTool(Tool):
    def __init__(self):
        self.drawing = False

    def draw_icon(self, canvas, x, y, w, h):
        canvas.draw_rect((x+5, y+5, w-10, h-10))
    
    def draw(self, canvas):
        if not self.drawing:
            return
        x, y, w, h = rect(self.x, self.y, self.mx, self.my)
        canvas.draw_rect((x, y, w, h), (128, 128, 128))
    
    def handle_input(self, canvas, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            x, y = pygame.mouse.get_pos()
            self.drawing = True
            self.x = x
            self.y = y
            self.mx = x
            self.my = y
        elif event.type == pygame.MOUSEMOTION:
            if not self.drawing:
                return
            x, y = pygame.mouse.get_pos()
            self.mx, self.my = x, y
        elif event.type == pygame.MOUSEBUTTONUP:
            if not self.drawing:
                return
            self.drawing = False
            x, y = pygame.mouse.get_pos()
            x, y, w, h = rect(x, y, self.x, self.y)
            shape = Rect(x, y, w, h, canvas.colour, canvas.outline_colour)
            canvas.add_shape(shape)

class ColourBoard():
    def draw_icon(self, canvas, x, y, w, h, colour):
        canvas.draw_rect((x+5, y+5, w-10, h-10), colour)

class PreviewColourBoard():
    def draw_board(self, canvas, x, y, w, h):
        canvas.draw_rect((x+5, y+5, w-10, h-10), canvas.colour)
        canvas.draw_rect((x+5, y+5, w-10, h-10), canvas.outline_colour, 3)

class Canvas:
    shapes: list[Shape]

    def __init__(self):
        self.shapes = []
        self.win = pygame.display.set_mode((800, 600))
        self.clock = pygame.time.Clock()
        self.running = False
        self.fps = 60
        self.tools = [
            SelectTool(),
            RectTool(),
            EllipseTool()
        ]
        self.board = PreviewColourBoard()
        self.colours = [
            (0, 0, 0), 
            (255, 0, 0), 
            (255, 125, 0), 
            (255, 255, 0), 
            (0, 255, 0), 
            (0, 255, 255), 
            (0, 0, 255),  
            (255, 0, 255), 
            (255, 255, 255)
        ]
        self.tool = self.tools[0]
        self.colour = self.colours[0]
        self.outline_colour = self.colours[0]
    
    def handle_tool_switch(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            for tool, x, y, w, h in self.each_tool():
                mousex, mousey = pygame.mouse.get_pos()
                if pygame.Rect(x, y, w, h).collidepoint(mousex, mousey):
                    self.tool = tool
                    return True
        return False
    
    def handle_colour_switch(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            for colour, x, y, w, h in self.each_colour():
                mousex, mousey = pygame.mouse.get_pos()
                if pygame.Rect(x, y, w, h).collidepoint(mousex, mousey):
                    if event.button == pygame.BUTTON_LEFT:
                        self.colour = colour
                    elif event.button == pygame.BUTTON_RIGHT:
                        self.outline_colour = colour
                    return True

    def each_tool(self):
        width = 100
        height = 80
        for i in range(len(self.tools)):
            tool = self.tools[i]
            x, y = 20, 20 + height * i
            yield tool, x, y, width, height

    def each_colour(self):
        width = 70
        height = 60
        for i in range(len(self.colours)):
            colour = self.colours[i]
            x, y = 710, 20 + height * i
            yield colour, x, y, width, height
    
    def select(self, x, y):
        for shape in reversed(self.shapes):
            if shape.get_rect().collidepoint(x, y):
                return True, shape
        return False, None
    
    def remove_shape(self, shape):
        self.shapes.remove(shape)

    def add_shape(self, shape):
        self.shapes.append(shape)
    
    def draw_image(self, x, y, image):
        self.win.blit(image, (x, y))

    def draw_ellipse(self, x, y, w, h, color = (0, 0, 0), width = 0):
        pygame.draw.ellipse(self.win, color, pygame.Rect(x, y, w, h), width)

    def draw_rect(self, rect, color = (0, 0, 0), width = 0):
        pygame.draw.rect(self.win, color, rect, width)
    
    def draw_tools(self):
        for tool, x, y, w, h in self.each_tool():
            self.draw_rect((x, y, w, h), (192, 192, 192))
            tool.draw_icon(self, x, y, w, h)
            if tool == self.tool:
                self.draw_rect((x, y, w, h), (255, 128, 0), 2)
    
    def draw_colours(self):
        for colour, x, y, w, h in self.each_colour():
            self.draw_rect((x, y, w, h), (192, 192, 192))
            ColourBoard().draw_icon(self, x, y, w, h, colour)
    
    def draw(self):
        self.draw_background()
        for shape in self.shapes:
            shape.draw(self)
        self.tool.draw(self)
        self.draw_tools()
        self.board.draw_board(canvas, 20, 20 + 80 * len(self.tools), 100, 80)
        self.draw_colours()
        pygame.display.update()
    
    def handle_input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                break
            if self.handle_colour_switch(event):
                continue

            if self.handle_tool_switch(event):
                continue
            self.tool.handle_input(self, event)
            
    def run(self):
        self.running = True
        while self.running:
            self.clock.tick(self.fps)
            self.handle_input()
            self.draw()
        pygame.quit()
    
    def draw_background(self):
        self.win.fill((255, 255, 255))

canvas = Canvas()
canvas.run()
