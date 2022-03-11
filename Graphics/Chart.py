import pandas as pd
from pandas_datareader import data as web
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import date, datetime, timedelta

class Chart:
    def __init__(self, ticker, start, end, title, chartType):
        self.df = web.DataReader(name        = ticker,
                                 data_source = "yahoo",
                                 start       = start,
                                 end         = end)
        self.ticker = ticker
        self.days = len(self.df.index)
        
        self.dates = []
        for x in self.df.index:
            self.dates.append(x.strftime("%m-%d-%Y"))
        
        self.dateToPrice = {}
        for x in range(self.days):
            self.dateToPrice[self.dates[x]] = self.df.Close[x]
        
        self.fig = make_subplots(shared_xaxes     = True,
                                 subplot_titles   = ((title, "Volume")),
                                 specs            = [[{"secondary_y": True}]])
        
        if chartType == "Candlestick":
            self.makeCandlestickChart()
        elif chartType == "Line":
            self.makeLineChart();
        
        self.fig.update_layout(yaxis1 = {"side": "right", "showgrid": False},
                               yaxis2 = {"side": "left"});

    def addClosingPrices(self):
        self.makeLineChart()
        
    def addMovingAverage(self, days, color, name):
        self.fig.add_trace(go.Scatter(x    = self.df.index,
                                      y    = self.df.Close.rolling(window = days, min_periods = 1).mean(),
                                      mode = "lines",
                                      line = {"width": 1, "color": color},
                                      name = name),
                           secondary_y = True)

    def addResistance(self, value, color, name):
        self.addSupport(value, color, name)
        
    def addSupport(self, value, color, name):
        self.fig.add_trace(go.Scatter(x    = self.df.index,
                                      y    = self.df.Close * 0 + value,
                                      mode = "lines",
                                      line = {"width": 1, "color": color},
                                      name = name),
                           secondary_y = True)

    def __addTrendlineExtend(self, arr, leftExtend, rightExtend, leftIndex, rightIndex, date1, date2, slope):
        #Extend the right side
        
        #rightDatetime is the date we want to end the extend at
        #endDatetime is the last date specified by the user upon creation of a Chart
        rightDatetime = datetime.strptime(date2, "%m-%d-%Y")
        endDatetime = datetime.strptime(list(self.dateToPrice.keys())[-1], "%m-%d-%Y")
        
        #If we want to extend past the end date, we have to append to self.dates and self.df
        if rightDatetime + timedelta(rightExtend) > endDatetime:
            excessDays = (rightDatetime + timedelta(rightExtend) - endDatetime).days
            for x in range(excessDays):
                nextDateString = datetime.strftime(endDatetime + timedelta(1 + x), "%m-%d-%Y")
                self.dates.append(nextDateString)
                self.df = self.df.append(pd.DataFrame([[None, None, None, None, None, None]],
                                                      columns = ["High", "Low", "Open", "Close", "Volume", "Adj Close"],
                                                      index = [pd.Timestamp(nextDateString)]))
        
        #Fill the rest of the values with None since we need arr and self.dates to ve the same length
        while len(arr) < len(self.dates):
            arr.append(None)

        ex = rightExtend
        numDays = 0
            
        #We must increment this to avoid a double add in arr[rightIndex]
        rightIndex += 1
        
        #While we can extend, update the trendline value
        while ex - numDays > 0:
            numDays += (datetime.strptime(self.dates[rightIndex], "%m-%d-%Y") - datetime.strptime(self.dates[rightIndex - 1], "%m-%d-%Y")).days
            arr[rightIndex] = self.dateToPrice[date2] + (numDays * slope)
            rightIndex += 1
            
        #Extend the left side
        ex = leftExtend
        numDays = 0
        
        #We must decrement this to avoid a double add in arr[leftIndex]
        leftIndex -= 1
        
        #While we can extend, update the trendline value
        while ex - numDays > 0:
            numDays += (datetime.strptime(self.dates[leftIndex + 1], "%m-%d-%Y") - datetime.strptime(self.dates[leftIndex], "%m-%d-%Y")).days
            if self.dateToPrice[date1] - (numDays * slope) < 0:
                break
            arr[leftIndex] = self.dateToPrice[date1] - (numDays * slope)
            leftIndex -= 1
        
    def addTrendline(self, date1, date2, name, color, leftExtend = 0, rightExtend = 0):
        if date1 not in self.dateToPrice.keys():
            print("The start date is not a trading day! '" + name + "' will not be displayed...")
            return
        elif date2 not in self.dateToPrice.keys():
            print("The end date is not a trading day! '" + name + "' will not be displayed...")
            return
        
        #Get the slope for the trendline
        diff = self.dateToPrice[date2] - self.dateToPrice[date1]
        days = (datetime.strptime(date2, "%m-%d-%Y") - datetime.strptime(date1, "%m-%d-%Y")).days
        slope = diff / days
        
        #Get the starting and ending index
        index = leftIndex = rightIndex = None
        for x in range(len(self.dates)):
            if self.dates[x] == date1:
                leftIndex = index = x
            elif self.dates[x] == date2:
                rightIndex = x
                break
        
        #Initialize auxilary array for the trendline and other variables to help with
        #calculating each value for the trendline
        arr = []
        prev = self.dates[index]
        d1 = date1[6:] + "-" + date1[0:5]
        d2 = date2[6:] + "-" + date2[0:5]
        counter = 0
        
        #Loop though all the days and append price following slope to create trendline
        for currentDate in self.dates:
            currentDateYMD = currentDate[6:] + "-" + currentDate[0:5]
            
            if currentDateYMD >= d1 and currentDateYMD <= d2:
                counter += (datetime.strptime(currentDate, "%m-%d-%Y") - datetime.strptime(prev, "%m-%d-%Y")).days
                arr.append(self.dateToPrice[date1] + (counter * slope))
                prev = currentDate
            else:
                arr.append(None)
                
        #If the user wishes to extend the line, call the helper function
        if leftExtend > 0 or rightExtend > 0:
            self.__addTrendlineExtend(arr, leftExtend, rightExtend, leftIndex, rightIndex, date1, date2, slope)

        #Create the chart
        self.fig.add_trace(go.Scatter(x    = self.df.index,
                                      y    = arr,
                                      mode = "lines",
                                      line = {"width": 1, "color": color},
                                      name = name),
                           secondary_y = True)
        
    def addVolume(self):
        self.fig.add_trace(go.Bar(x      = self.df.index,
                                  y      = self.df.Volume,
                                  name   = "Daily Volume",
                                  marker = {"color": "#636EFB"}),
                           secondary_y = False)
        
    def makeCandlestickChart(self):
        self.fig.add_trace(go.Candlestick(x          = self.df.index,
                                          open       = self.df.Open,
                                          close      = self.df.Close,
                                          low        = self.df.Low,
                                          high       = self.df.High,
                                          name       = self.ticker,
                                          showlegend = True),
                           secondary_y = True)
        
    def makeLineChart(self):
        self.fig.add_trace(go.Scatter(x    = self.df.index,
                                      y    = self.df.Close,
                                      mode = "lines",
                                      line = {"width": 1, "color": "black"},
                                      name = "Closing Price"),
                           secondary_y = True)
            
    def show(self):
        self.fig.show()