import yfinance as yf
import mplfinance as mpf

from datetime import date

import csv


row_legend = {
    -1:"Sell",
    0:"Do Nothing",
    1:"Buy",
    # Specific Codes:
    11:"Primary Trend Up",
    12:"Close is Over 15 EMA, Wait for Second Confirm",
    13:"Primary Trend is Down"
}


stocks = {
    "STXRES":{"interval":"1wk"},
    "STXFIN":{"interval":"1wk"},
    "STXIND":{"interval":"1wk"},
    "STX40":{"interval":"1wk"},
}

def get_stocks(stocks,file,interval="1d",period="3mo"):
    with open(file, mode='r') as file:
        reader = csv.reader(file)
        next(reader)  # Skip the header row
        for row in reader:
            stocks[row[0].split(":")[-1]]={"interval":interval,"period":period}




def lazy_trader(row,previous_code):
    
    code = 0
    comment = []
    if row['EMA_30'] > row['EMA_60']:
        code=11
        comment.append("Primary Trend is up")
        if row['Close'] > row['EMA_15']:
            code = 12
            comment.append('Close is over 15 EMA')
            if previous_code == 12:
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


def make_figure(df,stock):
    ema_lines = [
        mpf.make_addplot(df['EMA_15'], color='blue', width=0.75, label='EMA 15'),
        mpf.make_addplot(df['EMA_30'], color='green', width=0.75, label='EMA 30'),
        mpf.make_addplot(df['EMA_60'], color='red', width=0.75, label='EMA 60')
    ]
    
    fig, axlist = mpf.plot(
        df, 
        type='candle', 
        style='charles', 
        addplot=ema_lines, 
        volume=True, 
        title=stock, 
        ylabel='Price', 
        savefig={'fname': stock, 'dpi': 300, 'bbox_inches': 'tight'}, 
        returnfig=True
    )


    # Customize legend
    for ax in axlist:
        handles, labels = ax.get_legend_handles_labels()
        if handles:
            ax.legend(loc='lower left')

    # Save the figure
    fig.savefig(stock+str(date.today()), dpi=300, bbox_inches='tight')

def pre_process(stocks,stock):
    stocks[stock]["ticker"]=yf.Ticker(stock+".JO")
    stock_df = stocks[stock]["ticker"].history(period=stocks[stock]["period"], interval=stocks[stock]["interval"])

    stocks[stock]["history"]=stock_df

    stock_df["EMA_15"]=stock_df['Close'].ewm(span=15, adjust=False).mean()
    stock_df["EMA_30"]=stock_df['Close'].ewm(span=30, adjust=False).mean()
    stock_df["EMA_60"]=stock_df['Close'].ewm(span=60, adjust=False).mean()
    


def main(max_count=1):
    stocks = {
        # "STXRES":{"interval":"1wk"},
        # "STXFIN":{"interval":"1wk"},
        # "STXIND":{"interval":"1wk"},
        # "STX40":{"interval":"1wk"},
    }
    # Load JSE full list
    get_stocks(stocks,"companies-list.csv",interval="1d")

    count = 1
    for stock in stocks:
        try:
        # if True:
            print(stock)
            
            pre_process(stocks,stock)

            stock_df = stocks[stock]["history"]

            stock_df['buy_state']=0
            stock_df['comments']=""
            previous_code = 0
            for index, row in stock_df.iterrows():
                previous_code,stock_df.at[index,'comments'] = lazy_trader(row,previous_code)
                stock_df.at[index,'buy_state'] = previous_code+0

            if stock_df.iloc[-1]['buy_state'] == 1:
                print(stock_df.iloc[-1]['buy_state'])
                print(stock_df.iloc[-1]['comments'])
                print(stock_df.iloc[-2]['buy_state'])
                print(stock_df.iloc[-2]['comments'])
                stock_df.to_csv(stock+".csv",index=True)
                make_figure(df=stock_df,stock=stock)

            

                count = count + 1
                if count>max_count:
                    break
        except Exception as e:
            print(e)
# main()

def get_open_positions():
    stocks = {
        # "STXRES":{"interval":"1wk"},
        # "STXFIN":{"interval":"1d"},
        "STXIND":{"interval":"1wk","period":"1y"},
        # "STX40":{"interval":"1d"},
        "NRP":{"interval":"1d","period":"3mo"},
        "GRT":{"interval":"1d","period":"3mo"},
        "INL":{"interval":"1d","period":"3mo"},
        "SBK":{"interval":"1d","period":"3mo"},
    }
    
    for stock in stocks:
        try:
        # if True:
            print(stock)
            pre_process(stocks,stock)

            stock_df = stocks[stock]["history"]

            stock_df['buy_state']=0
            stock_df['comments']=""
            previous_code = 0
            for index, row in stock_df.iterrows():
                previous_code,stock_df.at[index,'comments'] = lazy_trader(row,previous_code)
                stock_df.at[index,'buy_state'] = previous_code+0

            print(stock_df.iloc[-1]['buy_state'])
            print(stock_df.iloc[-1]['comments'])

            make_figure(df=stock_df,stock=stock)
        except Exception as e:
            print(e)

# main()
get_open_positions()
print("done")