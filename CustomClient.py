import requests
import json
import datetime as dt
import websockets.legacy.client as cl
import asyncio
import uuid
import time
import base64
import threading
import multiroutine
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding


def load_private_key_from_file(file_path):
    with open(file_path, "rb") as key_file:
        private_key = serialization.load_pem_private_key(
            key_file.read(),
            password=None,
            backend=default_backend()
        )
    return private_key


key_id = None
with open("secrets/key_id.txt", 'r') as f: # File with your personal key id
    key_id = f.read()
private_key = load_private_key_from_file('secrets/new_key.txt') # File with your RSA private key
api_base = "https://api.elections.kalshi.com"



def sign_key(path, method, ts):
    msg = (ts + method + path).encode("utf-8")

    sig = private_key.sign(
        msg,
        padding.PSS(mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.DIGEST_LENGTH),
        hashes.SHA256()
    )
    return base64.b64encode(sig).decode("utf-8")

class Client():
    def __init__(self):
        self.orderbook_ids = [0]
        self.orderbooks = []
        self._running = []
        self._lock = asyncio.Lock()
    
    def get_headers(self, path, method):
        timestamp = str(int(dt.datetime.now().timestamp() * 1000))

        headers = {
            "KALSHI-ACCESS-KEY": key_id,
            "KALSHI-ACCESS-TIMESTAMP": timestamp,
            "KALSHI-ACCESS-SIGNATURE": sign_key(path, method, timestamp),
        }
        return headers
    
    def get_portfolio(self):
        headers = self.get_headers("/trade-api/v2/portfolio/balance", "GET")

        response = requests.get(api_base + "/trade-api/v2/portfolio/balance", headers=headers)
        return response.json()
    
    def get_orderbook_snapshot(self, ticker, max_depth=None):
        if max_depth == None:
            return requests.get(f"https://api.elections.kalshi.com/trade-api/v2/markets/{ticker}/orderbook").json()
        else:
            query = {"depth":f"{max_depth}"}
            return requests.get(f"https://api.elections.kalshi.com/trade-api/v2/markets/{ticker}/orderbook", params=query).json()

    def get_positions(self):
        headers = self.get_headers("/trade-api/v2/portfolio/positions", "GET")
        return requests.get(api_base + "/trade-api/v2/portfolio/positions", headers=headers).json()

    async def book_connection(self, ticker, verbose=False):
        async with self._lock:
            self.orderbook_ids.append(self.orderbook_ids[-1]+1)
            my_id = self.orderbook_ids[-1]
            self._running.append(True)

        msg = json.dumps({
            "id": my_id,
            "cmd": "subscribe",
            "params": {
                "channels": [
                "orderbook_delta"
                ],
                "market_tickers": [ticker]
            }
        })

        headers = self.get_headers("/trade-api/ws/v2", "GET")
        
        async with cl.connect("wss://api.elections.kalshi.com/trade-api/ws/v2", extra_headers=headers) as ws:
            print(f"Connected to order book of {ticker} with id of {my_id}")
            tick = -1
            await ws.send(msg)
            occurrence = 0
            while True:
                raw = await ws.recv()
                if tick == -1:
                    tick = 0
                    pass
                elif not tick:
                    my_book = {'id': my_id, 'book': {'yes': [], 'no': []}}
                    book = json.loads(raw)
                    my_book['book']['yes'] = book['msg']['yes']
                    my_book['book']['no'] = book['msg']['no']
                    self.orderbooks.append(my_book)
                    tick = 2
                else:
                    message = json.loads(raw)
                    side = message['msg']['side']
                    price = message['msg']['price']
                    delta = message['msg']['delta']
                    for i in self.orderbooks:
                        if i['id'] == my_id:
                            found = False
                            for j, v in enumerate(i['book'][side]):
                                if v[0] == price:
                                    found = True
                                    v[1] += delta
                                    if v[1] == 0:
                                        del i['book'][side][j]
                                    break
                            if not found:
                                i['book'][side].append([price, delta])
                            break
                    occurrence += 1
                if verbose:
                    print(raw)
    
    def wrap(self, ticker):
        print("started connecting")
        asyncio.run(self.book_connection(ticker))
    
    def connect_to_book(self, ticker):
        task = threading.Thread(target=self.wrap, args=(ticker,))
        task.start()
        return task

    def menu(self):
        commands = ["-h", "start_book", "start_trade"]
        x = input("> ")
        if x == "-h":
            print(commands)
            self.menu()

    def create_order(self, action: str, side: str, ticker: str, price: int, contracts: int):
        headers = self.get_headers("/trade-api/v2/portfolio/orders", "POST")
        msg = {
            "client_order_id": str(uuid.uuid4()),
            "action": action,
            "side": side,
            "ticker": ticker,
            "count": contracts
        }
        if side == "yes":
            msg["yes_price"] = price
        elif side == "no":
            msg["no_price"] = price
        order = requests.post(api_base + "/trade-api/v2/portfolio/orders", json=msg, headers=headers).json()
        return order

    def get_queue(self, ticker):
        headers = self.get_headers("/trade-api/v2/portfolio/orders/queue_positions", "GET")
        query = {"market_tickers": [ticker]}
        url = api_base + "/trade-api/v2/portfolio/orders/queue_positions"
        response = requests.get(url, params=query, headers=headers)
        return response.json()

    async def fill_connector(self, order_ids, prices, teams):
        msg = json.dumps({
            "id": 0,
            "cmd": "subscribe",
            "params": {
                "channels": [
                "fill"
                ],
            }
        })

        headers = self.get_headers("/trade-api/ws/v2", "GET")
        async with cl.connect("wss://api.elections.kalshi.com/trade-api/ws/v2", extra_headers=headers) as ws:
            print(f"Connected to fills")
            await ws.send(msg)
            tick = -1
            initial = True
            second = False
            filled = None
            contracts = None
            while True:
                print("Awaiting")
                raw = await ws.recv()
                print(f"Raw: {raw}")
                raw = json.loads(raw)
                id = raw.get("msg").get("order_id")
                if tick == -1:
                    tick = 0
                    continue
                if initial and not second:
                    contracts = raw.get("msg").get("count")
                    if id == order_ids[0]:
                        self.cancel_order(order_ids[3])
                        filled = 0
                    elif id == order_ids[1]:
                        self.cancel_order(order_ids[2])
                        filled = 1
                    elif id == order_ids[2]:
                        self.cancel_order(order_ids[1])
                        filled = 2
                    elif id == order_ids[3]:
                        self.cancel_order(order_ids[0])
                        filled = 3
                    initial = False
                    second = True

                if (not initial) and second:
                    if filled == 0:
                        if id == order_ids[1]:
                            return
                        elif id == order_ids[2]:
                            self.create_order("sell", "yes", teams[1], prices[3], contracts)
                    elif filled == 1:
                        if id == order_ids[0]:
                            return
                        elif id == order_ids[3]:
                            self.create_order("buy", "yes", teams[1], prices[2], contracts)
                    elif filled == 2:
                        if id == order_ids[3]:
                            return
                        elif id == order_ids[0]:
                            self.create_order("sell", "yes", teams[0], prices[1], contracts)
                    elif filled == 3:
                        if id == order_ids[2]:
                            return
                        elif id == order_ids[1]:
                            self.create_order("buy", "yes", teams[0], prices[0], contracts)
                    second = False
                    return


    def fill_wrap(self, order_ids, prices, teams):
        print("started connecting")
        asyncio.run(self.fill_connector(order_ids, prices, teams))
    
    def connect_to_fills(self, order_ids, prices, teams):
        self.fill_wrap(order_ids, prices, teams)
        #task = threading.Thread(target=self.fill_wrap, args=(order_ids, prices, teams))
        #task.start()
        #return task

    def get_opposite_ticker(self, ticker):
        event = ticker.split("-")[0]
        date = ticker.split("-")[1]
        team1 = ticker.split("-")[2]
        last_date = int([i for i, v in enumerate(date) if v.isdigit()][-1])
        teams = date[last_date+1:]
        team2 = teams.replace(team1, "")
        return "-".join([event,date,team1]), "-".join([event,date,team2])

    def cancel_order(self, order_id):
        headers = self.get_headers(f"/trade-api/v2/portfolio/orders/{order_id}", "DELETE")
        order = requests.delete(api_base + f"/trade-api/v2/portfolio/orders/{order_id}", headers=headers).json()
        return order

    def main(self):
        self.menu()
    
    def start(self):
        self.main()

