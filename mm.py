import CustomClient as cc
import time
import threading
import asyncio
from collections import deque

client = cc.Client()

print(client.get_portfolio())
for i in client.get_positions():
    print(i)


ticker = "KXNBAGAME-25OCT21HOUOKC-HOU"

team1, team2 = client.get_both_tickers(ticker)


book0 = client.connect_to_book(team2, False)


prices = deque(maxlen=2)

t = time.perf_counter()
inc = 0

client._get_headers
start_time = time.perf_counter()
print(client.get_portfolio())
print(f"Time to get portfolio after initial connection: {time.perf_counter()-start_time}")


"""
while True:
    if len(client.books) < 1:
        continue
    now = time.perf_counter()
    if now - t >= 1/10:
        inc += 1
        t = now
        prices.append(client.books[0].calc_real_mid())
        if not prices[0] == -1 and len(prices) > 1:
            print(f"{prices}: {(prices[1] - prices[0])*10}")
        #print(f"Bid: {client.books[0].best_bid}, Ask: {client.books[0].best_ask}, Inc: {inc}")
        #print(client.books[0].calc_real_mid())"""

print()
order = client.create_order("sell", "yes", team2, 75, 1)
order_id = order.get('order').get('order_id')
print(order_id)
time.sleep(1)
print()
print(client.get_order_info(order_id))
print()
print(client.cancel_order(order_id))