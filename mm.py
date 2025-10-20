import CustomClient as cc
import time
import threading
import asyncio

client = cc.Client()

print(client.get_portfolio())
for i in client.get_positions():
    print(i)


team1, team2 = client.get_both_tickers("KXNFLGAME-25OCT20TBDET-TB")


book0 = client.connect_to_book(team2, True)

while True:
    pass