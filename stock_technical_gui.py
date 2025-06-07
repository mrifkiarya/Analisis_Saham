import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import datetime as dt
import ta

st.set_page_config(page_title="Analisis Saham Harian", layout="wide")

st.title("📊 Analisis Teknikal Saham Harian Indonesia")
st.write("Masukkan kode saham IDX (misalnya: ADRO.JK, BBCA.JK, TLKM.JK)")

# Sidebar input
kode_saham = st.text_input("🔍 Cari Kode Saham", value="ADRO.JK")

if kode_saham:
    try:
        # Ambil data
        data = yf.download(kode_saham, period="6mo", interval="1d", progress=False)
        if data.empty:
            st.error("Kode saham tidak ditemukan atau data kosong.")
        else:
            st.success(f"Menampilkan data untuk: {kode_saham}")
            df = data.copy()
            df.dropna(inplace=True)

            # Tambahkan indikator
            df['MA20'] = ta.trend.sma_indicator(df['Close'], window=20)
            df['RSI'] = ta.momentum.RSIIndicator(df['Close']).rsi()
            macd = ta.trend.MACD(df['Close'])
            df['MACD'] = macd.macd()
            df['Signal'] = macd.macd_signal()
            bollinger = ta.volatility.BollingerBands(df['Close'])
            df['BB_upper'] = bollinger.bollinger_hband()
            df['BB_lower'] = bollinger.bollinger_lband()
            df['BB_mid'] = bollinger.bollinger_mavg()
            stoch = ta.momentum.StochasticOscillator(df['High'], df['Low'], df['Close'])
            df['%K'] = stoch.stoch()
            df['%D'] = stoch.stoch_signal()
            df['ATR'] = ta.volatility.AverageTrueRange(df['High'], df['Low'], df['Close']).average_true_range()

            # Visualisasi
            fig, ax = plt.subplots(figsize=(12, 6))
            ax.plot(df.index, df['Close'], label='Close')
            ax.plot(df.index, df['MA20'], label='MA20')
            ax.fill_between(df.index, df['BB_upper'], df['BB_lower'], color='gray', alpha=0.2, label='Bollinger Bands')
            ax.set_title(f'Harga & MA20 - {kode_saham}')
            ax.legend()
            ax.grid(True)
            st.pyplot(fig)

            # Ambil data terakhir
            latest = df.iloc[-1]
            prev = df.iloc[-2]
            signal_summary = []

            # Moving Average
            if prev['Close'] < prev['MA20'] and latest['Close'] > latest['MA20']:
                signal_summary.append("📈 MA20: Bullish Crossover")
            elif prev['Close'] > prev['MA20'] and latest['Close'] < latest['MA20']:
                signal_summary.append("📉 MA20: Bearish Crossover")

            # RSI
            if latest['RSI'] > 70:
                signal_summary.append("⚠️ RSI: Overbought")
            elif latest['RSI'] < 30:
                signal_summary.append("🔻 RSI: Oversold")
            else:
                signal_summary.append(f"📊 RSI: {latest['RSI']:.2f}")

            # MACD
            if latest['MACD'] > latest['Signal'] and prev['MACD'] <= prev['Signal']:
                signal_summary.append("📈 MACD: Bullish Crossover")
            elif latest['MACD'] < latest['Signal'] and prev['MACD'] >= prev['Signal']:
                signal_summary.append("📉 MACD: Bearish Crossover")

            # Bollinger
            if latest['Close'] > latest['BB_upper']:
                signal_summary.append("⚠️ Bollinger: Overbought")
            elif latest['Close'] < latest['BB_lower']:
                signal_summary.append("🔻 Bollinger: Oversold")

            # Stochastic
            if latest['%K'] > 80 and latest['%D'] > 80:
                signal_summary.append("⚠️ Stochastic: Overbought")
            elif latest['%K'] < 20 and latest['%D'] < 20:
                signal_summary.append("🔻 Stochastic: Oversold")
            elif latest['%K'] > latest['%D']:
                signal_summary.append("📈 Stochastic: Bullish")
            elif latest['%K'] < latest['%D']:
                signal_summary.append("📉 Stochastic: Bearish")

            # ATR
            signal_summary.append(f"📊 ATR (Volatilitas): {latest['ATR']:.2f}")

            # Ringkasan
            st.subheader("📌 Ringkasan Sinyal Hari Ini")
            for sinyal in signal_summary:
                st.markdown(f"- {sinyal}")

    except Exception as e:
        st.error(f"Terjadi kesalahan: {e}")
