import CustomClient as cc
import time
import threading
import asyncio
from collections import deque
import math
import pandas
import matplotlib.pyplot as plt


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


def liquidate():
    global inventory
    global quote_ids
    global quote_quantities
    global quotes
    if inventory == 0:
        return 0
    elif inventory < 0:
        client.create_order('buy', 'yes', team, book.best_ask, abs(inventory))
    else:
        client.create_order('sell', 'yes', ticker, book.best_bid, abs(inventory))
    inventory = 0
    quote_ids = [None, None]
    quotes = [0, 0]
    quote_quantities = [0,0]


def update_trades(msg: dict):
    global tracked_yes_trades
    global tracked_no_trades
    if msg.get('type') == 'subscribed':
        print(f"Message from trade >> {msg}")
    else:
        side = msg.get('msg').get("taker_side")
        print(f"Message from trade >> Taker Side: {side}, Price: {msg.get('msg').get(f'{side}_price')}, Quantity: {msg.get("msg").get("count")}, Total: ${(msg.get('msg').get(f'{side}_price') * msg.get("msg").get("count")) / 100:.2f}")
    
        if side == 'yes':
            tracked_yes_trades.append(msg.get("msg").get("count"))
        else:
            tracked_no_trades.append(msg.get("msg").get("count"))


def count_trades(lis):
    return sum(lis)



client = cc.Client()

port = client.get_portfolio()
print(f"Client started, portfolio snapshot: {port}")



ticker = "KXBTCD-25OCT3019-T107499.99"

team1, team2 = client.get_both_tickers(ticker)

team = team1






inventory = 0
quote_ids = [None, None]
quotes = [0, 0]
quote_quantities = [0, 0]


tracked_yes_trades = []
tracked_no_trades = []


yes_trades_queue = deque(maxlen=50)
no_trades_queue = deque(maxlen=50)







task, book = client.connect_to_book(team, False)
time.sleep(0.1)

client.connect_to_fills(False, update_inventory)
time.sleep(0.1)

client.connect_to_trade(team, update_trades)
time.sleep(2)



bull_persistence = 0
bear_persistence = 0

slope_queue = deque(maxlen=10)
drift_queue = deque(maxlen=50)

slopes = deque(maxlen=50)

counter = 0


midprice_tracker = []
microprice_tracker = []
imbalance_tracker = []
slope_tracker = []
z_tracker = []
drift_tracker = []
ratio_tracker = []

yes_tracker = []
no_tracker = []







minutes_to_run = 0.2

start_time = 0
t = time.perf_counter()
while True:
    if start_time and time.perf_counter() - start_time >= minutes_to_run*60:
        break
    if time.perf_counter() - t >= 0.1:
        t = time.perf_counter()
        # Every tenth of a second

        mid = (book.best_ask + book.best_bid) / 2
        micro = book.get_microprice(depth=1)

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
                if not start_time:
                    start_time = time.perf_counter()
                calc_time = time.perf_counter()
                mean = sum(slopes)/len(slopes)
                std = max(math.sqrt((sum([(x-mean)**2 for x in slopes])) / (len(slopes)-1)), 0.001)
                z_score = (slopes[-1] - mean) / std


                yesses = count_trades(tracked_yes_trades)
                nos = count_trades(tracked_no_trades)
                yes_trades_queue.append(yesses)
                no_trades_queue.append(nos)
                tracked_yes_trades = []
                tracked_no_trades = []

                ratio = sum(list(yes_trades_queue))/max(sum(list(no_trades_queue)), 0.1)


                midprice_tracker.append(mid)
                microprice_tracker.append(micro)
                imbalance_tracker.append(imbalance)
                slope_tracker.append(slope)
                z_tracker.append(z_score)
                drift_tracker.append(drift)
                ratio_tracker.append(ratio)

                yes_tracker.append(yesses)
                no_tracker.append(nos)




                print(f"Mean: {round(mean, 5)}, Std: {round(std, 5)}, Z score: {round(z_score, 5)}")
                print(quote_ids)
                print(quote_quantities)
                print(f"Trades over last 5 seconds >> Yes: {sum(list(yes_trades_queue))}, No: {sum(list(no_trades_queue))}, Ratio (y:n): {ratio}")
                print(f"Time since starting timer: {time.perf_counter()-start_time}")
                
                
                
                
                        

        print()


# print(microprice_tracker)
# print(midprice_tracker)
# print(imbalance_tracker)
# print(slope_tracker)
# print(z_tracker)
# print(drift_tracker)
# print(ratio_tracker)

df = pandas.DataFrame({"micro": microprice_tracker,
                       "mid": midprice_tracker,
                       "imbalance": imbalance_tracker,
                       "slope": slope_tracker,
                       "z-score": z_tracker,
                       "drift": drift_tracker,
                       "ratio": ratio_tracker,
                       "yesses": yes_tracker,
                       "nos": no_tracker})

print(df)

to_time = int(minutes_to_run*600)
pegs = to_time//25
fig, ax = plt.subplots(4, 1)

top = max(df['micro'].max(), df['mid'].max()) + 0.25
middle_price = (df['micro'].mean() + df['mid'].mean()) / 2
bottom = min(df['micro'].min(), df['mid'].min()) - 0.25

ax[0].plot(df.index, df['micro'], color="blue")
# ax[0].plot(df.index, df['mid'], color='red')
ax[0].set_title('Price')
ax[0].set_xticks(range(0, to_time, pegs))
# ax[0].set_ylim(bottom=bottom, top=top)

# ax[3].plot(df.index, df['yesses'])
ax[3].plot(df.index, df['slope'])
ax[3].set_title('slope')
ax[3].set_xticks(range(0, to_time, pegs))

ax[1].plot(df.index, df['z-score'])
ax[1].set_title('Z-Score')
ax[1].set_xticks(range(0, to_time, pegs))

ax[2].plot(df.index, df['drift'])
ax[2].set_title('Drift')
ax[2].set_xticks(range(0, to_time, pegs))




plt.show()




fig, ax = plt.subplots(2, 4)

ax[0, 0].plot(df.index, df['micro'])
ax[0, 0].set_title('Microprice')

ax[0, 1].plot(df.index, df['mid'])
ax[0, 1].set_title('Midprice')

ax[0, 2].plot(df.index, df['imbalance'])
ax[0, 2].set_title('Imbalance')

ax[0, 3].plot(df.index, df['slope'])
ax[0, 3].set_title('Slope')

ax[1, 0].plot(df.index, df['z-score'])
ax[1, 0].set_title('Z-Score')

ax[1, 1].plot(df.index, df['drift'])
ax[1, 1].set_title('Drift')

ax[1, 2].plot(df.index, df['ratio'])
ax[1, 2].set_title('Ratio')






fig.tight_layout()

plt.show()
