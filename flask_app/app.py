from flask import Flask
from yahoo_fin import get_open_positions,get_buys


app = Flask(__name__)

@app.route('/')
def hello():
    open_posistions = {
            # "STXRES":{"interval":"1wk"},
            # "STXFIN":{"interval":"1d"},
            "STXIND.JO":{"interval":"1wk","period":"1y"},
            # "STX40":{"interval":"1d"},
            # "NRP.JO":{"interval":"1d","period":"3mo"},
            "GRT.JO":{"interval":"1d","period":"3mo"},
            "INL.JO":{"interval":"1d","period":"3mo"},
            "SBK.JO":{"interval":"1d","period":"3mo"},
            "FSR.JO":{"interval":"1d","period":"3mo"},
        }


    buys = get_buys(max_count=1,exchanges=["jse","stx"])
    # buys = {}
    ret_open = get_open_positions(open_posistions)

    # stock_df.to_csv(stock+".csv",index=True)

    return {"buys":buys,"open_positions":ret_open}

if __name__ == '__main__':
    app.run(host='0.0.0.0',port=5001)