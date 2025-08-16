import yfinance as yf
import plotly.graph_objects as go
from plotly.offline import plot

from datetime import date
from .stock_lists import STOCK_LIST

from pprint import pprint

from daily_checks.models import Stock,OpenPosition,Platform

row_legend = {
    -1:"Sell",
    0:"Do Nothing",
    1:"Buy",
    # Specific Codes:
    11:"Primary Trend Up",
    12:"Close is Over 15 EMA, Wait for Second Confirm",
    13:"Primary Trend is Down"
}

def make_candlestick_plot(df, stock):
    fig = go.Figure(data=[go.Candlestick(x=df.index,
                open=df['Open'],
                high=df['High'],
                low=df['Low'],
                close=df['Close'])])

    fig.add_trace(go.Scatter(x=df.index, y=df['EMA_15'], line=dict(color='green'), name='EMA 15'))
    fig.add_trace(go.Scatter(x=df.index, y=df['EMA_30'], line=dict(color='yellow'), name='EMA 30'))
    fig.add_trace(go.Scatter(x=df.index, y=df['EMA_60'], line=dict(color='red'), name='EMA 60'))

    fig.update_layout(
        title=stock,
        yaxis_title='Price',
        xaxis_title='Date',
    )
    return plot(fig, output_type='div')


stocks = {
    "STXRES":{"interval":"1wk"},
    "STXFIN":{"interval":"1wk"},
    "STXIND":{"interval":"1wk"},
    "STX40":{"interval":"1wk"},
}

def get_stocks_old(exchanges):
    stocks = {}
    for exchange in exchanges:
        if exchange in STOCK_LIST:
            for stock in STOCK_LIST[exchange]["stocks"]:
                temp_key_arr = [stock]
                if str(STOCK_LIST[exchange]["yf_suffix"]!=""):
                    temp_key_arr.append(STOCK_LIST[exchange]["yf_suffix"])
                stocks[".".join(temp_key_arr)]=STOCK_LIST[exchange]["stocks"][stock]

    
    return stocks



def get_stocks(exchanges):
    # Dictionary to hold the results
    result = {}
    for exchange in exchanges:
        platforms = Platform.objects.filter(code = exchange)
        for platform in platforms:

            temp_stocks = Stock.objects.filter(
                platform=platform
            ).exclude(
                id__in=OpenPosition.objects.filter(stock__platform=platform).values_list('stock_id', flat=True)
            )
            for stock in temp_stocks:
                temp_key_arr = [stock.code]
                if stock.exchange_prefix != "":
                    temp_key_arr.append(stock.exchange_prefix)
                result[".".join(temp_key_arr)]={
                    "interval":stock.default_interval,
                    "period":stock.default_period
                }
    
    
    return result

def lazy_trader(row,previous_code,previous_close=0):
    
    code = 0
    comment = []
    if row['EMA_30'] > row['EMA_60']:
        code=11
        comment.append("Primary Trend is up")
        if row['Close'] > row['EMA_15']:
            code = 12
            comment.append('Close is over 15 EMA')
            if previous_code == 12 and row['Close']>previous_close:
                comment.append("Buy")
                code = 1
            else:
                comment.append("Wait for second confirm")
                
    else:
        code = 13
        comment.append("Primary Trend is down")
    if row['Close'] < row['EMA_15']:
        code = -1
        comment.append('Close is below 15 EMA, SELL')
    
    return code,",".join(comment)


import requests
import certifi
import os

# def pre_process(stocks,stock):
#     session = requests.Session()
#     session.verify = certifi.where()

#     stocks[stock]["ticker"]=yf.Ticker(stock)
#     # stock_df = stocks[stock]["ticker"].history(period=stocks[stock]["period"], interval=stocks[stock]["interval"])
#     stock_df = stocks[stock]["ticker"].history(period=stocks[stock]["period"], interval=stocks[stock]["interval"], session=session)

#     stocks[stock]["history"]=stock_df

#     stock_df["EMA_15"]=stock_df['Close'].ewm(span=15, adjust=False).mean()
#     stock_df["EMA_30"]=stock_df['Close'].ewm(span=30, adjust=False).mean()
#     stock_df["EMA_60"]=stock_df['Close'].ewm(span=60, adjust=False).mean()

