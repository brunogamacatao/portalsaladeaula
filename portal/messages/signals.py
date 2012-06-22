"""
Signals relating to messages.
"""
from django.dispatch import Signal

message_will_be_posted = Signal(providing_args=["message", "request"])
massage_was_posted     = Signal(providing_args=["message", "request"])