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

    def __addTrendlineExtend(self, arr, extend, leftIndex, rightIndex, date1, date2, slope):
        #Do right side here first
        #If extend past right limit, add more indices with value 'None'? Use timedelta!
        ex = extend
        counter = 0
        
        #Able to use timedelta to get the next day. Just append 'None' to self.df.index
        #and continue appending to arr to add on to the trendline
        date = datetime.strptime(date2, "%m-%d-%Y")
        
        #print(self.df.index)
        #Only if date2 + extend in not in range of specified dates
        #print(datetime.strftime(date + timedelta(extend), "%m-%d-%Y"))
        #print(self.dateToPrice.keys())
        
        #If last date of range + extend is out of range, then we may need to append some indices
        #Make sure to only append the number of days that we need remaining, and not just the extend value
        
        if date + timedelta(extend) > datetime.strptime(list(self.dateToPrice.keys())[-1], "%m-%d-%Y"):
            excessDays = (date + timedelta(extend) - datetime.strptime(list(self.dateToPrice.keys())[-1], "%m-%d-%Y")).days
            print(self.df.index)
            for x in range(excessDays):
                #print(self.df)
                #print(type(self.df.index[0]))
                #print(self.df.index[0])
                #Figure out how to append here!
                #print(type(pd.Timestamp(datetime.strftime(date + timedelta(1 + x), "%m-%d-%Y"))))
                #print(pd.Timestamp(datetime.strftime(date + timedelta(1 + x), "%m-%d-%Y")))
                #self.df.index.append(pd.Timestamp(datetime.strftime(date + timedelta(1 + x), "%m-%d-%Y")))
                #self.df = self.df.append({pd.Timestamp(datetime.strftime(date + timedelta(1 + x), "%m-%d-%Y")): {None}}, ignore_index=False)
                self.df.index.append(pd.Index([pd.Timestamp(datetime.strftime(date + timedelta(1 + x), "%m-%d-%Y"))]))
                print(len(self.df.index))
            print(self.df.index)
            
        #Make sure to only take year, month, day, and not time
        #print(date + timedelta(days = 1))
        
        while ex > 0 and rightIndex < len(self.dates):
            numDays = (datetime.strptime(self.dates[rightIndex], "%m-%d-%Y") - datetime.strptime(self.dates[rightIndex - 1], "%m-%d-%Y")).days
            counter += numDays
            arr[rightIndex] = self.dateToPrice[date2] + (counter * slope)
            ex -= numDays
            rightIndex += 1
            
        #Now do the left side!
        ex = extend
        counter = 0
        
        while ex > 0 and leftIndex - 1 >= 0:
            numDays = (datetime.strptime(self.dates[leftIndex + 1], "%m-%d-%Y") - datetime.strptime(self.dates[leftIndex], "%m-%d-%Y")).days
            counter += numDays
            if self.dateToPrice[date1] - (counter * slope) < 0:
                break
            arr[leftIndex] = self.dateToPrice[date1] - (counter * slope)
            ex -= numDays
            leftIndex -= 1
        
    def addTrendline(self, date1, date2, name, color, extend = 5):
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
        counter = 0
        
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
        
        #Loop though all the days (change to just start and end index?) and append next value
        #to create trendline
        for x in range(self.days):
            currentDate = self.dates[x]
            currentDateYMD = currentDate[6:] + "-" + currentDate[0:5]
            
            if currentDateYMD >= d1 and currentDateYMD <= d2:
                counter += (datetime.strptime(currentDate, "%m-%d-%Y") - datetime.strptime(prev, "%m-%d-%Y")).days
                arr.append(self.dateToPrice[date1] + (counter * slope))
                prev = currentDate
            else:
                arr.append(None)
                
        if extend > 0:
            self.__addTrendlineExtend(arr, extend, leftIndex, rightIndex, date1, date2, slope)
            
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