import CustomClient as cc
import time
import threading


client = cc.Client()

print(client.get_portfolio())

team1 = "KXNCAAFGAME-25OCT17UNCCAL-CAL"
team2 = "KXNCAAFGAME-25OCT17UNCCAL-UNC"

t1_quotes = []
t2_quotes = []

t = time.perf_counter()




client.connect_to_book(team1)



print("past point")
while(True):
    if time.perf_counter() - t >= 1.0:
        t = time.perf_counter()
        print(client.orderbooks[0])
