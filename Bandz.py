import streamlit as st
import pandas as pd
import yfinance as yf
import datetime
import pandas_ta as ta
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import backtesting
from backtesting import Backtest
from backtesting import Strategy
import bokeh

# MAINPAGE
st.set_page_config(
  page_title="Owen's Trading Window",
  page_icon=":bar_chart:",
  layout="wide"                 
)

st.title(":bar_chart: Bollinger Band Trading")
st.markdown("##")
st.header("This tool is for educational purposes only. This is not trading advice.")
st.code("Choose your stock and date range")

myStock = str(st.text_input("Enter Stock to View",
                        "AVGO",
                        key = "placeholder"
                        ))

dateStart = st.date_input("Enter Start Date", datetime.date(2014, 1, 30))

dateEnd = st.date_input("Enter End Date", datetime.date(2024, 1, 30))

st.markdown(blue-background["Adjust your Fast / Slow exponential moving average. 50- and 200-day EMAs are used as indicators for long-term trends."])

myEMA = int(st.text_input("Fast Moving Average",
                        '200',
                        key = "placeholder2"
                        ))
myEMA2 = int(st.text_input("Slow Moving Average",
                        '50',
                        key = "placeholder3"
                        ))
   
st.code("Tune your parameters for Backtesting")
myCash = st.number_input("How Much Money Are We Playing With?",
                        placeholder = "1000"
                        )

stMargin = int(st.text_input("Whats Your Margin? 1/*",
                        '5',
                        key = "placeholder4"
                        ))
myMargin = float(1 / stMargin)


# Determining if moving average is trending up or down and giving it a signal.
# 2 == Buy, 1 == Sell
def addEMAsignal(df):
    EMAsignal = [0] * len(df)
    for i in range(0, len(df)):
        if df.EMA2[i] > df.EMA[i]:
            EMAsignal[i] = 2
        elif df.EMA2[i] < df.EMA[i]:
            EMAsignal[i] = 1
    df["EMASignal"] = EMAsignal

#Testing if close is lower than the BB, and if EMA Signal is in uptrend, sends out buying signal and viceversa 
def addorderslimit(df, percent):
    ordersignal = [0] * len(df)
    for i in range(1,len(df)):
        if df.Close[i] <= df['BBL_14_2.0'][i] and df.EMASignal[i] == 2:
            ordersignal[i] = df.Close[i] - df.Close[i] * percent
        elif df.Close[i] >= df['BBU_14_2.0'][i] and df.EMASignal[i] == 1:
            ordersignal[i] = df.Close[i] - df.Close[i] * percent
        # if df.Close[i] <= df['BBL_20_2.5'][i] and df.EMASignal[i] == 2:
        #     ordersignal[i] = df.Close[i] - df.Close[i] * percent
        # elif df.Close[i] >= df['BBU_20_2.5'][i] and df.EMASignal[i] == 1:
        #     ordersignal[i] = df.Close[i] - df.Close[i] * percent
    df['ordersignal'] = ordersignal   
    
# Visualization Functions
def pointposbreak(x):
    if x['ordersignal'] != 0:
        return x['ordersignal']
    else:
        return np.nan
    
# Pulling Stock Data From Yahoo Finance
# dfStock = yf.download("^index"... For Index/ETF")
dfStock = yf.download(myStock, start = dateStart, end = dateEnd)

dfStock = dfStock[dfStock.High != dfStock.Low]
dfStock.reset_index(inplace=True)
dfStock.head()

# Calculating fast and slow moving averages and an RSI value for each day
dfStock['EMA'] = ta.ema(dfStock.Close, length = myEMA)
dfStock['EMA2'] = ta.ema(dfStock.Close, length = myEMA2)
dfStock['RSI'] = ta.rsi(dfStock.Close, length = 12)    

myBBandz = ta.bbands(dfStock.Close, length = 14, std = 2.0)

dfStock = dfStock.join(myBBandz)
dfStock.dropna(inplace = True)
dfStock.reset_index(inplace = True)
# dfStock[420:425]

