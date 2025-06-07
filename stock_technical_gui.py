import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import ta

st.set_page_config(page_title="Analisis Saham Harian", layout="wide")

st.title("Analisis Teknikal Saham Harian Indonesia")
st.write("Masukkan kode saham IDX (misalnya: ADRO.JK, BBCA.JK, TLKM.JK)")

# Sidebar input
kode_saham = st.text_input("🔍 Cari Kode Saham", value="TLKM.JK")

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
            
            # Konversi ke Series untuk menghindari error dimensional
            close_prices = df['Close'].squeeze()  # Mengubah menjadi Series
            high_prices = df['High'].squeeze()
            low_prices = df['Low'].squeeze()

            # Tambahkan indikator dengan input yang benar
            df['MA20'] = ta.trend.sma_indicator(close_prices, window=20)
            df['RSI'] = ta.momentum.rsi(close_prices)
            
            # MACD
            macd = ta.trend.MACD(close_prices)
            df['MACD'] = macd.macd()
            df['Signal'] = macd.macd_signal()
            
            # Bollinger Bands
            bb = ta.volatility.BollingerBands(close_prices)
            df['BB_upper'] = bb.bollinger_hband()
            df['BB_lower'] = bb.bollinger_lband()
            df['BB_mid'] = bb.bollinger_mavg()
            
            # Stochastic
            stoch = ta.momentum.StochasticOscillator(
                high=high_prices,
                low=low_prices,
                close=close_prices
            )
            df['%K'] = stoch.stoch()
            df['%D'] = stoch.stoch_signal()
            
            # ATR
            df['ATR'] = ta.volatility.average_true_range(
                high=high_prices,
                low=low_prices,
                close=close_prices,
                window=14
            )

            # Visualisasi
            fig, ax = plt.subplots(figsize=(12, 6))
            ax.plot(df.index, df['Close'], label='Close Price', color='blue')
            ax.plot(df.index, df['MA20'], label='20-day MA', color='orange')
            ax.fill_between(df.index, df['BB_upper'], df['BB_lower'], color='gray', alpha=0.2, label='Bollinger Bands')
            ax.set_title(f'Harga Saham & Indikator Teknikal - {kode_saham}')
            ax.legend()
            ax.grid(True)
            st.pyplot(fig)

            # Analisis sinyal
            latest = df.iloc[-1]
            prev = df.iloc[-2]
            signal_summary = []

            # Moving Average Analysis
            if prev['Close'] < prev['MA20'] and latest['Close'] > latest['MA20']:
                signal_summary.append("📈 MA20: Bullish Crossover (Harga menembus MA20 ke atas)")
            elif prev['Close'] > prev['MA20'] and latest['Close'] < latest['MA20']:
                signal_summary.append("📉 MA20: Bearish Crossover (Harga menembus MA20 ke bawah)")

            # RSI Analysis
            rsi_value = latest['RSI']
            if rsi_value > 70:
                signal_summary.append(f"⚠️ RSI: {rsi_value:.2f} (Overbought)")
            elif rsi_value < 30:
                signal_summary.append(f"🔻 RSI: {rsi_value:.2f} (Oversold)")
            else:
                signal_summary.append(f"📊 RSI: {rsi_value:.2f} (Netral)")

            # MACD Analysis
            if latest['MACD'] > latest['Signal'] and prev['MACD'] <= prev['Signal']:
                signal_summary.append("📈 MACD: Bullish Crossover (MACD menembus Signal Line ke atas)")
            elif latest['MACD'] < latest['Signal'] and prev['MACD'] >= prev['Signal']:
                signal_summary.append("📉 MACD: Bearish Crossover (MACD menembus Signal Line ke bawah)")

            # Bollinger Bands Analysis
            if latest['Close'] > latest['BB_upper']:
                signal_summary.append("⚠️ Bollinger: Harga di atas upper band (Overbought)")
            elif latest['Close'] < latest['BB_lower']:
                signal_summary.append("🔻 Bollinger: Harga di bawah lower band (Oversold)")

            # Stochastic Analysis
            stoch_k = latest['%K']
            stoch_d = latest['%D']
            if stoch_k > 80 and stoch_d > 80:
                signal_summary.append(f"⚠️ Stochastic: %K={stoch_k:.2f}, %D={stoch_d:.2f} (Overbought)")
            elif stoch_k < 20 and stoch_d < 20:
                signal_summary.append(f"🔻 Stochastic: %K={stoch_k:.2f}, %D={stoch_d:.2f} (Oversold)")
            elif stoch_k > stoch_d:
                signal_summary.append(f"📈 Stochastic: %K={stoch_k:.2f} > %D={stoch_d:.2f} (Bullish)")
            else:
                signal_summary.append(f"📉 Stochastic: %K={stoch_k:.2f} < %D={stoch_d:.2f} (Bearish)")

            # ATR Analysis
            signal_summary.append(f"📊 ATR (Volatilitas): {latest['ATR']:.2f}")

            # Tampilkan ringkasan
            st.subheader("📌 Ringkasan Sinyal Teknikal Hari Ini")
            for sinyal in signal_summary:
                st.markdown(f"- {sinyal}")

            # Tampilkan data terakhir
            st.subheader("📋 Data Teknikal Terakhir")
            st.dataframe(df.tail().style.format("{:.2f}"))

    except Exception as e:
        st.error(f"Terjadi kesalahan: {str(e)}")
        st.error("Pastikan kode saham benar (contoh: TLKM.JK) dan coba lagi.")
