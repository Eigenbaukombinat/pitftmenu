#coding:utf8
import os
import time
import sys
import pygame
import RPi.GPIO as GPIO  
import numpy
import math

    
BUTTON_EVENT = pygame.USEREVENT + 1
global TIMER_EVENT
TIMER_EVENT = pygame.USEREVENT + 2

SENSOR_REGISTRY = {}
SENSOR_HANDLERS = {}

def register_sensor(klass, addr):
      global TIMER_EVENT
      pygame.time.set_timer(TIMER_EVENT, 1000)
      SENSOR_REGISTRY[TIMER_EVENT] = klass(addr)
      TIMER_EVENT += 1
      return SENSOR_REGISTRY[TIMER_EVENT - 1], TIMER_EVENT - 1

def unregister_sensor(id):
    global TIMER_EVENT
    del SENSOR_REGISTRY[id]
    TIMER_EVENT -= 1

def register_sensor_handler(timer_event, target):
    handlers = SENSOR_HANDLERS.get(timer_event, None)
    if handlers is None:
        handlers = SENSOR_HANDLERS[timer_event] = []
    handlers.append(target)

def unregister_sensor_handler(timer_event, target):
    handlers = SENSOR_HANDLERS.get(timer_event, [])
    handlers_new = [t for t in handlers if t != target]
    SENSOR_HANDLERS[timer_event] = handlers_new


class TempSensor(object):
    
    degree = -999
    last = -1000

    def __init__(self, addr):
       self.file = open('/sys/bus/w1/devices/%s/w1_slave' % addr, 'r')
    
    def update(self):
       self.file.seek(0)
       out =self.file.read()
       if 'crc=d1 YES' not in out:
           self.degree = -999
       try:
           temp = out[out.find('t=')+2:]
       except IndexError:
           self.degree = -999
       try:
           self.degree = float(temp) / 1000.0
       except TypeError:
           self.degree = -999
       update_needed = self.last != self.degree
       self.last = self.degree
       return update_needed





def btn_rising(channel):
    ev = pygame.event.Event(BUTTON_EVENT, channel=channel)
    pygame.event.post(ev)


class Button(object):
    def __init__(self, pin, text, x, y, w, h, col):
       self.pin = pin
       self.text = text
       self.x = x
       self.y = y
       self.w = w
       self.h = h
       self.col = col

    def attach(self, screen):
       self.screen = screen

    def render(self):
       self.rect_shape = pygame.Rect(self.x, self.y, self.w, self.h)
       self.rect = pygame.draw.rect(self.screen.app.scr, self.col, self.rect_shape)
       font = pygame.font.SysFont("consolas", BTN_RO, True)
       text = font.render(self.text, True, (255,255,255))
       self.screen.app.scr.blit(text, [self.x,self.y])


class QuitAction(object):
    def __call__(self, app, current_screen):
        GPIO.cleanup()
        current_screen.clear()
        pygame.display.flip()
        pygame.quit()

class SwitchAction(object):
    def __init__(self, target):
        self.target = target
    
    def __call__(self, app, current_screen):
        current_screen.clear()
        current_screen.close()
        app.goto(self.target)
        self.target.open()
        self.target.render_buttons()
        pygame.display.flip()

class ToggleAction(object):
    def __init__(self, pin):
        self.pin = pin
        self.is_on = False
        GPIO.setup(pin, GPIO.OUT)

    def __call__(self, app, current_screen):
        print "set pin %i to %s" % (self.pin, not self.is_on)
        GPIO.output(self.pin, not self.is_on)
        self.is_on = not self.is_on


class Screen(object):
    def __init__(self, app, caption):
        self.app = app
        self.buttons = {}
        self.actions = {}
        self.add_button(99, caption, (0, 21, 220, 20), (0,0,0))

    def add_button(self, pin, text, (x, y, w, h), col=(40,40,40)):
        self.buttons[pin] = Button(pin, text, x, y, w, h, col)
        self.buttons[pin].attach(self)

    def add_action(self, pin, action):
        self.actions[pin] = action

    def open(self):
        pass

    def close(self):
        pass

    def update(self):
        pass

    def clear(self):
        self.app.clear()

    def render_buttons(self):
        for pin, button in self.buttons.items():
            button.render()
        pygame.display.flip()