# Go Button
# st.button("See Data", type = "secondary")
if st.button("Calculate Buying / Selling Signals"):
    if len(dfStock) == 0:
        st.text("Hmm, check your date ranges or stock symbol")
    else:
        addEMAsignal(dfStock)
        addorderslimit(dfStock, 0.000)

        st.code("Market Data")
        
        # dfSignal = dfStock[dfStock.ordersignal != 0] 
        st.dataframe(dfStock[dfStock.ordersignal != 0], use_container_width = True)
        # st.dataframe(myBBandz[420:425], use_container_width = True)
        # Plot Graph of Buying / Selling Signals
        # pl = st.empty()
        # scatterchart = st.plotly_chart(plotscatterchart(dfStock), them = "sreamlit", use_container_width = True)
        # pl.image(scatterchart, use_container_width = True)
        # st.pyplot(fig= plotscatterchart(dfStock), use_container_width=True)
        dfStock['pointposbreak'] = dfStock.apply(lambda row: pointposbreak(row), axis = 1)
        dfpl = dfStock[:].copy()

        fig = go.Figure(data = [go.Candlestick(x = dfpl.index,
                        open = dfpl['Open'],
                        high = dfpl['High'],
                        low = dfpl['Low'],
                        close = dfpl['Close']),
                        go.Scatter(x = dfpl.index, y = dfpl.EMA, line = dict(color = 'orange', width = 2), name = "Fast Moving Average 'EMA'"),
                        go.Scatter(x = dfpl.index, y = dfpl.EMA2, line = dict(color = 'yellow', width = 2), name = "Slow Moving Average 'EMA2'"),        
                        go.Scatter(x = dfpl.index, y = dfpl['BBL_14_2.0'], line = dict(color = 'blue', width = 1), name = "Lower Bollinger Band"),
                        go.Scatter(x = dfpl.index, y = dfpl['BBU_14_2.0'], line = dict(color = 'blue', width = 1), name = "Upper Bollinger Band")])
        fig.add_scatter(x = dfpl.index, y = dfpl['pointposbreak'], mode = "markers",
                                marker = dict(size = 6, color = "purple"),
                                name = "Signal")

        fig.update_xaxes(rangeslider_visible = False)
            # fig.update_layout(autosize = False, width = 1300, height = 600, margin = dict(l = 50, r = 50, b = 100, t = 100, pad = 4), paper_bgcolor = "lightblue")
        fig.update_layout(autosize = True, height = 700, margin = dict(l = 50, r = 50, b = 100, t = 100, pad = 4))
            # fig.show()                   
        st.plotly_chart(fig, theme = "streamlit", use_container_width = True)

        dfpl = dfStock[:].copy()
        
        def SIGNAL():
            return dfpl.ordersignal
        
        class myStrat(Strategy):
            initsize = 0.99
            mysize = initsize
            def init(self):
                super().init()
                self.signal = self.I(SIGNAL)

            def next(self):
                super().next()
                TPSLRatio = 2
                perc = 0.02

                if len(self.trades) > 0:
                    #check if trade was open for more than *10 days then closes trade
                    if self.data.index[-1] - self.trades[-1].entry_time >= 10:
                        self.trades[-1].close()
                    if self.trades[-1].is_long and self.data.RSI[-1] >= 75:
                        self.trades[-1].close()
                    elif self.trades[-1].is_short and self.data.RSI[-1] <= 25:
                        self.trades[-1].close()

                #stop-loss for when RSI is not enough to close the trade. 2 to 1 take-profit ratio for uptrend.
                if self.signal != 0 and len(self.trades) == 0 and self.data.EMASignal == 2:
                    sl1 = min(self.data.Low[-1], self.data.Low[-2]) * (1-perc)
                    tp1 = self.data.Close[-1] + (self.data.Close[-1] - sl1) * TPSLRatio
                    self.buy(sl = sl1, size = self.mysize)
                #stop-loss for downtrend
                elif self.signal != 0 and len(self.trades) == 0 and self.data.EMASignal == 1:
                    sl1 = sl1 = max(self.data.High[-1], self.data.High[-2]) * (1+ perc)
                    tp1 = self.data.Close[-1] - (sl1 - self.data.Close[-1]) * TPSLRatio
                    self.sell(sl = sl1, tp = tp1, size = self.mysize)

        # bt = Backtest(dfpl, myStrat, cash = 1000, margin = 1/5, commission = .000)
        bt = Backtest(dfpl, myStrat, cash = myCash, margin = myMargin, commission = .000)

        stat = bt.run()
        plot = bt.plot()
        st.dataframe(stat, use_container_width = True)
    
        st.bokeh_chart(plot, use_container_width = True)
        
        
        # st.pyplot(bt.plot)
        # if st.button("Run BackTest"):
        #     st.code("BackTesting Results:")
        #     st.dataframe(stat)
        

        
