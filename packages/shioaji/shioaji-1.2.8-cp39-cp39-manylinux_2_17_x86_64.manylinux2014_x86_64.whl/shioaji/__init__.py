from shioaji.shioaji import Shioaji
from shioaji.constant import Exchange
from shioaji.account import Account
from shioaji.backend.utils import on_quote, on_event
from shioaji.stream_data_type import (
    TickSTKv1,
    TickFOPv1,
    BidAskSTKv1,
    BidAskFOPv1,
    QuoteSTKv1,
)
from . import config
from .order import Order
from ._version import __version__

def main():
    print("Hello from shioaji!")
    
