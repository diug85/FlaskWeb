import numpy as np
import pandas as pd
import pandas_datareader as web
import datetime
import graphs
import json
import urllib.request

pd.set_option('chained',None)

def gethistory(symbol):
    try:
        #API yahoo: S71DONYPLYY66CAV
        #API gmail: TQG5DQFV2DDMNPJN
        if symbol == "BTC":
            url = f"https://www.alphavantage.co/query?function=DIGITAL_CURRENCY_DAILY&symbol={symbol}&market=USD&apikey=TQG5DQFV2DDMNPJN"
            txt = 'Time Series (Digital Currency Daily)'
            aux1 = "a"
            aux2 = " (USD)"
        else:
            url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={symbol}&outputsize=full&apikey=TQG5DQFV2DDMNPJN"
            txt = 'Time Series (Daily)'
            aux1 = ""
            aux2 = ""

        webpage = urllib.request.urlopen(url)

        # parse JSON
        jsondata = json.loads(webpage.read())
        index = list(jsondata[txt].keys())[:780]
        index.sort()

        op = [] # Open
        hi = [] # High
        lo = [] # Low
        cl = [] # Close

        for i in range(780):    # Three years of data (260 * 3)
            op.append(float(jsondata[txt][index[i]]['1' + aux1 + '. open' + aux2]))
            hi.append(float(jsondata[txt][index[i]]['2' + aux1 + '. high' + aux2]))
            lo.append(float(jsondata[txt][index[i]]['3' + aux1 + '. low' + aux2]))
            cl.append(float(jsondata[txt][index[i]]['4' + aux1 + '. close' + aux2]))
    except:
        return None

    return pd.DataFrame(data=list(zip(op,hi,lo,cl)), index=index, columns=['open','high','low','close']).sort_index(kind='mergesort')

def CalcIndicators(ohlc):
    # PSAR
    psar = PSAR(ohlc)
    # MACD tuple
    macd, signal, hist = MACD(ohlc)
    # RSI
    rsi = RSI(ohlc)
    # ADX
    #url = 'https://www.alphavantage.co/query?function=ADX&symbol=MSFT&interval=daily&time_period=14&apikey=TQG5DQFV2DDMNPJN'
    #adx = graphs.IndicatorJson(url, 'ADX')
    # ADX
    #url = 'https://www.alphavantage.co/query?function=ADXR&symbol=MSFT&interval=daily&time_period=14&apikey=TQG5DQFV2DDMNPJN'
    #adxr = graphs.IndicatorJson(url, 'ADXR')

    diplus, diminus, adx, adxr = ADRX(ohlc)

    return psar, macd, signal, hist, rsi, adx, adxr, diplus, diminus

def PSAR(ohlc, AF=0.02, AFmax=0.2):
    ## RETURNS a pd.Series object

    #The PSAR starts always in a LARGE position with this initial arbitrary values
    n = ohlc.shape[0] # Total of historical data
    sar = np.zeros(n+1) # Has an extra space to calculate tomorrows SAR

    # The algorithm uses the first 5 days to choose an arbitrary SAR and EP
    pos = 'L' #position L=long or S=short
    sar[5] = ohlc['low'][0:5].min()
    ep = sar[5]
    accel = AF

    for day in range(5,n):
        if pos == 'L':
            #If we find a new Extreme Point (a new high)
            if ep < ohlc['high'][day]:
                ep = ohlc['high'][day]
                accel = min(AFmax, accel + AF)

            #If the reverse point has been broken, reverse to SHORT position
            if ohlc['low'][day] <= sar[day]:
                pos = 'C'
                sar[day] = ep
                ep = ohlc['low'][day]
                accel = AF
                sar[day+1] = max(ohlc['high'][day-1],ohlc['high'][day],sar[day] + accel * (ep-sar[day]))
            else:
                sar[day+1] = min(ohlc['low'][day-1],ohlc['low'][day],sar[day] + accel * (ep-sar[day]))
        else:
            #If we find a new Extreme Point (a new low)
            if ep > ohlc['low'][day]:
                ep = ohlc['low'][day]
                accel = min(AFmax, accel + AF)

            #If the reverse point has been broken, reverse to LONG position
            if ohlc['high'][day] >= sar[day]:
                pos = 'L'
                sar[day] = ep
                ep = ohlc['high'][day]
                accel = AF
                sar[day+1] = min(ohlc['low'][day-1],ohlc['low'][day],sar[day] + accel * (ep-sar[day]))
            else:
                sar[day+1] = max(ohlc['high'][day-1],ohlc['high'][day],sar[day] + accel * (ep-sar[day]))

    return pd.Series(sar, index = list(ohlc.index) + ['Tomorrow'])

