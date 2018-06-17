from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import argparse
import socket
import pygame
import time
import struct


class PS4Controller(object):
  """Class representing the PS4 controller. Pretty straightforward functionality."""

  controller = None
  axis_data = None
  button_data = None
  hat_data = None

  def __init__(self, remote_ip, remote_port):
    """Initialize the joystick components"""
    pygame.init()
    pygame.joystick.init()
    self.controller = pygame.joystick.Joystick(0)
    self.controller.init()

    self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    self.remote_ip = remote_ip
    self.remote_port = remote_port

  def listen(self):
      """Listen for events to happen"""

      if not self.axis_data:
        self.axis_data = {}

      if not self.button_data:
        self.button_data = {}
        for i in range(self.controller.get_numbuttons()):
          self.button_data[i] = False

      if not self.hat_data:
        self.hat_data = {}
        for i in range(self.controller.get_numhats()):
          self.hat_data[i] = (0, 0)

      prev_forward = -2.
      prev_left = -2.
      while True:
        for event in pygame.event.get():
          if event.type == pygame.JOYAXISMOTION:
            self.axis_data[event.axis] = event.value
          elif event.type == pygame.JOYBUTTONDOWN:
            self.button_data[event.button] = True
          elif event.type == pygame.JOYBUTTONUP:
            self.button_data[event.button] = False
          elif event.type == pygame.JOYHATMOTION:
            self.hat_data[event.hat] = event.value

          # Send to remote IP.
          if 5 in self.axis_data and 4 in self.axis_data and 0 in self.axis_data:
            r2 = (self.axis_data[5] + 1.) / 2.
            l2 = -(self.axis_data[4] + 1.) / 2.
            forward = r2 + l2
            left = -self.axis_data[0]
          else:
            forward = 0.
            left = 0.
          if (abs(prev_forward - forward) > 0.01 or
              abs(prev_left - left) > 0.01):
            prev_forward = forward
            prev_left = left
            print(forward, left)
            buf = bytearray(struct.pack('ff', forward, left))
            self.socket.sendto(buf, (self.remote_ip, self.remote_port))

        time.sleep(0.001)


if __name__ == '__main__':
  parser = argparse.ArgumentParser(description='Sends forward/backward and left/right controls by UDP.')
  parser.add_argument('--remote_ip', action='store', default='192.168.2.3', help='IP of minicar')
  parser.add_argument('--remote_port', type=int, action='store', default=6789, help='Port of minicar')
  args = parser.parse_args()

  ps4 = PS4Controller(args.remote_ip, args.remote_port)
  ps4.listen()
