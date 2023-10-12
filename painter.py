# pylint: disable=missing-class-docstring,missing-function-docstring
"""
A simple paint program
"""
from __future__ import annotations
from typing import Any, Generator, Iterator, Sequence
from abc import abstractmethod, ABC
import pygame
# from pygame import gfxdraw

Color = pygame.Color
Rect = pygame.Rect
Vector2 = pygame.Vector2
Coordinate = tuple[int, int]

# pylint: disable=no-member
pygame.init()

MOUSEBUTTONUP = pygame.MOUSEBUTTONUP
MOUSEBUTTONDOWN = pygame.MOUSEBUTTONDOWN
MOUSEMOTION = pygame.MOUSEMOTION
KEYUP = pygame.KEYUP
K_DELETE = pygame.K_DELETE
K_BACKSPACE = pygame.K_BACKSPACE
BUTTON_LEFT = pygame.BUTTON_LEFT
BUTTON_RIGHT = pygame.BUTTON_RIGHT
QUIT = pygame.QUIT
# pylint: enable=no-member

BLACK = pygame.Color(0, 0, 0)
WHITE = pygame.Color(255, 255, 255)
GRAY = pygame.Color(128, 128, 128)


class ICanvas(ABC):
    @abstractmethod
    def draw_image(self, x: float, y: float, image: pygame.Surface):
        pass

    @abstractmethod
    def draw_ellipse(self, rect: Rect, color: Color = BLACK, width: int = 0):
        pass

    @abstractmethod
    def draw_polygon(self, points: list[Vector2], color: Color = BLACK, width: int = 0):
        pass

    @abstractmethod
    def draw_rect(self, rect: Rect, rotation: float = 0, color: Color = BLACK, width: int = 0):
        pass

    @abstractmethod
    def draw_line(self, p1: Vector2, p2: Vector2, color: Color = BLACK, width: int = 1):
        pass

    @abstractmethod
    def select(self, x: float, y: float) -> tuple[bool, 'Shape' | None]:
        pass

    @abstractmethod
    def remove_shape(self, shape: 'Shape'):
        pass

    @abstractmethod
    def add_shape(self, shape: 'Shape'):
        pass


class Handles:
    """
    Hnaldes are the 4 points of a rectangle
    """

    def __init__(self, rect, rotation):
        self.rect = rect
        self.rotation = rotation

    def get_points(self):
        """
        Returns the 4 rotated points of the rectangle
        """
        x, y, w, h = self.rect
        cx, cy = (x + x + w) / 2, (y + y + h) / 2
        center = Vector2(cx, cy)
        points = [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]
        new_points = []
        for point in points:
            p = Vector2(point)
            delta = p - center
            delta = delta.rotate(self.rotation) + center
            new_points.append(delta)
        return new_points


def make_rect(x1: int, y1: int, x2: int, y2: int) -> Rect:
    """
    Returns a rectangle from 2 points
    """
    w, h = abs(x2 - x1), abs(y2 - y1)
    x, y = min(x1, x2), min(y1, y2)
    return Rect(x, y, w, h)


class Shape(Rect):
    colour: Color
    outline_colour: Color

    def __init__(self, x: float, y: float, w: int, h: int, colour: Color = BLACK, outline_colour: Color = BLACK, rotation: float = 0):
        super().__init__(x, y, w, h)
        self.colour = colour
        self.outline_colour = outline_colour
        self.rotation = rotation

    def get_rect(self) -> Rect:
        x, y, w, h = super().x, super().y, super().w, super().h
        if w < 0:
            x += w
            w = -w
        if h < 0:
            y += h
            h = -h
        return Rect(x, y, w, h)

    def get_points(self):
        x, y, w, h = self.get_rect()
        cx, cy = (x + x + w) / 2, (y + y + h) / 2
        center = pygame.Vector2(cx, cy)
        points = [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]
        points = map(lambda pair: pygame.Vector2(pair[0], pair[1]), points)
        return rotate_points(points, center, self.rotation)

    def move(self, dx, dy):
        super().move_ip(dx, dy)

    def resize(self, dx, dy):
        super().update(self.x, self.y, self.w + dx, self.h + dy)

    def rotate(self, handle_point: Vector2):
        self.rotation = 90 - (handle_point - self.center).angle_to((0, 0))

    @abstractmethod
    def draw(self, canvas: ICanvas):
        pass

    def draw_focus(self, canvas: ICanvas):
        pass


def rotate_points(points: Iterator[pygame.Vector2], center: pygame.Vector2, rotation: float):
    new_points = []
    for point in points:
        p = pygame.Vector2(point)
        delta = p - center
        delta = delta.rotate(rotation) + center
        new_points.append(delta)
    return new_points


