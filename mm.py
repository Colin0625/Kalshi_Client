import CustomClient as cc
import time
import threading
import asyncio
from collections import deque

client = cc.Client()

print(client.get_portfolio())
for i in client.get_positions():
    print(i)


team1, team2 = client.get_both_tickers("KXNFLGAME-25OCT20TBDET-TB")


book0 = client.connect_to_book(team2, False)


prices = deque(maxlen=20)

t = time.perf_counter()
inc = 0

while True:
    if len(client.books) < 1:
        continue
    now = time.perf_counter()
    if now - t >= 1/10:
        inc += 1
        t = now
        #print(f"Bid: {client.books[0].best_bid}, Ask: {client.books[0].best_ask}, Inc: {inc}")
        print(client.books[0].calc_real_mid())