import CustomClient as cc
import time
import threading
import asyncio
from collections import deque
import math
import pandas


def calculate_fees(price, contracts):
    return math.ceil((0.0175 * contracts * price * (1-price))*100)

def calculate_spread_profit(bid_price, ask_price, contracts):
    bid_fees = calculate_fees(bid_price, contracts)
    ask_fees = calculate_fees(ask_price, contracts)
    rev = (ask_price - bid_price) * contracts
    return rev - bid_fees - ask_fees

class RunningStats:
    def __init__(self):
        self.n = 0          # count
        self.mean = 0.0     # running mean
        self.M2 = 0.0       # sum of squared diffs

    def add(self, x: float):
        self.n += 1
        delta = x - self.mean
        self.mean += delta / self.n
        delta2 = x - self.mean
        self.M2 += delta2 * delta
    
    def std(self):
        # population std if you divide by n, sample std if (n-1)
        if self.n < 2:
            return 0.0
        variance = self.M2 / (self.n - 1)
        return max(variance ** 0.5, 0.01)

# returns in per tick slope, may need to convert to per second.
def get_slope(lis):
    N = len(lis)
    num1 = (N*sum([i*v for i, v in enumerate(lis)]))
    num2 = (sum([x for x in range(10)]) * sum(lis))
    den1 = (N*sum([x**2 for x in range(N)]))
    den2 = (sum(list(range(N)))**2)
    return (num1 - num2)/(den1 - den2)

def update_inventory(event):
    print(event)







client = cc.Client()

port = client.get_portfolio()
print(f"Client started, portfolio snapshot: {port}")



ticker = "KXNCAAFGAME-25OCT25MISSOKLA-OKLA"

team1, team2 = client.get_both_tickers(ticker)

team = team2


task, book = client.connect_to_book(team, False)
time.sleep(0.5)

client.connect_to_fills(False, update_inventory)
time.sleep(1)





inventory = 0
quotes = [None, None]

slope_queue = deque(maxlen=10)
drift_queue = deque(maxlen=50)

slopes = deque(maxlen=50)

counter = 0



t = time.perf_counter()
while True:
    if time.perf_counter() - t >= 0.1:
        t = time.perf_counter()
        # Every tenth of a second

        p = book.get_microprice()

        slope_queue.append(p)
        drift_queue.append(p)

        print(list(drift_queue)[-3:])
        if len(slope_queue) == 10:
            slopes.append(get_slope(slope_queue))
            print(f"Slope: {slopes[-1]}")
            print(f"Drift: {drift_queue[-1] - drift_queue[0]}")
            if len(slopes) == 50:
                if quotes[0] == None:
                    quotes[0] = client.create_order('buy', 'yes', team, book.best_bid, 7)
                if quotes[1] == None:
                    quotes[1] = client.create_order('sell', 'yes', team, book.best_ask, 7)


        print()