class Rectangle(Shape):
    def draw(self, canvas):
        points = self.get_points()
        canvas.draw_polygon(points, self.colour)
        canvas.draw_polygon(points, self.outline_colour, 2)

    def draw_focus(self, canvas):
        canvas.draw_rect(self.get_rect(), self.rotation,
                         pygame.Color(255, 128, 0), 2)


class Ellipse(Shape):
    def draw(self, canvas):
        canvas.draw_ellipse(self.get_rect(), self.colour)
        canvas.draw_ellipse(self.get_rect(), self.outline_colour, 2)

    def draw_focus(self, canvas):
        canvas.draw_ellipse(self.get_rect(), pygame.Color(255, 128, 0), 2)


class Tool(ABC):
    @abstractmethod
    def draw_icon(self, canvas: ICanvas, rect: Rect):
        pass

    def draw(self, _canvas: ICanvas):
        pass

    def handle_input(self, _canvas: ICanvas, _event: pygame.event.Event):
        return False

    def handle_colour(self, _colour: Color | None, _outline_colour: Color | None):
        return False


class SelectTool(Tool):
    shape: Shape | None
    dragging: bool

    def __init__(self):
        self.pointer = pygame.transform.scale(
            pygame.image.load("assets/mouse_pointer.png"), (80, 80))
        self.dragging = False
        self.drag_handle = None
        self.shape = None
        self.x = 0
        self.y = 0

    def get_handles(self) -> list[Rect]:
        assert self.shape
        points = self.shape.get_points()
        handles = []
        for p in points:
            handle = Rect(p.x - 5, p.y - 5, 10, 10)
            handles.append(handle)
        return handles

    def get_rotation_handle(self) -> tuple[Vector2, Vector2]:
        assert self.shape
        rect = self.shape.get_rect()
        cx = rect.centerx
        p1 = Vector2(cx, rect.y - 20)
        p2 = Vector2(cx, rect.y)
        p1 = (p1 - rect.center).rotate(self.shape.rotation) + rect.center
        p2 = (p2 - rect.center).rotate(self.shape.rotation) + rect.center
        return p1, p2

    def get_handle(self, x: float, y: float) -> int | None:
        handles = self.get_handles()
        for i, handle in enumerate(handles):
            if pygame.Rect(*handle).collidepoint(x, y):
                return i
        p1, _ = self.get_rotation_handle()
        if pygame.Rect(p1.x - 5, p1.y - 5, 10, 10).collidepoint(x, y):
            return 4

    def process_drag_handle(self, handle: int, dx: float, dy: float):
        assert self.shape
        if handle == 0:
            self.shape.move(dx, dy)
            self.shape.resize(-dx, -dy)
        elif handle == 1:
            self.shape.move(0, dy)
            self.shape.resize(dx, -dy)
        elif handle == 2:
            self.shape.resize(dx, dy)
        elif handle == 3:
            self.shape.move(dx, 0)
            self.shape.resize(-dx, dy)

    def change_colour(self, colour: Color | None, outline_colour: Color | None):
        assert self.shape
        if colour:
            self.shape.colour = colour
        if outline_colour:
            self.shape.outline_colour = outline_colour

    def draw_handles(self, canvas: ICanvas):
        for x, y, w, h in self.get_handles():
            canvas.draw_rect(Rect(x, y, w, h), 0, WHITE)
            canvas.draw_rect(Rect(x, y, w, h), 0, BLACK, 1)
        p1, p2 = self.get_rotation_handle()
        rect = Rect(p1.x - 5, p1.y - 5, 10, 10)
        canvas.draw_line(p1, p2)
        canvas.draw_ellipse(rect, WHITE)
        canvas.draw_ellipse(rect, BLACK, 1)

    def draw(self, canvas):
        if self.shape:
            self.shape.draw_focus(canvas)
            self.draw_handles(canvas)

    def draw_icon(self, canvas: ICanvas, rect: Rect):
        canvas.draw_image(rect.x+5, rect.y+5, self.pointer)

    def handle_colour(self, colour: Color | None, outline_colour: Color | None):
        self.change_colour(colour, outline_colour)
        return True

    def handle_input(self, canvas: ICanvas, event: pygame.event.Event):
        if self.shape:
            if event.type == MOUSEBUTTONDOWN:
                x, y = pygame.mouse.get_pos()
                handle = self.get_handle(x, y)
                if handle is not None:
                    self.dragging = True
                    self.drag_handle = handle
                    self.x, self.y = x, y
                    return
            elif event.type == MOUSEMOTION:
                if self.drag_handle is not None:
                    x, y = pygame.mouse.get_pos()
                    if self.drag_handle == 4:
                        self.shape.rotate(pygame.Vector2(x, y))
                    else:
                        dx, dy = x - self.x, y - self.y
                        self.process_drag_handle(self.drag_handle, dx, dy)
                    self.x, self.y = x, y
                    return
            elif event.type == MOUSEBUTTONUP:
                if self.drag_handle is not None:
                    self.shape.normalize()
                    self.dragging = False
                    self.drag_handle = None
                    return

        if event.type == MOUSEBUTTONDOWN:
            self.dragging = True
            x, y = pygame.mouse.get_pos()
            self.dragging, self.shape = canvas.select(x, y)
            self.x, self.y = x, y
        elif event.type == MOUSEMOTION:
            if not self.dragging or not self.shape:
                return
            x, y = pygame.mouse.get_pos()
            dx, dy = x - self.x, y - self.y
            self.shape.move(dx, dy)
            self.x, self.y = x, y
        elif event.type == MOUSEBUTTONUP:
            self.dragging = False
        elif event.type == KEYUP:
            if event.key == K_DELETE or event.key == K_BACKSPACE:
                if self.shape:
                    canvas.remove_shape(self.shape)
                    self.shape = None