def pre_process(stocks, stock,session):
    # session = requests.Session()
    # session.verify = certifi.where()

    stocks[stock]["ticker"] = yf.Ticker(stock, session=session)  # <-- FIXED HERE
    stock_df = stocks[stock]["ticker"].history(
        period=stocks[stock]["period"], 
        interval=stocks[stock]["interval"]
    )

    stocks[stock]["history"] = stock_df

    stock_df["EMA_15"] = stock_df['Close'].ewm(span=15, adjust=False).mean()
    stock_df["EMA_30"] = stock_df['Close'].ewm(span=30, adjust=False).mean()
    stock_df["EMA_60"] = stock_df['Close'].ewm(span=60, adjust=False).mean()
    
def get_buys(max_count=1,exchanges = []):
    ret_obj = {
        "non_buy":{},
        "buy":{}
    }

    stocks = get_stocks(exchanges)
    session = requests.Session()
    session.verify = certifi.where()

    yf.shared._session = session
    count = 1
    for stock in stocks:
        try:
        # if True:
            pre_process(stocks,stock,session)

            stock_df = stocks[stock]["history"]

            stock_df['buy_state']=0
            stock_df['comments']=""
            previous_code = 0
            previous_close = 0
            for index, row in stock_df.iterrows():
                previous_code,stock_df.at[index,'comments'] = lazy_trader(row,previous_code,previous_close=previous_close)
                stock_df.at[index,'buy_state'] = previous_code+0
                previous_close = row["Close"]

            if int(stock_df.iloc[-1]['buy_state']) == 1:
                ret_obj['buy'][stock]={
                    "states":[
                        (stock_df.iloc[-1]['comments'],int(stock_df.iloc[-1]['buy_state'])),
                        (stock_df.iloc[-2]['comments'],int(stock_df.iloc[-2]['buy_state']))
                    ],
                    "dataframe":stock_df[-5:].to_json(orient='split'),
                    "dataframe_html":stock_df[-5:].to_html(classes="table table-responsive"),
                    "plot":make_candlestick_plot(stock_df,stock),
                    "name": stocks[stock]["ticker"].info["longName"] if "longName" in stocks[stock]["ticker"].info else stock
                }
                # stock_df.to_csv(stock+".csv",index=True)
                
                count = count + 1
                if count>max_count:
                    break
        except Exception as e:
            print(e)
    
    return ret_obj

def get_open_positions(stocks):
    ret_obj = {}
    session = requests.Session()
    session.verify = certifi.where()
    yf.shared._session = session
        
    for stock in stocks:
        try:
        # if True:
            
            pre_process(stocks,stock,session)

            stock_df = stocks[stock]["history"]

            stock_df['buy_state']=0
            stock_df['comments']=""
            previous_code = 0
            previous_close = 0
            for index, row in stock_df.iterrows():
                previous_code,stock_df.at[index,'comments'] = lazy_trader(row,previous_code,previous_close=previous_close)
                stock_df.at[index,'buy_state'] = previous_code+0
                previous_close = row["Close"]
            
            stocks[stock]["last_state"]=(stock_df.iloc[-1]['comments'],int(stock_df.iloc[-1]['buy_state']))
            stocks[stock]["history"]=stock_df.to_json(orient='split')
            ret_obj[stock]={}
            ret_obj[stock]["last_state"]=(stock_df.iloc[-1]['comments'],int(stock_df.iloc[-1]['buy_state']))
            ret_obj[stock]["name"]=stocks[stock]["name"]
            ret_obj[stock]["plot"]=make_candlestick_plot(stock_df,stock)

        except Exception as e:
            print(e)
    
    return ret_obj

# stocks = {
#         # "STXRES":{"interval":"1wk"},
#         # "STXFIN":{"interval":"1d"},
#         "STXIND":{"interval":"1wk","period":"1y"},
#         # "STX40":{"interval":"1d"},
#         "NRP":{"interval":"1d","period":"3mo"},
#         "GRT":{"interval":"1d","period":"3mo"},
#         "INL":{"interval":"1d","period":"3mo"},
#         "SBK":{"interval":"1d","period":"3mo"},
#     }


# get_buys(max_count=1,exchanges=["jse","stx"])
# get_open_positions(stocks)
