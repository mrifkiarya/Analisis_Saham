import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
from ta.momentum import RSIIndicator
from ta.trend import SMAIndicator

# Judul Aplikasi
st.title("📊 Analisis Teknikal Saham Harian Indonesia")

# Petunjuk
st.markdown("Masukkan kode saham IDX (misalnya: **ADRO.JK**, **BBCA.JK**, **TLKM.JK**)")

# Input kode saham
kode_saham = st.text_input("🔍 Cari Kode Saham", value="TLKM.JK")

# Tombol cari
if st.button("Tampilkan Analisis"):
    try:
        # Ambil data saham dari Yahoo Finance
        df = yf.download(kode_saham, period="6mo", interval="1d")

        if df.empty:
            st.warning("❗Data tidak ditemukan. Coba kode saham lain.")
        else:
            st.success(f"Menampilkan data untuk: {kode_saham}")

            # Pastikan tidak ada NaN untuk proses teknikal
            df.dropna(inplace=True)

            # Tambahkan indikator teknikal
            df['SMA20'] = SMAIndicator(close=df['Close'], window=20).sma_indicator()
            df['RSI'] = RSIIndicator(close=df['Close'], window=14).rsi()

            # Tampilkan tabel data terakhir
            st.subheader("📈 Data Harga & Indikator (5 Hari Terakhir)")
            st.dataframe(df[['Close', 'SMA20', 'RSI']].tail(5))

            # Plot Harga & SMA
            st.subheader("📉 Grafik Harga & SMA20")
            fig, ax = plt.subplots()
            ax.plot(df.index, df['Close'], label='Close Price', color='blue')
            ax.plot(df.index, df['SMA20'], label='SMA 20 Hari', color='orange')
            ax.set_xlabel("Tanggal")
            ax.set_ylabel("Harga")
            ax.legend()
            st.pyplot(fig)

            # Plot RSI
            st.subheader("📊 Grafik RSI (Relative Strength Index)")
            fig2, ax2 = plt.subplots()
            ax2.plot(df.index, df['RSI'], label='RSI', color='purple')
            ax2.axhline(70, color='red', linestyle='--', label='Overbought')
            ax2.axhline(30, color='green', linestyle='--', label='Oversold')
            ax2.set_ylim([0, 100])
            ax2.set_xlabel("Tanggal")
            ax2.set_ylabel("RSI")
            ax2.legend()
            st.pyplot(fig2)

    except Exception as e:
        st.error(f"Terjadi kesalahan: {e}")
