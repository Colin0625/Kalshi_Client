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
    
    def get_headers(self, path):
        timestamp = str(int(dt.datetime.now().timestamp() * 1000))

        headers = {
            "KALSHI-ACCESS-KEY": key_id,
            "KALSHI-ACCESS-TIMESTAMP": timestamp,
            "KALSHI-ACCESS-SIGNATURE": sign_key(path, "GET", timestamp),
        }
        return headers
    
    def get_portfolio(self):
        headers = self.get_headers("/trade-api/v2/portfolio/balance")

        response = requests.get(api_base + "/trade-api/v2/portfolio/balance", headers=headers)
        return response.json()
    
    def get_orderbook_snapshot(self, ticker, max_depth=None):
        if max_depth == None:
            return requests.get(f"https://api.elections.kalshi.com/trade-api/v2/markets/{ticker}/orderbook").json()
        else:
            query = {"depth":f"{max_depth}"}
            return requests.get(f"https://api.elections.kalshi.com/trade-api/v2/markets/{ticker}/orderbook", params=query).json()

    def get_positions(self):
        headers = self.get_headers("/trade-api/v2/portfolio/positions")
        return requests.get(api_base + "/trade-api/v2/portfolio/positions", headers=headers).json()

    async def book_connection(self, ticker):
        self.orderbook_ids.append(self.orderbook_ids[-1]+1)
        my_id = self.orderbook_ids[-1]
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

        headers = self.get_headers("/trade-api/ws/v2")
        
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
                if occurrence == 10:
                    print(f"Orderbook {my_id} is alive")
                    occurrence = 0
    
    async def connect_to_book(self, ticker):
        print("started connecting")
        book = asyncio.create_task(client.book_connection(ticker))
        await book



client = Client()
manager = multiroutine.TaskManager()


print(client.get_portfolio())

asyncio.run(manager.add(client.connect_to_book("KXNFLGAME-25SEP18MIABUF-BUF"), "Book"))