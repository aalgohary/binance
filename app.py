from flask import Flask, render_template, request, jsonify
import requests
import hashlib
import hmac
import time
import json
import pandas as pd
import math
import seaborn as sns
import matplotlib.pyplot as plt

app = Flask(__name__)

p_trade_data = {}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/retrieve-data', methods=['POST'])
def retrieve_data():
    # Manual Input
    ## Start day of the month (Day of subscription)
    start_day_of_the_month = int(request.json.get('startDay'))
    
    # Capital Per Month
    capital_per_month = {}
    capitalPerMonth = request.json.get('capitalPerMonth').split(',')
    for i in range(len(capitalPerMonth)):
        key = int(capitalPerMonth[i].strip().split(':')[0])
        value = float(capitalPerMonth[i].strip().split(':')[1])
        capital_per_month[key] = value

    ## Binance Data
    # Get the API keys and secrets from the request      
    base_url = 'https://api.binance.com'
    trades_endpoint = '/api/v3/myTrades'

    api_keys = request.json.get('apiKeys').split(',')
    api_secrets = request.json.get('apiSecrets').split(',')

    ## Binance Symbols             
    symbols = ['BTCUSDT', 'ETHUSDT', 'LTCUSDT', 'QTUMUSDT', 'DOCKUSDT', 'AVAXUSDT', 'FETUSDT', 'DGBUSDT',
               'ANTUSDT', 'DASHUSDT', 'ARPAUSDT', 'AVAUSDT', 'HBARUSDT', 'PUNDIXUSDT', 'VTHOUSDT', 'CHRUSDT',
               'OCEANUSDT', 'ETCUSDT', 'GLMRUSDT', 'OGNUSDT', 'GRTUSDT', 'SKLUSDT', 'BLZUSDT', 'API3USDT',
               'QNTUSDT', 'TFUELUSDT', 'EOSUSDT', 'IOSTUSDT', 'JASMYUSDT']

    # Functions
    def generate_signature(query_string, api_secret):
        return hmac.new(api_secret.encode('utf-8'), query_string.encode('utf-8'), hashlib.sha256).hexdigest()

    # API Call Params
    params = {
        'timestamp': int(time.time() * 1000),
        'recvWindow': 60000,
    }

    # Perform the necessary operations with the API keys and secrets
    trades_data = []

    for i, symbol in enumerate(symbols):
        current_api_key = api_keys[i % len(api_keys)].strip()
        current_api_secret = api_secrets[i % len(api_secrets)].strip()

        params['symbol'] = symbol
        query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
        signature = generate_signature(query_string, current_api_secret)
        query_string += f'&signature={signature}'

        headers = {
            'X-MBX-APIKEY': current_api_key
        }

        trades_url = f"{base_url}{trades_endpoint}?{query_string}"
        response = requests.get(trades_url, headers=headers)

        if response.status_code == 200:
            trades = response.json()

            if trades:  # Check if the response contains valid trade data
                trades_data.extend(trades)
        else:
            return jsonify({'error': f"Error for {symbol}: {response.status_code} {response.text}"}), 500

    # Convert trade data to dataframe
    df = pd.DataFrame(trades_data)
    
    # Convert string columns to numeric
    df[['price', 'qty', 'quoteQty']] = df[['price', 'qty', 'quoteQty']].apply(pd.to_numeric)

    # Add new columns
    df['Commission'] = df['quoteQty'].apply(lambda x: x / 1000)
    df['Date'] = pd.to_datetime(df['time'], unit='ms')
    df['Type'] = df['isBuyer'].apply(lambda x: 'Buy' if x else 'Sell')
    df['Role'] = df['isMaker'].apply(lambda x: 'Maker' if x else 'Taker')
    df['TypeMarketDate'] = df['Type']+df['symbol']+df['Date'].dt.strftime('%Y-%m-%d %H:%M:%S')
    
    # Define column renaming
    column_renaming = {
        'quoteQty': 'Total',
        'symbol': 'Market',
        'price': 'Price',
        'qty': 'Amount' 
    }

    # Apply column renaming
    df.rename(columns=column_renaming, inplace=True)

    # Create AvgBuyPrice column
    ## Group by 'TypeMarketDate' and calculate average price for 'BUY' types
    avgbuy4buy = df[df['Type'] == 'Buy'][['TypeMarketDate','Price']].groupby(['TypeMarketDate']).mean()
    
    ## Merge df and grouped_df on 'TypeMarketDate'
    df = df.merge(avgbuy4buy, on=['TypeMarketDate'], how='left')
    
    ## Rename the average buy price column
    df.rename(columns={'Price_x': 'Price', 'Price_y': 'AvgBuyPrice'}, inplace=True)

    ## Sort the trade history by Market and Date in descending order
    df = df.sort_values(['Market','Date'], ascending=[True,True])
    
    ## Forward Fill NaN
    df=df.fillna(method='ffill')
    
    ## Replace AvgBuyPrice with Price for Buy orders
    df.loc[df['Type'] == 'Buy', 'AvgBuyPrice'] = df.loc[df['Type'] == 'Buy', 'Price']

    # Sort the trade history by Market and Date in descending order
    df = df.sort_values('time', ascending=True)
    
    # Add new columns
    df['NetProfit ($)'] = (df['Price'] - df['AvgBuyPrice']) * df['Amount'] - df['Commission']
    
    # Calculate the sum of net profit
    sum_profit = round(df['NetProfit ($)'].sum(),2)
    
    # Calculate the number of months since the start of the month that begins on day 24
    df['Month'] = ((df['Date'].dt.year - df['Date'].dt.year.min()) * 12 +
                   (df['Date'].dt.month - df['Date'].dt.month.min()) +
                   (df['Date'].dt.day >= start_day_of_the_month))
    
    # Reorder the columns
    df = df[['Date', 'Month', 'Market', 'Type', 'Role', 'Price', 'Amount', 'Total', 'Commission', 'AvgBuyPrice', 'NetProfit ($)']]
    
    # Calculate profits per month
    monthly_profits = df.groupby('Month')['NetProfit ($)'].sum().round(2).reset_index()
    monthly_profits['NetProfit (%)'] = round(monthly_profits['NetProfit ($)'] / monthly_profits['Month'].map(capital_per_month) * 100,2)
    
    # Convert monthly profits to an HTML table
    monthly_profits_table = monthly_profits.to_html(index=False)
    
    # Calculate cumulative profit percentage per month
    df['NetProfit (%)'] = df['NetProfit ($)'] / df['Month'].map(capital_per_month) * 100
    df['CumulativeProfit (%)'] = df['NetProfit (%)'].cumsum()
    
    # Calculate the sum of net profit
    sum_profit_perct = round(df['NetProfit (%)'].sum(),2)
    
    # Convert the sorted trade history to an HTML table
    trade_history_table = df.to_html(index=False)

    # Saving Trade History Table
    df.to_csv("Trade_History_Table.csv")

    # Calculating the winning percentage
    count_of_sell_orders = len(df[df.Type=="Sell"])
    count_of_winning_sell_orders = len(df[(df.Type=="Sell") & (df['NetProfit ($)']>0)])
    win_percent = round(count_of_winning_sell_orders/count_of_sell_orders*100,2)
    
    # Prepare data for line graph
    daily_cumulative_profit = df.groupby(pd.Grouper(key='Date', freq='D'))['CumulativeProfit (%)'].last().reset_index()
    daily_cumulative_profit = daily_cumulative_profit.fillna(method='ffill')
    line_graph_data = {
        'labels': list(daily_cumulative_profit['Date'].dt.strftime('%Y-%m-%d')),
        'datasets': [
            {
                'label': 'Cumulative Profit Percentage',
                'data': [x for x in list(daily_cumulative_profit['CumulativeProfit (%)'])],
                'backgroundColor': 'rgba(0, 123, 255, 0.2)',
                'borderColor': 'rgba(0, 123, 255, 1)',
                'borderWidth': 1,
                'pointRadius': 0
            }
        ]
    }

    # Convert line graph data to JSON
    line_graph_json = json.dumps(line_graph_data)
    
    # Prepare Heatmap for NetProfit by Market and Month
    pp_heatmap_df = pd.pivot_table(df, values='NetProfit ($)', index='Market', columns='Month', aggfunc='sum')
    pp_heatmap_df.fillna(0, inplace=True)

    # Create the heatmap visualization
    plt.figure(figsize=(10, 6))
    sns.heatmap(pp_heatmap_df, annot=True, cmap='RdYlGn', fmt=".2f", cbar=False)
    plt.title('Net Profit by Market and Month')
    plt.xlabel('Month')
    plt.ylabel('Market')
    plt.xticks(rotation=90)
    plt.yticks(rotation=0)

    # Save the heatmap image to a file
    heatmap_path = 'static/heatmap.png'
    plt.savefig(heatmap_path)
    plt.close()
    
    # Prepare the data for the response
    # data = {
    #     'trade_history_table': trade_history_table,
    #     'sum_profit': sum_profit,
    #     'sum_profit_perct': sum_profit_perct,
    #     'win_percent': win_percent,
    #     'monthly_profits_table': monthly_profits_table,
    #     'line_graph_data': line_graph_json}

    p_trade_data['trade_history_table'] = trade_history_table
    p_trade_data['sum_profit'] = sum_profit
    p_trade_data['sum_profit_perct'] = sum_profit_perct
    p_trade_data['win_percent'] = win_percent
    p_trade_data['monthly_profits_table'] = monthly_profits_table
    p_trade_data['line_graph_data'] = line_graph_json
    p_trade_data['heatmap_path'] = heatmap_path
    
    return {}

@app.route('/trade_history')
def trade_history():
    # Get the data from the request or session or any other source
    trade_data = p_trade_data
    trade_history_table = trade_data['trade_history_table']
    sum_profit = trade_data['sum_profit']
    sum_profit_perct = trade_data['sum_profit_perct']
    win_percent = trade_data['win_percent']
    monthly_profits_table = trade_data['monthly_profits_table']
    line_graph_json = trade_data['line_graph_data']
    heatmap_path =  trade_data['heatmap_path']
        
    return render_template('trade_history.html', 
                           trade_history=trade_history_table, 
                           sum_profit=sum_profit,  
                           sum_profit_perct=sum_profit_perct,
                           win_percent = win_percent,
                           monthly_profits=monthly_profits_table,                                                
                           line_graph_data=line_graph_json,
                           heatmap_path=heatmap_path)

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=False, port=5500)
