import urllib.request
import json
import pandas as pd
import plotly
#import plotly.plotly as py
import plotly.graph_objs as go

def IndicatorJson(url, indicator):
    webpage = urllib.request.urlopen(url)
    txt = 'Technical Analysis: ' + indicator
    jsondata = json.loads(webpage.read())
    index = list(jsondata[ txt ].keys())[:780]
    index.sort()
    data = pd.Series(None, index=index)

    for day in range(780):
        data[day] = float(jsondata[txt][index[day]][indicator])

    return data

def PlotSystem3(ohlc, psar, macd, signal, hist, adx, diplus, diminus):
    trace1 = go.Candlestick(x = ohlc.index,
                        open = ohlc.open,
                        high = ohlc.high,
                        low = ohlc.low,
                        close = ohlc.close,
                        increasing = dict(line = dict(color='rgba(52,169,102,1)',
                                                      width=1
                                                      ),
                                         fillcolor = 'rgba(52,169,102,0)'
                                        ),
                        decreasing = dict(line = dict(color='rgba(220,68,59,1)',
                                                      width=1
                                                      ),
                                         fillcolor = 'rgba(220,68,59,0)'
                                        ),
                        hoverinfo = 'none',
                        legendgroup = "one",
                        showlegend = False,
                        line=dict(width=0.3),
                        whiskerwidth=1,
                        yaxis='y2'
                        )
    trace2 = go.Scatter(x=psar.index,
                        y=psar.values,
                        mode='markers',
                        marker=dict(size=4,
                                    color='white',
                                    ),
                        legendgroup='one',
                        name='Parabolic SAR',
                        showlegend=True,
                        yaxis='y2'
                        )
    trace3 = go.Scatter(x=adx.index,
                        y=adx.values,
                        mode='lines',
                        legendgroup='two',
                        name='ADX',
                        showlegend=True,
                        opacity=1,
                        line=dict(color='rgba(255, 255, 255, 1)'),
                        yaxis='y1'
                        )
    trace4 = go.Scatter(x=diplus.index,
                        y=diplus.values,
                        mode='lines',
                        legendgroup='two',
                        name='DMI+',
                        showlegend=True,
                        opacity=1,
                        line=dict(color='rgba(39, 68, 175,1)',
                                  width=1),
                        yaxis='y1'
                        )
    trace5 = go.Scatter(x=diminus.index,
                        y=diminus.values,
                        mode='lines',
                        legendgroup='two',
                        name='DMI-',
                        showlegend=True,
                        opacity=1,
                        line=dict(color='red',
                                  width=1),
                        yaxis='y1'
                        )
    trace6 = go.Scatter(x=[min(ohlc.index), max(ohlc.index)],
                        y=[25,25],
                        mode='lines',
                        showlegend=False,
                        legendgroup='two',
                        opacity=1,
                        line=dict(color='green',
                                  width=1,
                                  dash='dot'),
                        yaxis='y1'
                        )
    trace7 = go.Scatter(x=macd.index,
                        y=macd.values,
                        mode='lines',
                        legendgroup='three',
                        name='MACD',
                        showlegend=True,
                        opacity=1,
                        line=dict(color='rgba(255, 255, 255,1)',
                                  width=1),
                        yaxis='y3'
                        )
    trace8 = go.Scatter(x=signal.index,
                        y=signal.values,
                        mode='lines',
                        legendgroup='three',
                        name='Signal',
                        showlegend=True,
                        opacity=1,
                        line=dict(color='rgba(39, 68, 175,1)',
                                  width=2),
                        yaxis='y3'
                        )
    trace9 = go.Bar(x=hist.index,
                    y=hist.values,
                    marker=dict(color='rgba(214,14,14,1)',
                                line=dict(color='rgba(214,14,14,0.5)',
                                          width=1
                                          )
                                ),
                    name='Histogram',
                    showlegend=True,
                    legendgroup='three',
                    yaxis='y3'
                    )
    layout = go.Layout(autosize = True,
                       #width = 1500,
                       height = 500,
                       legend=dict(orientation="h",
                                   font=dict(color='rgba(200,200,200, 1)')
                                   ),
                       paper_bgcolor='rgba(37,37,37,1)',
                       plot_bgcolor='rgba(37,37,37,1)',
                       xaxis = dict(
                               rangeselector = dict(
                                               buttons=list([
                                                        dict(count=3,
                                                             label='3m',
                                                             step='month',
                                                             stepmode='backward'),
                                                        dict(count=6,
                                                             label='6m',
                                                             step='month',
                                                             stepmode='backward'),
                                                        dict(count=1,
                                                            label='YTD',
                                                            step='year',
                                                            stepmode='todate'),
                                                        dict(count=1,
                                                            label='1y',
                                                            step='year',
                                                            stepmode='backward')
                                                        ])
                                               ),

                                rangeslider=dict(visible=False),
                                range=[ohlc.index[-260],ohlc.index[-1]],
                                tickfont = dict(color='white'),
                                linewidth=1,
                                linecolor = 'rgba(255,255,255,1)',
                                mirror = "all"
                               ),
                        yaxis = dict(
                                    title = 'DMI',
                                    titlefont = dict(color='rgba(200,115,115,1)'),
                                    autorange = False,
                                    range=[0, max(adx.values[-520:])],
                                    domain = [0,0.2],
                                    tickfont = dict(color='white'),
                                    linewidth=1,
                                    linecolor = 'rgba(255,255,255,1)',
                                    mirror = True
                                    ),
                        yaxis2 = dict(
                                      title = 'PSAR',
                                      titlefont = dict(color='rgba(200,115,115,1)'),
                                      autorange=True,
                                      domain = [0.22,0.7],
                                      tickfont = dict(color='white'),
                                      linewidth=1,
                                      linecolor = 'rgba(255,255,255,1)',
                                      mirror = True
                                      ),
                        yaxis3 = dict(
                                      title = 'MACD',
                                      titlefont = dict(color='rgba(200,115,115,1)'),
                                      autorange=True,
                                      domain = [0.72,1],
                                      tickfont = dict(color='white'),
                                      linewidth=1,
                                      linecolor = 'rgba(255,255,255,1)',
                                      mirror =True
                                      ),
                        margin = dict(l=60,
                                      r=20,
                                      t=30,
                                      b=5
                                      )
                       )
    # Give correct format to all traces
    tab = [trace1, trace2, trace3, trace4, trace5, trace6, trace7, trace8, trace9]
    # Create figure to plot
    figure = go.Figure(data=tab, layout=layout)
    #Plot
    return plotly.offline.plot(figure, output_type="div", show_link=False, link_text=False)