class ThermostatScreen(Screen):
    def __init__(self, app, caption, addr):
        super(ThermostatScreen, self).__init__(app, caption)
        self.addr = addr
 
    def update(self):
       txt = self.sensor.degree
       self.rect_shape = pygame.Rect(40, 80, 220, 80)
       self.rect = pygame.draw.rect(self.app.scr, (0,0,0), self.rect_shape)
       font = pygame.font.SysFont("consolas", 35, True)
       text = font.render(str(txt), True, (255,255,255))
       self.app.scr.blit(text, [50,90])
       pygame.display.flip()
        
    def open(self):
       self.sensor, self.event = register_sensor(TempSensor, self.addr)
       self.sensor_handler = register_sensor_handler(self.event, self.sensor.update) 
       self.update()

    def close(self):
       unregister_sensor(self.event)
       unregister_sensor_handler(self.event, self.sensor.update)


class TftApp(object):

    def __init__(self, main_screen_cls, fb_dev="/dev/fb1", width=220, height=176, buttons=[], background=(255,255,255)):
	os.environ["SDL_FBDEV"] = fb_dev
	pygame.init()
	self.scr = pygame.display.set_mode((width, height))
	pygame.mouse.set_visible(0)
	# Fill background
	background_sur = pygame.Surface(self.scr.get_size())
	self.background_sur = background_sur.convert()
	self.background_sur.fill(background)
        self.clear()
	pygame.display.flip()
        GPIO.cleanup()
	GPIO.setmode(GPIO.BCM)  
        self.button_pins = []
        for button in buttons:
           self.button_pins.append(button)
	   GPIO.setup(button, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)  
	   GPIO.add_event_detect(button, GPIO.FALLING, callback=btn_rising, bouncetime=150)  
        self.main_screen = main_screen_cls(self, 'Main')

    def clear(self):
	self.scr.blit(self.background_sur, (0, 0))

    def start(self):
        self.goto(self.main_screen)

    def exec_actions(self, ch):
        if ch not in self.current.actions.keys():
            return
        self.current.actions[ch](self, self.current)

    def goto(self, screen):
        self.current = screen
        self.current.render_buttons()
	pygame.display.flip()


BTN_LO = 17 
BTN_LU = 27
BTN_RO = 18
BTN_RU = 24

def setup():
	app = TftApp(Screen, buttons=(BTN_RU, BTN_RO, BTN_LO, BTN_LU))
	main = app.main_screen
	foo = Screen(app, 'Foo screen')
	bar = Screen(app, 'Bar screen')
	thermo = ThermostatScreen(app, 'Temperature', '28-000002574ff2')
	foo_action = SwitchAction(foo)
	bar_action = SwitchAction(bar)
	main_action = SwitchAction(main)
	thermo_action = SwitchAction(thermo)

	LO = (0,0,109,20)
	RO = (110,0,110,20)
	LU = (0,156,109,20)
	RU = (110,156,109,20)

	main.add_button(BTN_LO, 'Foo', LO)
	main.add_action(BTN_LO, foo_action)
	main.add_button(BTN_RO, 'Bar', RO)
	main.add_action(BTN_RO, bar_action)
	main.add_button(BTN_LU, 'Temp', LU)
	main.add_action(BTN_LU, thermo_action)
	main.add_button(BTN_RU, 'Barrf', RU)
        
	thermo.add_button(BTN_LO, 'Main', LO)
	foo.add_button(BTN_LO, 'Main', LO)
	bar.add_button(BTN_LO, 'Main', LO)
	foo.add_action(BTN_LO, main_action)
	bar.add_action(BTN_LO, main_action)
	thermo.add_action(BTN_LO, main_action)

	relais_action = ToggleAction(22)
	foo.add_button(BTN_RO, 'Toggle Relais', RO)
	foo.add_action(BTN_RO, relais_action)

	quit_action = QuitAction()
	bar.add_button(BTN_RO, 'Quit', RO)
	bar.add_action(BTN_RO, quit_action)
	return app

app = setup()
app.start()
while True:
    ev = pygame.event.wait()
    timer_events = SENSOR_HANDLERS.get(ev.type, [])
    update_needed = False
    for timer_event in timer_events:
        if timer_event is not None:
            update_needed = timer_event()
    if update_needed:
        app.current.update()
    if not hasattr(ev, 'channel'):
        continue
    print ev.channel
    app.exec_actions(ev.channel)