def ADRX(ohlc):
    n = ohlc.shape[0] # Total of historical data
    series = pd.DataFrame(index=range(n),columns=['TR14', 'DI14_p', 'DI14_m', 'DX','ADX','ADXR'])
    global DM14_p
    global DM14_m
    global TR14
    DM14_p = 0
    DM14_m = 0
    TR14 = 0

    def CalcAux(day,mode=1):
        global DM14_p
        global DM14_m
        global TR14
        #Movement indicators
        DM1 = DirectionMove(ohlc['high'][day-1],ohlc['low'][day-1],ohlc['high'][day],ohlc['low'][day])
        DM14_p += DM1[0] - DM14_p / 14
        DM14_m += DM1[1] - DM14_m / 14
        TR14 += TrueRange(ohlc['close'][day-1],ohlc['high'][day],ohlc['low'][day]) - TR14 / 14
        #Movement Indexes
        series['TR14'][day] = TR14
        series['DI14_p'][day] = DM14_p / TR14 * 100
        series['DI14_m'][day] = DM14_m / TR14 * 100
        series['DX'][day] = abs(series['DI14_p'][day] - series['DI14_m'][day]) / (series['DI14_p'][day] + series['DI14_m'][day]) * 100

        if mode >= 2:
            #Smoothed Average of DX (ADX)
            series['ADX'][day] = (series['ADX'][day-1] * 13 + series['DX'][day]) / 14

        if mode >= 3:
            #ADXR
            series['ADXR'][day] = (series['ADX'][day]+series['ADX'][day-13])/2


    # The first 13 calculations (14 days) of +DM, -DM and TR
    for day in range(1,14):
        #Calculate the 1-day directional movement (DM1) for both directions
        DM1 = DirectionMove(ohlc['high'][day-1],ohlc['low'][day-1],ohlc['high'][day],ohlc['low'][day])
        #Acumulate to get the 14-day directional movement (DM14)
        DM14_p += DM1[0]
        DM14_m += DM1[1]
        #Acumulate of the 1-day True Range (TR1) to get the 14-day TR14
        TR14 += TrueRange(ohlc['close'][day-1],ohlc['high'][day],ohlc['low'][day])

    # First values of +DI14, -DI14 and TR14
    series['TR14'][13] = TR14
    series['DI14_p'][13] = DM14_p / TR14 * 100
    series['DI14_m'][13] = DM14_m / TR14 * 100

    # Calculate the smoothed series for +DM14, -DM14, TR14, +DI14 and -DI14
    for day in range(14,28):
        CalcAux(day)

    # First calculation for ADX
    series['ADX'][27] = sum(series['DX'][14:28])/14

    # Calculates smoothed ADX (along with the other series)
    for day in range(28,40):
        CalcAux(day,2)

    # Calculates ADXR (along with the other series)
    for day in range(40,n):
        CalcAux(day,3)

    diplus = pd.Series(data=series['DI14_p'])
    diplus.index=ohlc.index
    diminus = pd.Series(data=series['DI14_m'])
    diminus.index=ohlc.index
    adx = pd.Series(data=series['ADX'])
    adx.index=ohlc.index
    adxr = pd.Series(data=series['ADXR'])
    adxr.index=ohlc.index

    return diplus, diminus, adx, adxr

def DirectionMove(h1,l1,h2,l2):
    H = h2 - h1
    L = l1 - l2
    if H >= 0:
        if L > 0:
            if H > L:
                return (H,0)
            elif H < L:
                return (0,L)
        else:
            return (H,0)
    else:
        if L > 0:
            return (0,L)
    return (0,0)

def TrueRange(c1,h2,l2):
    return max(abs(h2-c1), abs(l2-c1), h2-l2)

