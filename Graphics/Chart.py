import pandas as pd
from pandas_datareader import data as web
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import date, datetime

class Chart:
    def __init__(self, ticker, start, end, title):
        self.df = web.DataReader(name        = ticker,
                                 data_source = "yahoo",
                                 start       = start,
                                 end         = end)
        
        self.days = len(self.df.index)
        
        self.dateToPrice = {}
        for x in range(self.days):
            self.dateToPrice[self.df.index[x].strftime("%m-%d-%Y")] = self.df.Close[x]
        
        self.fig = make_subplots(shared_xaxes     = True,
                                 vertical_spacing = 0.03,
                                 subplot_titles   = ((title, "Volume")),
                                 specs            = [[{"secondary_y": True}]])
        
        self.fig.add_trace(go.Candlestick(x          = self.df.index,
                                          open       = self.df.Open,
                                          close      = self.df.Close,
                                          low        = self.df.Low,
                                          high       = self.df.High,
                                          name       = ticker,
                                          showlegend = True),
                           secondary_y = True)
        
        self.fig.update_layout(yaxis1 = {"side": "right", "showgrid": False},
                               yaxis2 = {"side": "left"});
        
    def addVolume(self):
        self.fig.add_trace(go.Bar(x      = self.df.index,
                                  y      = self.df.Volume,
                                  name   = "Daily Volume",
                                  marker = {"color": "#636EFB"}),
                           secondary_y = False)
    
    def addMovingAverage(self, days, color, name):
        self.fig.add_trace(go.Scatter(x    = self.df.index,
                                      y    = self.df.Close.rolling(window = days, min_periods = 1).mean(),
                                      mode = "lines",
                                      line = {"width": 1, "color": color},
                                      name = name),
                           secondary_y = True)
        
    def addHorizontalLine(self, value, color, name):
        self.fig.add_trace(go.Scatter(x    = self.df.index,
                                      y    = self.df.Close * 0 + value,
                                      mode = "lines",
                                      line = {"width": 1, "color": color},
                                      name = name),
                           secondary_y = True)
        
    def addTrendline(self, date1, date2, name, color, extend = 5):
        if date1 not in self.dateToPrice.keys():
            print("The start date is not a trading day! '" + name + "' will not be displayed...")
            return
        elif date2 not in self.dateToPrice.keys():
            print("The end date is not a trading day! '" + name + "' will not be displayed...")
            return
        
        diff = self.dateToPrice[date2] - self.dateToPrice[date1]
        days = (datetime.strptime(date2, "%m-%d-%Y") - datetime.strptime(date1, "%m-%d-%Y")).days
        slope = diff / days
        counter = 0
        
        leftIndex = None
        rightIndex = None
        
        arr = []
        for x in range(self.days):
            if self.df.index[x].strftime("%m-%d-%Y") == date1:
                leftIndex = x
                
            if self.df.index[x].strftime("%m-%d-%Y") == date2:
                rightIndex = x
            
            if self.df.index[x].strftime("%m-%d-%Y") >= date1 and self.df.index[x].strftime("%m-%d-%Y") <= date2:
                arr.append(self.dateToPrice[date1] + (counter * slope))
                counter += 1
            else:
                arr.append(None)

        for x in range(1, 1 + extend):
            if(leftIndex - x >= 0):
                arr[leftIndex - x] = arr[leftIndex] - (x * slope)
            if(rightIndex + x <= self.days - 1):
                arr[rightIndex + x] = arr[rightIndex] + (x * slope)
            
        self.fig.add_trace(go.Scatter(x    = self.df.index,
                                      y    = arr,
                                      mode = "lines",
                                      line = {"width": 1, "color": color},
                                      name = name),
                           secondary_y = True)
            
    def show(self):
        self.fig.show()