class EllipseTool(Tool):
    def __init__(self):
        self.drawing = False
        self.x = 0
        self.y = 0
        self.mx = 0
        self.my = 0

    def draw_icon(self, canvas: ICanvas, rect: Rect):
        canvas.draw_ellipse(Rect(rect.x+5, rect.y+5, rect.w-10, rect.h-10))

    def draw(self, canvas: ICanvas):
        if not self.drawing:
            return
        x, y, w, h = make_rect(self.x, self.y, self.mx, self.my)
        canvas.draw_ellipse(Rect(x, y, w, h), GRAY)

    def handle_input(self, canvas: ICanvas, event: pygame.event.Event):
        if event.type == MOUSEBUTTONDOWN:
            x, y = pygame.mouse.get_pos()
            self.drawing = True
            self.x = x
            self.y = y
            self.mx = x
            self.my = y
        elif event.type == MOUSEMOTION:
            if not self.drawing:
                return
            x, y = pygame.mouse.get_pos()
            self.mx, self.my = x, y
        elif event.type == MOUSEBUTTONUP:
            if not self.drawing:
                return
            self.drawing = False
            x, y = pygame.mouse.get_pos()
            x, y, w, h = make_rect(x, y, self.x, self.y)
            shape = Ellipse(x, y, w, h)
            canvas.add_shape(shape)


class RectTool(Tool):
    def __init__(self):
        self.drawing = False
        self.x = 0
        self.y = 0
        self.mx = 0
        self.my = 0

    def draw_icon(self, canvas: ICanvas, rect: Rect):
        canvas.draw_rect(Rect(rect.x+5, rect.y+5, rect.w-10, rect.h-10), 0)

    def draw(self, canvas: ICanvas):
        if not self.drawing:
            return
        rect = make_rect(self.x, self.y, self.mx, self.my)
        canvas.draw_rect(rect, 0, GRAY)

    def handle_input(self, canvas: ICanvas, event: pygame.event.Event):
        if event.type == MOUSEBUTTONDOWN:
            x, y = pygame.mouse.get_pos()
            self.drawing = True
            self.x = x
            self.y = y
            self.mx = x
            self.my = y
        elif event.type == MOUSEMOTION:
            if not self.drawing:
                return
            x, y = pygame.mouse.get_pos()
            self.mx, self.my = x, y
        elif event.type == MOUSEBUTTONUP:
            if not self.drawing:
                return
            self.drawing = False
            x, y = pygame.mouse.get_pos()
            x, y, w, h = make_rect(x, y, self.x, self.y)
            shape = Rectangle(x, y, w, h)
            canvas.add_shape(shape)


class ColourBoard():
    def draw_icon(self, canvas: ICanvas, rect: Rect, colour: Color):
        canvas.draw_rect(
            Rect(rect.x+5, rect.y+5, rect.w-10, rect.h-10), 0, colour)


class PreviewColourBoard():
    def draw_board(self, canvas, rect):
        x, y, w, h = rect
        canvas.draw_rect(Rect(x+5, y+5, w-10, h-10), 0, canvas.colour)
        canvas.draw_rect(Rect(x+5, y+5, w-10, h-10),
                         0, canvas.outline_colour, 3)