def Volatility(ohlc,c=3):    # C is the constant defined in the Volatility Trading System
    n = ohlc.shape[0] # Total of historical data
    series = pd.DataFrame(index=range(n),columns=['TR','ATR7','ARC','POS','SAR'])

    #Calculation for the True Ranges (TR) and trackers for MAx and Min of close Price
    mx = ohlc['close'][0]
    mn = ohlc['close'][0]
    series['TR'][0] = ohlc['high'][0]-ohlc['low'][0]
    for day in range(1,7):
        series['TR'][day] = TrueRange(ohlc['close'][day-1],ohlc['high'][day],ohlc['low'][day])
        mx = max(mx,ohlc['close'][day])
        mn = min(mx,ohlc['close'][day])

    # Significant close for the first trade. THE ALGORITHM ASSUMES TO BE ALWAYS LONG
    pos = 'L'
    sic = mx

    #Calculation for the Average True Ranges (ATR) and ARC
    series['POS'][6] = pos
    series['ATR7'][6] = sum(series['TR'][:7])/7
    series['ARC'][6] = c * series['ATR7'][6]
    series['SAR'][6] = sic - series['ARC'][6]

    for day in range(7,n):
        series['TR'][day] = TrueRange(ohlc['close'][day-1],ohlc['high'][day],ohlc['low'][day])
        series['ATR7'][day] = (series['ATR7'][day-1]*6 + series['TR'][day])/7
        series['ARC'][day] = c * series['ATR7'][day]

        if pos == 'L':
            sic = max(sic,ohlc['close'][day])
            sar = sic - series['ARC'][day]
            if sar > ohlc['close'][day]:
                pos = 'S'
                sic = mn
                mx = ohlc['close'][day]
                mn = ohlc['close'][day]
                sar = sic + series['ARC'][day]
            series['POS'][day] = pos
            series['SAR'][day] = sar
        else:
            sic = min(sic,ohlc['close'][day])
            sar = sic + series['ARC'][day]
            if sar < ohlc['close'][day]:
                pos = 'L'
                sic = mx
                mx = ohlc['close'][day]
                mn = ohlc['close'][day]
                sar = sic - series['ARC'][day]
            series['POS'][day] = pos
            series['SAR'][day] = sar

        mx = max(mx,ohlc['close'][day])
        mn = min(mn,ohlc['close'][day])


    return series[['ATR7','POS','SAR']]

def Momentum(ohlc):
    n = ohlc.shape[0] # Total of historical data
    series = pd.DataFrame(index=range(n+1),columns=['MF','TBP','POS','StopLong','TargetLong','StopShort','TargetShort'])
    series=series.fillna(value=0.0000)
    series['POS']=""

    # Returns a tuple (Target, Stop) for both Long and Short positions
    # H2, L2 and C2 are today's high, low and close; C1 is yesterday's close
    def TargetStop(C1,H2,L2,C2):
        average = np.mean((H2,L2,C2))
        TR = TrueRange(C1,H2,L2)
        return (2*average - L2, average - TR, 2*average - H2, average + TR)

    #Calculate Momentum Factors
    series['MF'][2:-1] = np.array(ohlc['close'][2:])-np.array(ohlc['close'][:-2])
    #First trade
    i = 4
    while True:
        if series['MF'][i] < series['MF'][i-1] and series['MF'][i] < series['MF'][i-2]:
            pos = 'S'
            series['TBP'][i] = ohlc['close'][i-2] + max(series['MF'][i-2:i-1])
            break
        elif series['MF'][i] > series['MF'][i-1] or series['MF'][i] > series['MF'][i-2]:
            pos = 'L'
            series['TBP'][i] = ohlc['close'][i-2] + min(series['MF'][i-2:i-1])
            break
        else:
            i += 1
    series['POS'][i] = pos

    for day in range(i,n):
        if pos == 'L':
            if ohlc['close'][day] < series['TBP'][day]:
                pos = 'S'
                series['TBP'][day+1] = ohlc['close'][day-1] + max(series['MF'][day-1:day+1])
            else:
                series['TBP'][day+1] = ohlc['close'][day-1] + min(series['MF'][day-1:day+1])
        else:
            if ohlc['close'][day] > series['TBP'][day]:
                pos = 'L'
                series['TBP'][day+1] = ohlc['close'][day-1] + min(series['MF'][day-1:day+1])
            else:
                series['TBP'][day+1] = ohlc['close'][day-1] + max(series['MF'][day-1:day+1])
        # Today's position at today's close price
        series['POS'][day] = pos
        # Tuple for tomorrow's (Target LONG, Stop LONG, Target SHORT, Stop SHORT)
        (series['TargetLong'][day+1],series['StopLong'][day+1],series['TargetShort'][day+1], \
         series['StopShort'][day+1]) = \
        TargetStop(ohlc['close'][day-1],ohlc['high'][day],ohlc['low'][day],ohlc['close'][day])

    return series[['POS','TBP','TargetLong','StopLong','TargetShort','StopShort']]

