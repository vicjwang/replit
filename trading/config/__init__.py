import os

from .base import *


ENV = os.environ.get('ENV')

if ENV == 'test':
  from .test import *
