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

# returns in per tick slope, may need to convert to per second.
def get_slope(lis):
    N = len(lis)
    num1 = (N*sum([i*v for i, v in enumerate(lis)]))
    num2 = (sum([x for x in range(10)]) * sum(lis))
    den1 = (N*sum([x**2 for x in range(N)]))
    den2 = (sum(list(range(N)))**2)
    return (num1 - num2)/(den1 - den2)

def update_inventory(event: dict):
    inventory = int(event.get("msg").get("post_position"))
    print("recieved fill")
    if event.get('msg').get("order_id") == quote_ids[0]:
        print("bid fill")
        if event.get('msg').get('count') == quote_quantities[0]:
            print("Full")
            quote_ids[0] = None
            quotes[0] = 0
            quote_quantities[0] = 0
        else:
            print("partial")
            quote_quantities[0] -= event.get('msg').get('count')
    elif event.get('msg').get("order_id") == quote_ids[1]:
        print("ask fill")
        if event.get('msg').get('count') == quote_quantities[1]:
            print("full")
            quote_ids[1] = None
            quotes[1] = 0
            quote_quantities[1] = 0
        else:
            print("partial")
            quote_quantities[1] -= event.get('msg').get('count')
    else:
        print("UNKNOW ORDER FILL! ------------------------------- !!!!!!!!!!!!")
    
    print()
    print()
    print()
    print(event)
    print(f"Inventory updated to {inventory}")
    print()
    print()
    print()


def liquidate(inv):
    global inventory
    global quote_ids
    global quote_quantities
    global quotes
    if inv == 0:
        return 0
    elif inv < 0:
        client.create_order('buy', 'yes', team, book.best_ask, abs(inv))
    else:
        client.create_order('sell', 'yes', ticker, book.best_bid, abs(inv))
    inventory = 0
    quote_ids = [None, None]
    quotes = [0, 0]
    quote_quantities = [0,0]




client = cc.Client()

port = client.get_portfolio()
print(f"Client started, portfolio snapshot: {port}")



ticker = "KXNBAGAME-25OCT27PORLAL-POR"

team1, team2 = client.get_both_tickers(ticker)

team = team1


task, book = client.connect_to_book(team, False)
time.sleep(0.5)

client.connect_to_fills(False, update_inventory)
time.sleep(1)





inventory = 0
quote_ids = [None, None]
quotes = [0, 0]
quote_quantities = [0, 0]



bull_persistence = 0
bear_persistence = 0

slope_queue = deque(maxlen=10)
drift_queue = deque(maxlen=50)

slopes = deque(maxlen=50)

counter = 0



t = time.perf_counter()
while True:
    if time.perf_counter() - t >= 0.1:
        t = time.perf_counter()
        # Every tenth of a second

        mid = (book.best_ask + book.best_bid) / 2
        micro = book.get_microprice()

        imbalance = book.best_bid_quantity / (book.best_bid_quantity + book.best_ask_quantity)

        slope_queue.append(micro)
        drift_queue.append(micro)

        print(f"Midprice: {round(mid, 5)}, Bid: {round(book.best_bid, 5)}, Ask: {round(book.best_ask, 5)}")
        print(f"Microprice: {round(micro, 5)}")
        print(f"Imbalance: {round(imbalance, 5)}")
        print(f"Bids: {book.best_bid_quantity}, Asks: {book.best_ask_quantity}, Total: {book.best_bid_quantity+book.best_ask_quantity}")
        #print(f"")
        if len(slope_queue) == 10:
            slope = get_slope(slope_queue)*10
            slopes.append(slope)
            print(f"Slope: {round(slopes[-1], 5)}")
            drift = drift_queue[-1] - drift_queue[0]
            print(f"Drift: {round(drift, 5)}")
            if len(slopes) == 50:
                calc_time = time.perf_counter()
                mean = sum(slopes)/len(slopes)
                std = max(math.sqrt((sum([(x-mean)**2 for x in slopes])) / (len(slopes)-1)), 0.001)
                z_score = (slopes[-1] - mean) / std
                print(f"Mean: {round(mean, 5)}, Std: {round(std, 5)}, Z score: {round(z_score, 5)}")
                print(quote_ids)
                print(quote_quantities)
                
                
                
                        

        print()