def RSI(ohlc):
    n = ohlc.shape[0] # Total of historical data
    rsi = pd.Series(0,index=ohlc.index)

    # Differences between the close of day 'n' and day 'n-1'
    closes = np.array(ohlc['close'][1:]) - np.array(ohlc['close'][:-1])
    # Average of the UP closes for the first 14 days
    up = sum(closes[:14][closes[:14]>0])/14
    # Average of the DOWN closes for the first 14 days
    down = -sum(closes[:14][closes[:14]<0])/14
    # RSI
    rsi[14] = 100 - 100 / (1+up/down)

    for day in range(15,n):
        # Smoothed average for the UP and DOWN closes
        up = (13 * up + max(0,closes[day-1]) ) / 14
        down = (13 * down - min(0,closes[day-1]) ) / 14
        #RSI
        rsi[day] = 100 - 100 / (1+up/down)

    return rsi

def RTS(ohlc):
    H = np.array(ohlc['high'])
    L = np.array(ohlc['low'])
    X = (H+L+np.array(ohlc['close']))/3
    n = ohlc.shape[0]

    # This lis is where all the trnsactions will be loaded
    log = []

    # Indicators to enter or exit from a trade
    bp = 2*X - H
    sp = 2*X - L
    hbop = 2*X - 2*L + H
    lbop = 2*X - 2*H + L

    # This indicators are valid for the next day. We insert a zero to the begining
    # to match the index with ohlc's index
    bp = np.insert(bp,0,0)
    sp = np.insert(sp,0,0)
    hbop = np.insert(hbop,0,0)
    lbop = np.insert(lbop,0,0)

    #Vector and Dictionary to map each day into "B", "O" or "S"
    BOSvect = np.array(('o ').split()*n)
    BOSdict = {'b':'o','o':'s','s':'b'}

    #Choose the first "B" day within the first 15 days.
    indx = (L[2:15]).argmin() + 2
