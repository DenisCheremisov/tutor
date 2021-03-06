#!/usr/bin/env python
# -*- coding: utf-8 -*-

import threading
import color


import pygtk
pygtk.require('2.0')
import gtk, gobject, cairo, math


height = 200
width  = 200

def prepare (f):
    """
    Декоратор для сокращения количества операций
    """
    def prepared (cl, *args, **kwargs):
        cl.lock.acquire ()
        if 'color' in kwargs:
            cl.set_color (kwargs['color'])
            kwargs.pop ('color')
        f (cl, *args, **kwargs)
        widget.queue_draw ()
        cl.lock.release ()
        return cl
    return prepared

class  Cover:
    """
    Вспомогательный класс. Используется для отложенного рисования.
    """
    def __init__ (self):
        self.lock = threading.Lock ()
        self.operations = []
        self.screen = None

    @prepare
    def move_to (self, x, y):
        self.operations.append (lambda c: c.move_to(x,y))

    @prepare
    def set_color (self, new_color):
        r,g,b = [i/255.0 for i in new_color]
        self.operations.append (lambda c: c.stroke())
        self.operations.append (lambda c: c.set_source_rgb (r,g,b))

    @prepare
    def line_to (self, x, y):
        self.operations.append (lambda c: c.line_to(x,y))

    @prepare
    def circle (self, x, y, r):
        self.operations.append (lambda c: c.stroke())
        self.operations.append (lambda c: c.arc (x, y, r, 0.0, 2.0*math.pi))

    @prepare
    def rectangle (self, x, y, w, h):
        self.operations.append (lambda c: c.rectangle (x, y, w, h))

    def polygon (self, point_list):
        if len (point_list) == 1:
            self.circle (*(lisp(point_list[0]) + [1]))
        elif len (point_list) == 2:
            self.line(*point_list[0])(*point_list[1])
        else:
            self.move_to(*point_list[0])
            for point in point_list[1:]:
                self.line_to(*point)
            self.close_path()

    @prepare
    def fill (self):
        self.operations.append (lambda c: c.fill ())

    @prepare
    def stroke (self):
        self.operations.append (lambda c: c.stroke ())

    @prepare
    def close_path (self):
        self.operations.append (lambda c: c.close_path())


    def line (self, x, y):
        self.move_to (x, y)
        return self.line_to

    @prepare
    def text (self, *args, **kwarg):
        text = ''.join(map(str,args))
        if 'at' in kwarg:
            self.operations.append (lambda c: c.move_to(*kwarg['at']))
        self.operations.append (lambda c: c.show_text(text))

    @prepare
    def arc (self, x, y, r, a1, a2):
        self.operations.append (lambda c: c.arc(x,y,r,a1,a2))

    @prepare
    def arc_negative (self, x, y, r, a1, a2):
        self.operations.append (lambda c: c.arc_negative(x,y,r,a1,a2))

    def sector(self,edge1,edge2,middle):
        from vector import Vector
        from arc import calculate_arc_parameters
        a = Vector(edge1)
        b = Vector(edge2)
        c = Vector(middle)
        d = calculate_arc_parameters (a,b,c)
        print d
        self.stroke()
        self.arc(d.center.x, d.center.y, d.R, d.phi1, d.phi)
        self.arc(d.center.x, d.center.y, d.R, d.phi, d.phi2)
        
        
        
            
cover = Cover ()


class Shapes(gtk.DrawingArea):

    # Draw in response to an expose-event
    __gsignals__ = { "expose-event": "override" }


    # Handle the expose-event by drawing
    def do_expose_event(self, event):

        # Create the cairo context
        cr = self.window.cairo_create()

        # Restrict Cairo to the exposed area; avoid extra work
        cr.rectangle(event.area.x, event.area.y,
                     event.area.width, event.area.height)
        cr.clip()

        self.draw(cr, *self.window.get_size())


    def draw(self, cr, w, h):
        """
        Заливаем площадь рисования белым цветом
        """
        global width, height
        width, height = w, h
        cover.screen = self
        cr.set_source_rgb(1, 1, 1)
        cr.rectangle(0, 0, width, height)
        cr.fill()
        cr.set_source_rgb(0, 0, 0)

        cover.lock.acquire ()
        for operation in cover.operations:
             operation (cr)
        cover.lock.release ()
        cr.stroke ()


widget = None
class MyThread (threading.Thread):
    def run (self):
        cover.lock.acquire()
        window = gtk.Window()
        window.connect("delete-event", gtk.main_quit)
        global widget
        widget = Shapes()
        widget.show()
        window.add(widget)
        window.present()
        cover.lock.release()
        gtk.main()

cover.lock.acquire()
MyThread().start()
cover.lock.release()
