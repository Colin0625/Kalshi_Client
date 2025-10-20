import CustomClient as cc
import time
import threading

client = cc.Client()

print(client.get_portfolio())

team1 = "KXEPLGAME-25OCT20WHUBRE-BRE"
team2 = client.get_opposite_ticker(team1)

print(input())
