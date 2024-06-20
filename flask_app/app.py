from flask import Flask
from yahoo_fin import get_open_positions,get_buys
from stock_lists import STOCK_LIST

app = Flask(__name__)

@app.route('/')
def hello():
    return "Hello, Home Assistant!"

if __name__ == '__main__':
    app.run(host='0.0.0.0')