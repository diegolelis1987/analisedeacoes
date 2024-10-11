from flask import Flask, render_template, request, jsonify
import yfinance as yf
import plotly.graph_objs as go
import pandas as pd

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process():
    ticker = request.form['ticker']
    stock_data = yf.Ticker(ticker)

    # Obtenha os dados históricos
    df = stock_data.history(period='1y')  # Obter dados do último ano

    # Verifique se o DataFrame não está vazio
    if df.empty:
        return jsonify({'error': 'Nenhum dado encontrado para o ticker fornecido.'}), 400

    # Calcule indicadores
    bollinger = calculate_bollinger_bands(df)
    volume = calculate_volume(df)
    sma, ema = calculate_sma_ema(df)
    rsi = calculate_rsi(df)

    # Prepare os gráficos
    bollinger_chart = create_bollinger_chart(df, bollinger)
    volume_chart = create_volume_chart(df, volume)
    sma_ema_chart = create_sma_ema_chart(df, sma, ema)
    rsi_chart = create_rsi_chart(df, rsi)

    return jsonify({
        'bollinger': [bollinger_chart, "Bollinger Bands ajudam a visualizar a VOLATILIDADE da ação e identificar POSSÍVEIS reversões de preço..."],
        'volume': [volume_chart, "Volume mostra o TOTAL de ações negociadas em um período."],
        'sma_ema': [sma_ema_chart, "SMA (Média Móvel Simples) e EMA (Média Móvel Exponencial) ajudam a entender a tendência."],
        'rsi': [rsi_chart, "RSI (Índice de Força Relativa) indica condições de sobrecompra ou sobrevenda."],
        'summary': {
            'latest_close': df['Close'][-1],
            'previous_close': df['Close'][-2] if len(df) > 1 else None,
            'percent_change': (df['Close'][-1] - df['Close'][-2]) / df['Close'][-2] * 100 if len(df) > 1 else None,
            'avg_volume': df['Volume'].mean()
        },
        'ticker': ticker  # Retorne o ticker para uso no front-end
    })

def calculate_bollinger_bands(df):
    window = 20
    df['SMA'] = df['Close'].rolling(window=window).mean()
    df['Upper Band'] = df['SMA'] + (df['Close'].rolling(window=window).std() * 2)
    df['Lower Band'] = df['SMA'] - (df['Close'].rolling(window=window).std() * 2)
    return df[['Upper Band', 'Lower Band', 'SMA']]

def calculate_volume(df):
    return df['Volume']

def calculate_sma_ema(df):
    sma = df['Close'].rolling(window=20).mean()
    ema = df['Close'].ewm(span=20, adjust=False).mean()
    return sma, ema

def calculate_rsi(df):
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def create_bollinger_chart(df, bollinger):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df.index, y=df['Close'], mode='lines', name='Close Price'))
    fig.add_trace(go.Scatter(x=bollinger.index, y=bollinger['Upper Band'], mode='lines', name='Upper Band'))
    fig.add_trace(go.Scatter(x=bollinger.index, y=bollinger['Lower Band'], mode='lines', name='Lower Band'))
    fig.add_trace(go.Scatter(x=bollinger.index, y=bollinger['SMA'], mode='lines', name='SMA'))
    fig.update_layout(title='Bollinger Bands', xaxis_title='Date', yaxis_title='Price')
    return fig.to_html(full_html=False)

def create_volume_chart(df, volume):
    fig = go.Figure()
    fig.add_trace(go.Bar(x=df.index, y=volume, name='Volume'))
    fig.update_layout(title='Volume', xaxis_title='Date', yaxis_title='Volume')
    return fig.to_html(full_html=False)

def create_sma_ema_chart(df, sma, ema):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df.index, y=df['Close'], mode='lines', name='Close Price'))
    fig.add_trace(go.Scatter(x=df.index, y=sma, mode='lines', name='SMA'))
    fig.add_trace(go.Scatter(x=df.index, y=ema, mode='lines', name='EMA'))
    fig.update_layout(title='SMA and EMA', xaxis_title='Date', yaxis_title='Price')
    return fig.to_html(full_html=False)

def create_rsi_chart(df, rsi):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df.index, y=rsi, mode='lines', name='RSI'))
    fig.add_hline(y=70, line_color='red', line_dash='dash', name='Overbought')
    fig.add_hline(y=30, line_color='green', line_dash='dash', name='Oversold')
    fig.update_layout(title='RSI', xaxis_title='Date', yaxis_title='RSI Value')
    return fig.to_html(full_html=False)

if __name__ == '__main__':
    app.run(debug=True)
