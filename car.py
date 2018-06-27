from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import argparse
import math
import RPi.GPIO as io
import signal
import socket
import struct
import sys
import time


def init_gpio():
  io.setmode(io.BCM)


def cleanup_gpio():
  io.cleanup()


def signal_handler(signal, frame):
  print('Cleaning up...')
  cleanup_gpio()
  sys.exit(0)


class Motor(object):

  def __init__(self, in1_pin, in2_pin, pwm_pin, max_value=99.):
    self._in1_pin = in1_pin
    self._in2_pin = in2_pin
    self._pwm_pin = pwm_pin

    io.setup(in1_pin, io.OUT)
    io.setup(in2_pin, io.OUT)
    io.setup(pwm_pin, io.OUT)

    self._pwm = io.PWM(pwm_pin, 100)  # 100 Hz.
    self._pwm.start(0)

    self._max = max_value
    self._current = 0.
    self._t = time.time()
    self._k = 2.

  def __del__(self):
    self._pwm.stop()

  def set(self, v):
    v = min(v, self._max, max(v, -self._max))
    # Continuous leaky integrator.
    dv = v - self._current
    dt = min(time.time() - self._t, .5)
    self._current += dv * (1. - math.exp(-self._k * dt))

    if self._current < 0.:
      io.output(self._in1_pin, True)
      io.output(self._in2_pin, False)
    else:
      io.output(self._in1_pin, False)
      io.output(self._in2_pin, True)

    v = self._current
    if abs(v) < 10.:
      v = 0.  # Turn off completly if possible.
    self._pwm.ChangeDutyCycle(abs(v))


def run(local_ip, local_port, fb_pins, lr_pins):
  if local_ip is None:
    raise ValueError('Local IP address not specified.')

  # Intercept Ctrl+C.
  signal.signal(signal.SIGINT, signal_handler)

  print('Binding to UDP port...')
  local_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
  local_socket.bind((local_ip, local_port))
  local_socket.settimeout(.1)

  init_gpio()
  steering = Motor(in1_pin=lr_pins[0], in2_pin=lr_pins[1], pwm_pin=lr_pins[2])
  speed = Motor(in1_pin=fb_pins[0], in2_pin=fb_pins[1], pwm_pin=fb_pins[2],
                max_value=60.)  # Prevent maxing out forward speed.

  forward = 0.
  steering = 0.
  while True:
    # 2 floats.
    try:
      data, _ = local_socket.recvfrom(4 * 2)
      forward, left = struct.unpack('ff', data)
    except:
      pass
    steering.set(left)
    speed.set(forward)
    print('L/R: {}'.format(left))
    print('F/B: {}'.format(forward))


if __name__ == '__main__':
  # Find local IP.
  s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
  try:
    s.connect(('192.168.2.1', 1))
    local_ip = s.getsockname()[0]
  except:
    local_ip = None
  finally:
    s.close()

  parser = argparse.ArgumentParser(description='Sends forward/backward and left/right controls by UDP.')
  parser.add_argument('--local_ip', action='store', default=local_ip, help='IP of minicar')
  parser.add_argument('--local_port', type=int, action='store', default=6789, help='Port of minicar')
  parser.add_argument('--fb_pins', action='store', default='17,25,4', help='Pins for the forward/backward motion')
  parser.add_argument('--lr_pins', action='store', default='23,22,24', help='Pins for the left/right motion')
  args = parser.parse_args()
  fb_pins = tuple(int(p) for p in args.fb_pins.split(','))
  lr_pins = tuple(int(p) for p in args.lr_pins.split(','))
  run(args.local_ip, args.local_port, fb_pins, lr_pins)
