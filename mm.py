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







client = cc.Client()

port = client.get_portfolio()
print(f"Client started, portfolio snapshot: {port}")



ticker = "KXNCAAFGAME-25OCT25MIZZVAN-VAN"

team1, team2 = client.get_both_tickers(ticker)

team = team2


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
    if time.perf_counter() - t >= 0.01:
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
        if len(slope_queue) == 10:
            slopes.append(get_slope(slope_queue)*10)
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
                print(f"Time to calculate all: {time.perf_counter() - t}")
                exit()
                if abs(z_score) > 2 and abs(drift) > 0.25:
                    print("----------------- MOVING!")
                
                else:
                    print("Could go")
                    if not quote_ids[0] and not quote_ids[1]:
                        print("currently going")
                        bid = book.best_bid
                        ask = book.best_ask
                        spread = ask - bid
                        if spread == 1:
                            print("option 1")
                            quote_ids[0] = client.create_order('buy', 'yes', team, bid, 7).get('order').get('order_id')
                            quote_ids[1] = client.create_order('sell', 'yes', team, ask, 7).get('order').get('order_id')
                            quotes[0] = bid
                            quotes[1] = ask
                            quote_quantities[0] = 7
                            quote_quantities[1] = 7
                        if spread == 2:
                            if imbalance < 0.25:
                                print("option 2")
                                quote_ids[0] = client.create_order('buy', 'yes', team, bid, 7).get('order').get('order_id')
                                quote_ids[1] = client.create_order('sell', 'yes', team, ask-1, 7).get('order').get('order_id')
                                quotes[0] = bid
                                quotes[1] = ask-1
                                quote_quantities[0] = 7
                                quote_quantities[1] = 7
                            elif imbalance > 0.75:
                                print("option 3")
                                quote_ids[0] = client.create_order('buy', 'yes', team, bid+1, 7).get('order').get('order_id')
                                quote_ids[1] = client.create_order('sell', 'yes', team, ask, 7).get('order').get('order_id')
                                quotes[0] = bid+1
                                quotes[1] = ask
                                quote_quantities[0] = 7
                                quote_quantities[1] = 7
                            else:
                                print("option 4")
                                quote_ids[0] = client.create_order('buy', 'yes', team, bid, 7).get('order').get('order_id')
                                quote_ids[1] = client.create_order('sell', 'yes', team, ask, 7).get('order').get('order_id')
                                quotes[0] = bid
                                quotes[1] = ask
                                quote_quantities[0] = 7
                                quote_quantities[1] = 7
                        

        print()
