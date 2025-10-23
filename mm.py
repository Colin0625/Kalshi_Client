import CustomClient as cc
import time
import threading
import asyncio
from collections import deque
import math


def calculate_fees(price, contracts):
    return math.ceil((0.0175 * contracts * price * (1-price))*100)

def calculate_spread_profit(bid_price, ask_price, contracts):
    bid_fees = calculate_fees(bid_price, contracts)
    ask_fees = calculate_fees(ask_price, contracts)
    rev = (ask_price - bid_price) * contracts
    return rev - bid_fees - ask_fees


client = cc.Client()

port = client.get_portfolio()
print(f"Client started, portfolio snapshot: {port}")



ticker = "KXNFLGAME-25OCT23MINLAC-MIN"

team1, team2 = client.get_both_tickers(ticker)



te = team2



book0 = client.connect_to_book(te, False)
time.sleep(2)
print()
print(client.create_order('buy', 'yes', te, client.books[0].best_bid, 5))
print()
print(client.create_order('sell', 'yes', te, client.books[0].best_ask, 5))
print()

t = time.perf_counter()

def fire(raw, msg):
    print(f"{raw}, {msg}")

print()
client.connect_to_fills(False, fire, msg="yo wassup")




c = 0

while True:
    pass
    """if time.perf_counter()-t > 1/4:
        t = time.perf_counter()
        #print(client.books[0].best_bid)
        #print(client.books[0].best_bid_quantity)
        c += 1
        print(f"Contracts: {c}")
        print(client.books[0].best_bid/100)
        print(client.books[0].best_ask/100)
        print(f"Entry Cost: {(client.books[0].best_bid * c)/100}")
        print(f"Revenue without fees: {((client.books[0].best_ask - client.books[0].best_bid)*c)/100}")
        #print(calculate_fees(client.books[0].best_bid/100, c))
        #print(calculate_fees(client.books[0].best_ask/100, c))
        print(f"Profit: {((client.books[0].best_ask - client.books[0].best_bid)*c - calculate_fees(client.books[0].best_bid/100, c) - calculate_fees(client.books[0].best_ask/100, c))/100}")
        print()"""