#    indx = 1
    BOSvect[indx-1] = 's'
    pos = 'long'
    mode = 'react'
    status = 'open'

    for day in range(indx,n):
        if day==15:
            1==1
        # Next "B", "O" or "S" day
        BOSvect[day] = BOSdict[ BOSvect[day-1] ]

        if mode == 'react':
            if day == 239:
                day=day
            if BOSvect[day] == 'b':
                # Reaction LONG
                if L[day] <= bp[day]:
                    if pos == 'short' and status == 'open':
                        status = 'close'
                        log.append((day,pos,mode,status,bp[day]))
                    pos = 'long'
                    status = 'open'
                    log.append((day,pos,mode,status,bp[day]))
                # Trend SHORT
                if L[day] <= lbop[day]:
                    if status == 'open':
                        status = 'close'
                        log.append((day,pos,mode,status,lbop[day]))
                    status = 'open'
                    pos = 'short'
                    mode = 'trend'
                    log.append((day,pos,mode,status,lbop[day]))
                    stop = max(H[day-2:day])
                # Trend LONG
                elif H[day] >= hbop[day]:
                    if status == 'open':
                        status = 'close'
                        log.append((day,pos,mode,status,hbop[day]))
                    status = 'open'
                    pos = 'long'
                    mode = 'trend'
                    log.append((day,pos,mode,status,hbop[day]))
                    stop = min(L[day-2:day])
                if pos == 'short'and mode == 'react':
                    status = 'close'
                    if H[day] >= sp[day]:
                        log.append((day,pos,mode,status,sp[day]))
                    else:
                        log.append((day,pos,mode,status,ohlc['close'][day]))
                    pos = 'none'

            elif BOSvect[day] == 'o':
                if pos == 'long' and H[day] >= sp[day] and status == 'open':
                    status = 'close'
                    log.append((day,pos,mode,status,sp[day]))
                elif H[day] >= hbop[day]:
                    if status == 'open':
                        status = 'close'
                        log.append((day,pos,mode,status,hbop[day]))
                    mode = 'trend'
                    pos = 'long'
                    status = 'open'
                    log.append((day,pos,mode,status,hbop[day]))
                    stop = min(L[day-2:day])
                elif L[day] <= lbop[day]:
                    if status == 'open':
                        status = 'close'
                        log.append((day,pos,mode,status,lbop[day]))
                    status = 'open'
                    mode = 'trend'
                    pos = 'short'
                    status = 'open'
                    log.append((day,pos,mode,status,lbop[day]))
                    stop = max(H[day-2:day])
            elif BOSvect[day] == 's':
                if H[day] >= sp[day]:
                    if status == 'open':
                        status = 'close'
                        log.append((day,pos,mode,status,sp[day]))
                    status = 'open'
                    pos = 'short'
                    log.append((day,pos,mode,status,sp[day]))
                if H[day] >= hbop[day]:
                    if status == 'open':
                        status = 'close'
                        log.append((day,pos,mode,status,hbop[day]))
                    status = 'open'
                    pos = 'long'
                    mode = 'trend'
                    log.append((day,pos,mode,status,hbop[day]))
                    stop = min(L[day-2:day])
                elif L[day] <= lbop[day]:
                    if status == 'open':
                        status = 'close'
                        log.append((day,pos,mode,status,lbop[day]))
                    status = 'open'
                    pos = 'short'
                    mode = 'trend'
                    log.append((day,pos,mode,status,lbop[day]))
                    stop = max(H[day-2:day])
                elif status == 'open' and pos == 'long':
                    status = 'close'
                    log.append((day,pos,mode,status,ohlc['close'][day]))

        #Mode == TREND
        else:
            if pos == 'long':
                stop = min(L[day-2:day])
                if L[day] <= stop:
                    status = 'close'
                    log.append((day,pos,mode,status,stop))
                    pos = 'none'
                    mode = 'react'
                    # find the max of highs for this trade
                    highest = H[log[-2][0]:day+1].argmax() + log[-2][0]
                    BOSvect[highest] = 's'
                    # Phasing
                    for d in range(highest+1,day+1):
                        BOSvect[d] = BOSdict[ BOSvect[d-1] ]
            elif pos == 'short':
                stop = max(H[day-2:day])
                if H[day] >= stop:
                    status = 'close'
                    log.append((day,pos,mode,status,stop))
                    pos = 'none'
                    mode = 'react'
                    # find the min of lows for this trade
                    lowest = L[log[-2][0]:day+1].argmin() + log[-2][0]
                    BOSvect[lowest] = 'b'
                    # Phasing
                    for d in range(lowest+1,day+1):
                        BOSvect[d] = BOSdict[ BOSvect[d-1] ]

    return (pd.DataFrame(data=[BOSvect,sp,bp,hbop,lbop]).T, log) #pd.DataFrame(data=np.array([X,bp,sp,hbop,lbop,log]).transpose())

def MACD(ohlc,Periods_MACD=(12,26),Period_signal=9):
    macd = pd.Series(ohlc.close).ewm(span=Periods_MACD[0]).mean() - pd.Series(ohlc.close).ewm(span=Periods_MACD[1]).mean()
    macd.name = "MACD"
    signal = macd.ewm(span=Period_signal).mean()
    signal.name = "Signal"
    hist = macd - signal
    hist.name = "Histogram"
    return macd, signal, hist

#if __name__ == "__main__":
#    main()
#
#Cuando ADX cruza por encima de la curva DM+ o DM- (la que sea superior) hay que
#estar atentos. Una vez que ADX la supera hay que estar atento pues UN CAMBIO DE
#TENDENCIA grande puede darse cuando 1. ADX CRUZO AMBAS CURVAS DI14 y 2. ADX PRESENTE
#EL PRIMER DECREMENTO
#
#Si ADX esta por debajo de ambos DI14 es no se debe tradear con un systema que
#siga una tendencia tendencia













