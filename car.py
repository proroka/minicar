from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import argparse
import socket
import struct
import RPi.GPIO as io

import signal
import sys

_DEADZONE = .2


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
    if abs(v) < _DEADZONE:
      v = 0
    v = min(v, 1., max(v, -1.))  # Values between -1 and 1.
    if v < 0.:
      # Rescale between .2 and 1.
      v = (v + _DEADZONE) / (1. - _DEADZONE)
      io.output(self._in1_pin, True)
      io.output(self._in2_pin, False)
    else:
      v = (v - _DEADZONE) / (1. - _DEADZONE)
      io.output(self._in1_pin, False)
      io.output(self._in2_pin, True)
    speed = int(100. * abs(v))
    v = min(v, 100.)  # Values between -1 and 1.
    self._pwm.ChangeDutyCycle(speed)


def run(local_ip, local_port):
  # Intercept Ctrl+C.
  signal.signal(signal.SIGINT, signal_handler)

  print('Binding to UDP port...')
  local_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
  local_socket.bind((local_ip, local_port))

  init_gpio()
  steering = Motor(in1_pin=23, in2_pin=24, pwm_pin=25)

  while True:
    # 2 floats.
    print('Waiting for data...')
    data, _ = local_socket.recvfrom(4 * 2)
    forward, left = struct.unpack('ff', data)
    steering.set(left)
    print('L/R: {}'.format(left))


if __name__ == '__main__':
  parser = argparse.ArgumentParser(description='Sends forward/backward and left/right controls by UDP.')
  parser.add_argument('--local_ip', action='store', default='192.168.2.3', help='IP of minicar')
  parser.add_argument('--local_port', type=int, action='store', default=6789, help='Port of minicar')
  args = parser.parse_args()
  run(args.local_ip, args.local_port)
