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

#EMA--------------------------
def get_closing_graph_previous_day(num_days, company):
    vals = []
    for i in num_days:
        date_obj = datetime.datetime.strptime(i, '%Y-%m-%d')
        date_obj = date_obj - datetime.timedelta(days=1)
        while date_obj.weekday() > 4:  # 4 corresponds to Friday, so this includes Saturday and Sunday
            date_obj = date_obj - datetime.timedelta(days=1)
        last_day = date_obj.strftime('%Y-%m-%d')
        #stock --------------------
        stock = yf.Ticker(company)
        stock_data = stock.history(period="1mo", interval="1d")
        closingPrice = stock_data.loc[last_day]['Close']
        #macd = polygonclient.get_macd(ticker="AAPL", timespan="day", timestamp=i)
        #vals.append(macd.values[0])
        vals.append(closingPrice)
    #vals = [x.value for x in vals]
    return vals

def get_closing_graph_current_day(num_days, company):
    vals = []
    for i in num_days:
        stock = yf.Ticker(company)
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

#---------------------------
def xaxis(num_days):
    return num_weekdays(num_days)

def isvalidStock(company):
    if len(yf.Ticker(company).history()) == 0:
        return False
    else:
        return True

def makegraph(number, company, vals_list):
    fig = go.Figure()
    days = xaxis(number)
    #ema_data = []
    for value in vals_list:
        print(vals_list)
        vals_ema = ema_formula(int(value), get_closing_graph_previous_day(days, company), get_closing_graph_current_day(days, company), number)
        df_ema = pd.DataFrame(dict(
            Days = days,
            Value = vals_ema
        ))
        df_ema.sort_values(by="Days")
        trace_ema = go.Scatter(x=df_ema['Days'], y=df_ema['Value'], mode='lines', name='EMA ' + str(value), line=dict(color='blue'))
        fig.add_trace(trace_ema)
    """vals_ema_4 = ema_formula(4, get_closing_graph_previous_day(days, company), get_closing_graph_current_day(days, company), number)
    vals_ema_9 = ema_formula(9, get_closing_graph_previous_day(days, company), get_closing_graph_current_day(days, company), number)
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
    trace_ema_4 = go.Scatter(x=df_ema_4['Days'], y=df_ema_4['Value'], mode='lines', name='EMA 4', line=dict(color='blue'))
    trace_ema_9 = go.Scatter(x=df_ema_9['Days'], y=df_ema_9['Value'], mode='lines', name='EMA 9', line=dict(color='red'))
    fig.add_trace(trace_ema_4)
    fig.add_trace(trace_ema_9)
    """
    return fig
def getNews(company):
    comp = yf.Ticker(company)
    organized = [{'title': source['title'], 'publisher': source['publisher'], 'companies': source['relatedTickers']} for source in comp.news]
    return organized



app = Dash(__name__)
companyName = ""
currStock = False
lastVal = ""
list_of_lines = []
#---------------------------------------------------------------
@app.callback(
    Output('change-company', 'children'),
    [Input('input_val', 'value'),
     Input('dropdown', 'value')]
)

def Company(name, check):
    if check == "Stock":
        global companyName
        companyName = name
        return None

@app.callback(
    Output('news', 'children'),
    [Input('input_val', 'value'),
     Input('dropdown', 'value')]
)
def update_news_div(value, check):
    global currStock
    global lastVal
    if (check == "Stock"):
        if isvalidStock(value):
            currStock = True
            lastVal = value
            return [
                html.Div([
                    html.H2(article['title'], style={'font-size': '14px'}),
                    html.P(f"Publisher: {article['publisher']}", style={'font-size': '10px'}),
                    html.P(f"Owners: {', '.join(article['companies'])}", style={'font-size': '10px'}),
                    html.Hr()  # Add a horizontal line to separate articles
                ], style={'display': 'inline-block', 'width': '30%', 'margin-right': '2%'}) 
                for article in getNews(value)
            ]
    if (currStock == True):
        print(value)
        return [
                html.Div([
                    html.H2(article['title'], style={'font-size': '14px'}),
                    html.P(f"Publisher: {article['publisher']}", style={'font-size': '10px'}),
                    html.P(f"Owners: {', '.join(article['companies'])}", style={'font-size': '10px'}),
                    html.Hr()  # Add a horizontal line to separate articles
                ], style={'display': 'inline-block', 'width': '30%', 'margin-right': '2%'}) 
                for article in getNews(lastVal)
            ]

@app.callback(
    Output('ema', 'children'),
    [Input('input_val', 'value'),
     Input('dropdown', 'value')]
)

def update_graph(input_value, check):
    global currStock
    global lastVal
    global list_of_lines
    """if (check == "EMA"):
        if isvalidStock(input_value):
            return [dcc.Graph(
                id='winner-graph',
                figure=makegraph(5, input_value)
            )]
    """
    if (isvalidStock(input_value) and check == "Stock"):
            list_of_lines = []
    if (check == "EMA"):
        if (input_value.isdigit()):
            list_of_lines.append(input_value)
        return [dcc.Graph(
                id='winner-graph',
                figure=makegraph(5, lastVal, list_of_lines)
        )]
    if (currStock == True):
        return [dcc.Graph(
            id='winner-graph',
            figure=makegraph(5, lastVal, list_of_lines)
        )]
#---------------------------------------------------------------

app.layout = html.Div(children=[
    html.Div([
        html.H1(children='Stocks', style={'text-align': 'center'}),
    ], style={'width': '100%'}),

    html.Div([
        dcc.Input(id='input_val', value='', type='text', style={'width': '200px', 'height': '30px', 'margin': '20px'}),
        dcc.Dropdown(
            id = 'dropdown',
            options=[
                {'label': 'Stock Name', 'value': 'Stock'},
                {'label': 'Exponential Moving Average', 'value': 'EMA'},
                {'label': 'Simple Moving Average', 'value': 'SMA'},
                {'label': 'Moving Average Convergence/Divergence', 'value': 'MACD'}
            ],
            value='MTL',
            style={'width': '200px', 'height': '30px', 'margin': '10px 0px 0px 0px', 'zIndex': '1'},
        ),
    ], style={'display': 'flex', 'justify-content': 'center'}),

    html.Div(id='change-company', style={'display': 'flex', 'justify-content': 'center'}),

    html.Div([
        html.Div(id='news', style={'float': 'left', 'width': '90%'}),
        html.Div(id='ema', style={'float': 'right', 'width': '90%'})
    ], style={'display': 'grid', 'grid-template-columns': '1fr 1fr', 'gap': '10px'})
], style={'display': 'flex', 'flex-direction': 'column'})


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