class Canvas(ICanvas):
    shapes: list[Shape]
    tools: list[Tool]
    colours: list[Color]
    colour: Color
    outline_colour: Color

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
            pygame.Color(0, 0, 0),
            pygame.Color(255, 0, 0),
            pygame.Color(255, 125, 0),
            pygame.Color(255, 255, 0),
            pygame.Color(0, 255, 0),
            pygame.Color(0, 255, 255),
            pygame.Color(0, 0, 255),
            pygame.Color(255, 0, 255),
            pygame.Color(255, 255, 255)
        ]
        self.tool = self.tools[0]
        self.colour = self.colours[0]
        self.outline_colour = self.colours[0]
        self.rotate_degrees = 0

    def handle_tool_switch(self, event: pygame.event.Event):
        if event.type == MOUSEBUTTONDOWN:
            for tool, rect in self.each_tool():
                mousex, mousey = pygame.mouse.get_pos()
                if rect.collidepoint(mousex, mousey):
                    self.tool = tool
                    return True
        return False

    def handle_colour_switch(self, event: pygame.event.Event):
        if event.type == MOUSEBUTTONDOWN:
            for colour, rect in self.each_colour():
                mousex, mousey = pygame.mouse.get_pos()
                if rect.collidepoint(mousex, mousey):
                    if event.button == BUTTON_LEFT:
                        if not self.tool.handle_colour(colour, None):
                            self.colour = colour
                    elif event.button == BUTTON_RIGHT:
                        if not self.tool.handle_colour(None, colour):
                            self.outline_colour = colour
                    return True

    def each_tool(self) -> Generator[tuple[Tool, Rect], Any, None]:
        width = 100
        height = 80
        for i, tool in enumerate(self.tools):
            x, y = 20, 20 + height * i
            yield tool, Rect(x, y, width, height)

    def each_colour(self) -> Generator[tuple[Color, Rect], Any, None]:
        width = 70
        height = 60
        for i, colour in enumerate(self.colours):
            x, y = 710, 20 + height * i
            yield colour, Rect(x, y, width, height)

    def select(self, x: float, y: float):
        for shape in reversed(self.shapes):
            if shape.get_rect().collidepoint(x, y):
                return True, shape
        return False, None

    def remove_shape(self, shape: Shape):
        self.shapes.remove(shape)

    def add_shape(self, shape: Shape):
        shape.colour = self.colour
        shape.outline_colour = self.outline_colour
        self.shapes.append(shape)

    def draw_image(self, x: float, y: float, image: pygame.Surface):
        self.win.blit(image, (x, y))

    def draw_ellipse(self, rect: Rect, color: Color = BLACK, width: int = 0):
        pygame.draw.ellipse(self.win, color, rect, width)

    def draw_polygon(self, points: Sequence[Coordinate], color: Color = BLACK, width: int = 0):
        pygame.draw.polygon(self.win, color, points, width)

    def draw_rect(self, rect: Rect, rotation: float = 0, color: Color = BLACK, width: int = 0):
        center = rect.center
        points = [rect.topleft, rect.topright,
                  rect.bottomright, rect.bottomleft]
        new_points = []
        for point in points:
            p = pygame.Vector2(point)
            delta = p - center
            delta = delta.rotate(rotation) + center
            new_points.append(delta)
        pygame.draw.polygon(self.win, color, new_points, width)

    def draw_line(self, p1: Vector2, p2: Vector2, color: Color = BLACK, width: int = 1):
        pygame.draw.line(self.win, color, p1, p2, width)

    def draw_tools(self):
        for tool, rect in self.each_tool():
            self.draw_rect(rect, 0, pygame.Color(192, 192, 192))
            tool.draw_icon(self, rect)
            if tool == self.tool:
                self.draw_rect(rect, 0, pygame.Color(255, 128, 0), 2)

    def draw_colours(self):
        for colour, rect in self.each_colour():
            self.draw_rect(rect, 0, pygame.Color(192, 192, 192))
            ColourBoard().draw_icon(self, rect, colour)

    def draw(self):
        self.draw_background()
        for shape in self.shapes:
            shape.draw(self)
        self.tool.draw(self)
        self.draw_tools()
        self.board.draw_board(self, Rect(
            20, 20 + 80 * len(self.tools), 100, 80))
        self.draw_colours()
        pygame.display.update()

    def handle_input(self):
        for event in pygame.event.get():
            if event.type == QUIT:
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
        # pylint: disable-next=no-member
        pygame.quit()

    def draw_background(self):
        self.win.fill((255, 255, 255))


if __name__ == "__main__":
    Canvas().run()
