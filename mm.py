import CustomClient as cc
import time
import threading
import asyncio
from collections import deque

client = cc.Client()

port = client.get_portfolio()
print(f"Client started, portfolio snapshot: {port}")



ticker = "KXNBAGAME-25OCT21GSWLAL-GSW"

team1, team2 = client.get_both_tickers(ticker)


book0 = client.connect_to_book(team2, False)
time.sleep(2)
t = time.perf_counter()
while True:
    if time.perf_counter()-t > 0.1:
        t = time.perf_counter()
        print(client.books[0].best_bid)
        print(client.books[0].best_bid_quantity)
        print()