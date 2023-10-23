from polygon import RESTClient
import config
import AlpacaTestingConfig
import json
from typing import cast
from urllib3 import HTTPResponse
from alpaca.trading.client import TradingClient
import datetime
import plotly.express as px
import pandas as pd
import yfinance as yf
from dash import Dash, html, dcc
from dash.dependencies import Input, Output
import plotly.graph_objects as go
polygonclient = RESTClient(config.API_KEY)
alpaca_trading_client = TradingClient(AlpacaTestingConfig.ALPACA_KEY, AlpacaTestingConfig.ALPACA_SECRET_KEY, paper=True)

#get current time
currentyear = datetime.datetime.now().year
currentmonth = datetime.datetime.now().month
currentday = datetime.datetime.now().day
startday = currentday - 4
def num_weekdays(num_days):
    weekdays = []
    current_date = datetime.datetime.now() - datetime.timedelta(days=1)
    count = 0

    while count < num_days:
        if current_date.weekday() < 5:
            weekdays.append(current_date.strftime('%Y-%m-%d'))
            count += 1
        current_date -= datetime.timedelta(days=1)
    return weekdays[::-1]

def get_closing_graph_previous_day(num_days):
    vals = []
    for i in num_days:
        date_obj = datetime.datetime.strptime(i, '%Y-%m-%d')
        date_obj = date_obj - datetime.timedelta(days=1)
        while date_obj.weekday() > 4:  # 4 corresponds to Friday, so this includes Saturday and Sunday
            date_obj = date_obj - datetime.timedelta(days=1)
        last_day = date_obj.strftime('%Y-%m-%d')
        #stock --------------------
        stock = yf.Ticker("AAPL")
        stock_data = stock.history(period="1mo", interval="1d")
        closingPrice = stock_data.loc[last_day]['Close']
        #macd = polygonclient.get_macd(ticker="AAPL", timespan="day", timestamp=i)
        #vals.append(macd.values[0])
        vals.append(closingPrice)
    #vals = [x.value for x in vals]
    return vals

def get_closing_graph_current_day(num_days):
    vals = []
    for i in num_days:
        stock = yf.Ticker("AAPL")
        stock_data = stock.history(period="1mo")
        closingPrice = stock_data.loc[i]['Close']
        vals.append(closingPrice)
    return vals

def ema_formula(multiplier, previous_price, current_price, days):
    vals = []
    previous_ema = previous_price[0]
    for i in range(days):
        ema = ((current_price[i] * (2/(1+multiplier))) + (previous_ema * (1-(2/(1+multiplier)))))
        vals.append(ema)
        previous_ema = ema
    return vals

def xaxis(num_days):
    return num_weekdays(num_days)


def makegraph(number):
    days = xaxis(number)
    vals_ema_4 = ema_formula(4, get_closing_graph_previous_day(days), get_closing_graph_current_day(days), number)
    vals_ema_9 = ema_formula(9, get_closing_graph_previous_day(days), get_closing_graph_current_day(days), number)
    df_ema_4 = pd.DataFrame(dict(
        Days = days,
        Value = vals_ema_4
    ))
    df_ema_9 = pd.DataFrame(dict(
        Days = days,
        Value = vals_ema_9
    ))
    df_ema_4 = df_ema_4.sort_values(by="Days")
    df_ema_9 = df_ema_9.sort_values(by="Days")
    fig = go.Figure()
    trace_ema_4 = go.Scatter(x=df_ema_4['Days'], y=df_ema_4['Value'], mode='lines', name='EMA 4', line=dict(color='blue'))
    trace_ema_9 = go.Scatter(x=df_ema_9['Days'], y=df_ema_9['Value'], mode='lines', name='EMA 9', line=dict(color='red'))
    fig.add_trace(trace_ema_4)
    fig.add_trace(trace_ema_9)
    return fig
def getNews(company):
    comp = yf.Ticker(company)
    organized = [{'title': source['title'], 'publisher': source['publisher'], 'companies': source['relatedTickers']} for source in comp.news]
    return organized



app = Dash(__name__)
companyName = ""

#---------------------------------------------------------------
@app.callback(
    Output('change-company', 'children'),
    [Input('my-input', 'value')]
)

def Company(name):
    global companyName
    companyName = name

@app.callback(
    Output('news', 'children'),
    [Input('my-input', 'value')]
)
def update_news_div(value):
    return [
        html.Div([
            html.H2(article['title'], style={'font-size': '14px'}),
            html.P(f"Publisher: {article['publisher']}", style={'font-size': '10px'}),
            html.P(f"Owners: {', '.join(article['companies'])}", style={'font-size': '10px'}),
            html.Hr()  # Add a horizontal line to separate articles
        ], style={'display': 'inline-block', 'width': '30%', 'margin-right': '2%'}) 
        for article in getNews(value)
    ]

@app.callback(
    Output('macd', 'children'),
    [Input('my-input', 'value')]
)

def update_graph(input_value):
    return dcc.Graph(
        id='stock-graph',
        figure=makegraph(5, input_value)
    )
#---------------------------------------------------------------

app.layout = html.Div(children=[
    html.Div([
        html.H1(children='Hello Dash', style={'display': 'inline-block'}),
        dcc.Input(id='my-input', value='', type='text', style={'display': 'inline-block', 'width': '200px', 'height': '30px', 'margin': '20px'}),
        html.Div(id='change-company'),
        html.Div(id = 'news')
    ], style={'display': 'flex'}),
    dcc.Graph(
        id='example-graph',
        figure=makegraph(5)
    ),
])

if __name__ == '__main__':
    app.run(debug=True)


    """html.Div([html.Div([
            html.H2(article['title'], style={'font-size': '14px'}),
            html.P(f"Publisher: {article['publisher']}", style={'font-size': '10px'}),
            html.P(f"Owners: {', '.join(article['companies'])}", style={'font-size': '10px'}),
            html.Hr()  # Add a horizontal line to separate articles
        ], style={'display': 'inline-block', 'width': '30%', 'margin-right': '2%'}) 
        for article in getNews(companyName)],
        style={'display': 'flex', 'flex-wrap': 'nowrap', 'overflow-x': 'auto'}
    ),"""


"""xd = getNews("MSFT")
df1 = pd.DataFrame(xd, columns=['title', 'publisher', 'companies'])
print(df1)"""

"""aggs = cast(
    HTTPResponse,
    polygonclient.get_aggs(
        "AAPL", 
        1, 
        "minute", 
        "2023-10-07", 
        "2023-10-08",
        raw = True
    ),
)

data = json.loads(aggs.data)"""