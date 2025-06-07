import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import ta
import numpy as np

st.set_page_config(page_title="Analisis Saham Harian", layout="wide")

st.title("📊 Analisis Teknikal Saham Harian Indonesia")
st.write("Masukkan kode saham IDX (misalnya: ADRO.JK, BBCA.JK, TLKM.JK)")

# Sidebar input
kode_saham = st.text_input("🔍 Cari Kode Saham", value="TLKM.JK")

if kode_saham:
    try:
        # Ambil data dengan timeout
        data = yf.download(kode_saham, period="6mo", interval="1d", progress=False)
        
        if data.empty:
            st.error("Kode saham tidak ditemukan atau data kosong.")
        else:
            st.success(f"Menampilkan data untuk: {kode_saham}")
            df = data.copy()
            df.dropna(inplace=True)
            
            # Pastikan kita menggunakan Series bukan DataFrame
            close = df['Close'].astype('float64')
            high = df['High'].astype('float64')
            low = df['Low'].astype('float64')
            
            # Fungsi untuk menghandle error pada indikator
            def safe_add_indicator(df, col_name, indicator_func, *args):
                try:
                    df[col_name] = indicator_func(*args)
                except Exception as e:
                    st.warning(f"Gagal menambahkan {col_name}: {str(e)}")
                    df[col_name] = np.nan
            
            # Tambahkan indikator dengan penanganan error
            safe_add_indicator(df, 'MA20', ta.trend.sma_indicator, close, 20)
            safe_add_indicator(df, 'RSI', ta.momentum.rsi, close)
            
            # MACD
            try:
                macd = ta.trend.MACD(close)
                df['MACD'] = macd.macd()
                df['Signal'] = macd.macd_signal()
            except Exception as e:
                st.warning(f"Gagal menambahkan MACD: {str(e)}")
                df['MACD'] = df['Signal'] = np.nan
            
            # Bollinger Bands
            try:
                bb = ta.volatility.BollingerBands(close)
                df['BB_upper'] = bb.bollinger_hband()
                df['BB_lower'] = bb.bollinger_lband()
                df['BB_mid'] = bb.bollinger_mavg()
            except Exception as e:
                st.warning(f"Gagal menambahkan Bollinger Bands: {str(e)}")
                df['BB_upper'] = df['BB_lower'] = df['BB_mid'] = np.nan
            
            # Stochastic
            try:
                stoch = ta.momentum.StochasticOscillator(high=high, low=low, close=close)
                df['%K'] = stoch.stoch()
                df['%D'] = stoch.stoch_signal()
            except Exception as e:
                st.warning(f"Gagal menambahkan Stochastic: {str(e)}")
                df['%K'] = df['%D'] = np.nan
            
            # ATR
            try:
                df['ATR'] = ta.volatility.average_true_range(high=high, low=low, close=close, window=14)
            except Exception as e:
                st.warning(f"Gagal menambahkan ATR: {str(e)}")
                df['ATR'] = np.nan

            # Visualisasi hanya untuk data yang valid
            valid_cols = [col for col in ['Close', 'MA20', 'BB_upper', 'BB_lower'] if col in df and not df[col].isnull().all()]
            
            if len(valid_cols) > 0:
                fig, ax = plt.subplots(figsize=(12, 6))
                if 'Close' in valid_cols:
                    ax.plot(df.index, df['Close'], label='Close Price', color='blue')
                if 'MA20' in valid_cols:
                    ax.plot(df.index, df['MA20'], label='20-day MA', color='orange')
                if all(col in valid_cols for col in ['BB_upper', 'BB_lower']):
                    ax.fill_between(df.index, df['BB_upper'], df['BB_lower'], color='gray', alpha=0.2, label='Bollinger Bands')
                ax.set_title(f'Harga Saham & Indikator Teknikal - {kode_saham}')
                ax.legend()
                ax.grid(True)
                st.pyplot(fig)
            else:
                st.warning("Tidak ada data yang valid untuk divisualisasikan")

            # Analisis sinyal hanya untuk data yang valid
            signal_summary = []
            
            if not df.empty:
                latest = df.iloc[-1]
                prev = df.iloc[-2] if len(df) > 1 else latest
                
                # Moving Average Analysis
                if 'MA20' in df and not pd.isna(latest['MA20']):
                    if prev['Close'] < prev['MA20'] and latest['Close'] > latest['MA20']:
                        signal_summary.append("📈 MA20: Bullish Crossover")
                    elif prev['Close'] > prev['MA20'] and latest['Close'] < latest['MA20']:
                        signal_summary.append("📉 MA20: Bearish Crossover")
                
                # RSI Analysis
                if 'RSI' in df and not pd.isna(latest['RSI']):
                    rsi_value = latest['RSI']
                    if rsi_value > 70:
                        signal_summary.append(f"⚠️ RSI: {rsi_value:.2f} (Overbought)")
                    elif rsi_value < 30:
                        signal_summary.append(f"🔻 RSI: {rsi_value:.2f} (Oversold)")
                    else:
                        signal_summary.append(f"📊 RSI: {rsi_value:.2f} (Netral)")
                
                # MACD Analysis
                if all(col in df for col in ['MACD', 'Signal']) and not pd.isna(latest['MACD']):
                    if latest['MACD'] > latest['Signal'] and prev['MACD'] <= prev['Signal']:
                        signal_summary.append("📈 MACD: Bullish Crossover")
                    elif latest['MACD'] < latest['Signal'] and prev['MACD'] >= prev['Signal']:
                        signal_summary.append("📉 MACD: Bearish Crossover")
                
                # Bollinger Bands Analysis
                if all(col in df for col in ['BB_upper', 'BB_lower']):
                    if latest['Close'] > latest['BB_upper']:
                        signal_summary.append("⚠️ Bollinger: Harga di atas upper band")
                    elif latest['Close'] < latest['BB_lower']:
                        signal_summary.append("🔻 Bollinger: Harga di bawah lower band")
                
                # Stochastic Analysis
                if all(col in df for col in ['%K', '%D']):
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
                if 'ATR' in df and not pd.isna(latest['ATR']):
                    signal_summary.append(f"📊 ATR (Volatilitas): {latest['ATR']:.2f}")

            # Tampilkan ringkasan
            if signal_summary:
                st.subheader("📌 Ringkasan Sinyal Teknikal Hari Ini")
                for sinyal in signal_summary:
                    st.markdown(f"- {sinyal}")
            else:
                st.warning("Tidak ada sinyal teknikal yang dapat dihasilkan dari data yang tersedia")

            # Tampilkan data terakhir
            st.subheader("📋 Data Teknikal Terakhir")
            st.dataframe(df.tail().style.format("{:.2f}"))

    except Exception as e:
        st.error(f"Terjadi kesalahan: {str(e)}")
        st.error("Pastikan:")
        st.error("- Kode saham benar (contoh: TLKM.JK)")
        st.error("- Koneksi internet stabil")
        st.error("- Library sudah diupdate (pip install --upgrade yfinance ta pandas numpy)")
