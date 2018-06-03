from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import argparse
import numpy as np
import RPi.GPIO as io
import signal
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

  def __init__(self, in1_pin, in2_pin, pwm_pin):
    self._in1_pin = in1_pin
    self._in2_pin = in2_pin
    self._pwm_pin = pwm_pin

    io.setup(in1_pin, io.OUT)
    io.setup(in2_pin, io.OUT)
    io.setup(pwm_pin, io.OUT)

    self._pwm = io.PWM(pwm_pin, 100)  # 100 Hz.
    self._pwm.start(0)

  def __del__(self):
    self._pwm.stop()

  def set(self, v):
    v = min(v, 1., max(v, -1.))  # Values between -1 and 1.
    if v < 0.:
      io.output(self._in1_pin, True)
      io.output(self._in2_pin, False)
    else:
      io.output(self._in1_pin, False)
      io.output(self._in2_pin, True)
    speed = int(99. * abs(v))
    self._pwm.ChangeDutyCycle(speed)


if __name__ == '__main__':
  # Intercept Ctrl+C.
  signal.signal(signal.SIGINT, signal_handler)

  parser = argparse.ArgumentParser(description='Test motor.')
  parser.add_argument('--in1', type=int, action='store', default=23)
  parser.add_argument('--in2', type=int, action='store', default=24)
  parser.add_argument('--pwm', type=int, action='store', default=25)
  args = parser.parse_args()

  init_gpio()
  m = Motor(args.in1, args.in2, args.pwm)
  for i in np.linspace(-1., 1., 21):
    m.set(i)
    time.sleep(.5)
  cleanup_gpio()