def PlotSystem2(ohlc, rsi, adx, adxr, wma1=5, wma2=12):
    trace1 = go.Candlestick(x = ohlc.index,
                        open = ohlc.open,
                        high = ohlc.high,
                        low = ohlc.low,
                        close = ohlc.close,
                        increasing = dict(line = dict(color='rgba(52,169,102,1)',
                                                      width=1
                                                      ),
                                         fillcolor = 'rgba(52,169,102,0)'
                                        ),
                        decreasing = dict(line = dict(color='rgba(220,68,59,1)',
                                                      width=1
                                                      ),
                                         fillcolor = 'rgba(220,68,59,0)'
                                        ),
                        hoverinfo = 'none',
                        legendgroup = "two",
                        showlegend = False,
                        line=dict(width=0.3),
                        whiskerwidth=1,
                        yaxis='y2'
                        )
    trace2 = go.Scatter(x=ohlc.index,
                        y=pd.Series(ohlc.close).ewm(span=wma1).mean(),
                        mode='lines',
                        legendgroup='two',
                        name='WMA(' + str(wma1) + ')',
                        showlegend=True,
                        opacity=1,
                        line=dict(color='red'),
                        yaxis='y2'
                        )
    trace3 = go.Scatter(x=ohlc.index,
                        y=pd.Series(ohlc.close).ewm(span=wma2).mean(),
                        mode='lines',
                        legendgroup='two',
                        name='WMA(' + str(wma2) + ')',
                        showlegend=True,
                        opacity=1,
                        line=dict(color='rgba(39, 68, 175,1)'),
                        yaxis='y2'
                        )
    trace4 = go.Scatter(x=rsi.index,
                        y=rsi.values,
                        mode='lines',
                        legendgroup='one',
                        name='Relative Strength Index',
                        showlegend=True,
                        opacity=1,
                        line=dict(color='rgba(255, 255, 255, 1)'),
                        yaxis='y3'
                        )
    trace5 = go.Scatter(x=[min(ohlc.index), max(ohlc.index)],
                        y=[30,30],
                        mode='lines',
                        showlegend=False,
                        legendgroup='three',
                        opacity=0.8,
                        line=dict(color='green',
                                  width=1,
                                  dash='dot'),
                        yaxis='y3'
                        )
    trace6 = go.Scatter(x=[min(ohlc.index), max(ohlc.index)],
                        y=[50,50],
                        mode='lines',
                        showlegend=False,
                        legendgroup='three',
                        opacity=0.5,
                        line=dict(color='white',
                                  width=1,
                                  dash='dot'),
                        yaxis='y3'
                        )
    trace7 = go.Scatter(x=[min(ohlc.index), max(ohlc.index)],
                        y=[70,70],
                        mode='lines',
                        showlegend=False,
                        legendgroup='three',
                        opacity=0.8,
                        line=dict(color='green',
                                  width=1,
                                  dash='dot'),
                        yaxis='y3'
                        )
    trace8 = go.Scatter(x=adx.index,
                        y=adx.values,
                        mode='lines',
                        legendgroup='three',
                        name='ADX',
                        showlegend=True,
                        opacity=1,
                        line=dict(color='rgba(110, 182, 202, 1)'),
                        yaxis='y1'
                        )
    trace9 = go.Scatter(x=adxr.index,
                        y=adxr.values,
                        mode='lines',
                        legendgroup='three',
                        name='ADXR',
                        showlegend=True,
                        opacity=1,
                        line=dict(color='rgba(255, 255, 255, 0.65)'),
                        yaxis='y1'
                        )
    trace10 = go.Scatter(x=[min(ohlc.index), max(ohlc.index)],
                        y=[25,25],
                        mode='lines',
                        showlegend=False,
                        legendgroup='three',
                        opacity=1,
                        line=dict(color='green',
                                  width=1,
                                  dash='dot'),
                        yaxis='y1'
                        )
    layout = go.Layout(#autosize = True,
                       #width = 1500,
                       #height = 800,
                       legend=dict(orientation="h",
                                   font=dict(color='rgba(255, 255, 255, 1)')
                                   ),
                       paper_bgcolor='rgba(37,37,37,1)',
                       plot_bgcolor='rgba(37,37,37,1)',
                       xaxis = dict(
                               rangeselector = dict(
                                               buttons=list([
                                                        dict(count=3,
                                                             label='3m',
                                                             step='month',
                                                             stepmode='backward'),
                                                        dict(count=6,
                                                             label='6m',
                                                             step='month',
                                                             stepmode='backward'),
                                                        dict(count=1,
                                                            label='YTD',
                                                            step='year',
                                                            stepmode='todate'),
                                                        dict(count=1,
                                                            label='1y',
                                                            step='year',
                                                            stepmode='backward')
                                                        ])
                                               ),

                                rangeslider=dict(visible=False),
                                range=[ohlc.index[-260],ohlc.index[-1]],
                                tickfont = dict(color='rgba(200,200,200,1)'),
                                linewidth=1,
                                linecolor = 'rgba(255,255,255,1)',
                                mirror = "all"
                               ),
                        yaxis = dict(
                                    title = 'ADXR',
                                    titlefont = dict(color='rgba(200,115,115,1)'),
                                    autorange = False,
                                    range=[0, max(adx.values[-520:])],
                                    domain = [0,0.2],
                                    tickfont = dict(color='rgba(200,200,200,1)'),
                                    linewidth=1,
                                    linecolor = 'rgba(255,255,255,1)',
                                    mirror = "all"
                                    ),
                        yaxis2 = dict(
                                      title = 'M Avg',
                                      titlefont = dict(color='rgba(200,115,115,1)'),
                                      autorange=True,
                                      domain = [0.23,0.7],
                                      tickfont = dict(color='rgba(200,200,200,1)'),
                                      linewidth=1,
                                      linecolor = 'rgba(255,255,255,1)',
                                      mirror = "all"
                                      ),
                        yaxis3 = dict(
                                      title = 'RSI',
                                      titlefont = dict(color='rgba(200,115,115,1)'),
                                      autorange=True,
                                      domain = [0.73,1],
                                      tickfont = dict(color='rgba(200,200,200,1)'),
                                      linewidth=1,
                                      linecolor = 'rgba(255,255,255,1)',
                                      mirror = "all"
                                      ),
                        margin = dict(l=60,
                                      r=20,
                                      t=30,
                                      b=5
                                      )
                       )
    # Give correct format to all traces
    tab = [trace1, trace2,trace3,trace4,trace5,trace6,trace7,trace8,trace9,trace10]
    # Create figure to plot
    figure = go.Figure(data=tab, layout=layout)
    #Plot
    return plotly.offline.plot(figure, output_type="div", show_link=False, link_text=False)

def PlotSystem1(ohlc, psar, adx, adxr, wma1=20, wma2=40):
    trace1 = go.Candlestick(x = ohlc.index,
                        open = ohlc.open,
                        high = ohlc.high,
                        low = ohlc.low,
                        close = ohlc.close,
                        increasing = dict(line = dict(color='rgba(52,169,102,1)'),
                                         fillcolor = 'rgba(52,169,102,1)'
                                        ),
                        decreasing = dict(line = dict(color='rgba(220,68,59,1)'),
                                         fillcolor = 'rgba(220,68,59,1)'
                                        ),
                        hoverinfo = 'none',
                        legendgroup = "one",
                        showlegend = False,
                        line=dict(width=0.3),
                        whiskerwidth=1,
                        yaxis='y2'
                        )
    trace2 = go.Scatter(x=psar.index,
                        y=psar.values,
                        mode='markers',
                        marker=dict(size=4,
                                    color='white',
                                    ),
                        legendgroup='one',
                        name='Parabolic SAR',
                        showlegend=True,
                        yaxis='y2'
                        )
    trace3 = go.Scatter(x=ohlc.index,
                        y=pd.Series(ohlc.close).ewm(span=wma1).mean(),
                        mode='lines',
                        legendgroup='two',
                        name='WMA(' + str(wma1) + ')',
                        showlegend=True,
                        opacity=0.6,
                        line=dict(color='red'),
                        yaxis='y2'
                        )
    trace4 = go.Scatter(x=ohlc.index,
                        y=pd.Series(ohlc.close).ewm(span=wma2).mean(),
                        mode='lines',
                        legendgroup='two',
                        name='WMA(' + str(wma2) + ')',
                        showlegend=True,
                        opacity=0.6,
                        line=dict(color='rgba(39, 68, 175,125)'),
                        yaxis='y2'
                        )
    trace5 = go.Scatter(x=adx.index,
                        y=adx.values,
                        mode='lines',
                        legendgroup='three',
                        name='ADX',
                        showlegend=True,
                        opacity=1,
                        line=dict(color='rgba(110, 182, 202, 1)'),
                        yaxis='y1'
                        )
    trace6 = go.Scatter(x=adxr.index,
                        y=adxr.values,
                        mode='lines',
                        legendgroup='three',
                        name='ADXR',
                        showlegend=True,
                        opacity=1,
                        line=dict(color='rgba(255, 255, 255, 0.65)'),
                        yaxis='y1'
                        )
    trace7 = go.Scatter(x=[min(ohlc.index), max(ohlc.index)],
                        y=[25,25],
                        mode='lines',
                        showlegend=False,
                        legendgroup='three',
                        opacity=1,
                        line=dict(color='green',
                                  width=1,
                                  dash='dot'),
                        yaxis='y1'
                        )
    layout = go.Layout(#autosize = True,
                       #width = 1500,
                       #height = 800,
                       legend=dict(orientation="h",
                                   font=dict(color='rgba(255, 255, 255, 1)')
                                   ),
                       paper_bgcolor='rgba(37,37,37,1)',
                       plot_bgcolor='rgba(37,37,37,1)',
                       xaxis = dict(
                               rangeselector = dict(
                                               buttons=list([
                                                        dict(count=3,
                                                             label='3m',
                                                             step='month',
                                                             stepmode='backward'),
                                                        dict(count=6,
                                                             label='6m',
                                                             step='month',
                                                             stepmode='backward'),
                                                        dict(count=1,
                                                            label='YTD',
                                                            step='year',
                                                            stepmode='todate'),
                                                        dict(count=1,
                                                            label='1y',
                                                            step='year',
                                                            stepmode='backward')
                                                        ])
                                               ),

                                rangeslider=dict(visible=False),
                                range=[ohlc.index[-260],ohlc.index[-1]],
                                tickfont = dict(color='rgba(200,200,200,1)'),
                                linewidth=1,
                                linecolor = 'rgba(255,255,255,1)',
                                mirror = "all"
                               ),
                        yaxis = dict(
                                    title = 'PSAR & M Avg',
                                    titlefont = dict(color='rgba(200,115,115,1)'),
                                    autorange = False,
                                    range=[0, max(adxr.values[-520:])],
                                    domain = [0,0.25],
                                    tickfont = dict(color='rgba(200,200,200,1)'),
                                    linewidth=1,
                                    linecolor = 'rgba(255,255,255,1)',
                                    mirror = "all"
                                    ),
                        yaxis2 = dict(
                                      title = 'ADXR',
                                      titlefont = dict(color='rgba(200,115,115,1)'),
                                      autorange=True,
                                      domain = [0.30,1],
                                      tickfont = dict(color='rgba(200,200,200,1)'),
                                      linewidth=1,
                                      linecolor = 'rgba(255,255,255,1)',
                                      mirror = "all"
                                      ),
                        margin = dict(l=60,
                                      r=20,
                                      t=30,
                                      b=5
                                      )
                       )
    # Give correct format to all traces
    tab = [trace1, trace2,trace3,trace4,trace5,trace6,trace7]
    # Create figure to plot
    figure = go.Figure(data=tab, layout=layout)
    #Plot
    return plotly.offline.plot(figure, output_type="div", show_link=False, link_text=False)