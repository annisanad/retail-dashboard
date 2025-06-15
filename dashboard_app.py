import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide", page_title="Dashboard Penjualan Retail")

@st.cache_data(ttl=600)
def load_data():
    try:
        df_sales = pd.read_csv("fact_sales.csv", dtype=str, low_memory=False)
        df_customer = pd.read_csv("dim_customer.csv", dtype=str, low_memory=False)
        df_date = pd.read_csv("dim_date.csv", dtype=str, low_memory=False)

        df = df_sales.merge(df_date, how="left", on="TransactionDate") \
                     .merge(df_customer, how="left", on="CustomerID")

        # konversi numerik
        df["Quantity"] = pd.to_numeric(df["Quantity"], errors="coerce")
        df["TotalAmount"] = pd.to_numeric(df["TotalAmount"], errors="coerce")
        df["DiscountApplied"] = pd.to_numeric(df["DiscountApplied"], errors="coerce")
        return df.dropna(subset=["TransactionDate", "CustomerID"])
    except Exception as e:
        st.error(f"❌ Gagal memuat data: {e}")
        return pd.DataFrame()

df = load_data()
if df.empty:
    st.stop()

# Sidebar filter
with st.sidebar:
    st.header("🔍 Filter Data")
    locs = ["-- Semua --"] + sorted(df["Location"].dropna().unique())
    pays = ["-- Semua --"] + sorted(df["PaymentMethod"].dropna().unique())
    gens = ["-- Semua --"] + sorted(df["Gender"].dropna().unique())

    selected_location = st.selectbox("Pilih Lokasi", locs)
    selected_payment = st.selectbox("Pilih Metode Pembayaran", pays)
    selected_gender = st.selectbox("Pilih Gender Pelanggan", gens)

filtered_df = df.copy()
if selected_location != "-- Semua --":
    filtered_df = filtered_df[filtered_df["Location"] == selected_location]
if selected_payment != "-- Semua --":
    filtered_df = filtered_df[filtered_df["PaymentMethod"] == selected_payment]
if selected_gender != "-- Semua --":
    filtered_df = filtered_df[filtered_df["Gender"] == selected_gender]

if filtered_df.empty:
    st.warning("❗ Tidak ada data yang cocok dengan kombinasi filter.")
    st.stop()

# KPI
st.title("📊 Dashboard Analitik Penjualan")
col1, col2, col3, col4 = st.columns(4)
col1.metric("💰 Total Penjualan", f"{filtered_df['TotalAmount'].sum():,.0f}")
col2.metric("📦 Total Item Terjual", int(filtered_df['Quantity'].sum()))
col3.metric("🧾 Jumlah Transaksi", filtered_df.shape[0])
col4.metric("👥 Jumlah Pelanggan", filtered_df['CustomerID'].nunique())

# Tabs
tab1, tab2 = st.tabs(["📈 Trend & Kategori", "🔁 Repeat & Diskon"])

# --- TAB 1 ---
with tab1:
    st.subheader("📅 Trend Penjualan Harian")
    daily = filtered_df.groupby("TransactionDate", observed=True)["TotalAmount"].sum().reset_index()
    fig1 = px.line(daily, x="TransactionDate", y="TotalAmount", markers=True)
    st.plotly_chart(fig1, use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("🏷️ Distribusi Penjualan per Kategori Produk")
        product_sales = filtered_df.groupby("ProductCategory", observed=True)["TotalAmount"].sum().reset_index()
        fig2 = px.pie(product_sales, names="ProductCategory", values="TotalAmount", hole=0.3)
        st.plotly_chart(fig2, use_container_width=True)

    with col2:
        st.subheader("📆 Penjualan Bulanan per Kategori (Stacked Bar)")
        monthly = filtered_df.groupby(["Month", "ProductCategory"], observed=True)["TotalAmount"].sum().reset_index()
        fig3 = px.bar(monthly, x="Month", y="TotalAmount", color="ProductCategory", text_auto=".2s")
        fig3.update_layout(barmode="stack")
        st.plotly_chart(fig3, use_container_width=True)

# --- TAB 2 ---
with tab2:
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📉 Distribusi Diskon per Kategori Produk")
        fig4 = px.box(filtered_df, x="ProductCategory", y="DiscountApplied")
        st.plotly_chart(fig4, use_container_width=True)

    with col2:
        st.subheader("🔹 Korelasi Quantity vs TotalAmount")

        df_scatter = filtered_df.copy()
        df_scatter = df_scatter.dropna(subset=["Quantity", "TotalAmount"])
        df_scatter = df_scatter[df_scatter["TotalAmount"] > 0]

        # batasi titik agar ringan di deploy
        if len(df_scatter) > 2000:
            df_scatter = df_scatter.sample(2000, random_state=42)

        fig6 = px.scatter(
            df_scatter,
            x="Quantity",
            y="TotalAmount",
            color="ProductCategory",
            size="TotalAmount",
            hover_data=["CustomerID", "PaymentMethod"],
            opacity=0.7
        )
        st.plotly_chart(fig6, use_container_width=True)

    st.subheader("🔁 Pola Pembelian Ulang (Binned Histogram per Kategori Produk)")
    repeat_df = (
        filtered_df.groupby(["CustomerID", "ProductCategory"], observed=True)
        .size().reset_index(name="RepeatCount")
    )

    bins = [0, 1, 2, 5, 10, 20, 50, 100, 5000]
    labels = ["1", "2", "3–5", "6–10", "11–20", "21–50", "51–100", "101+"]

    repeat_df["RepeatBin"] = pd.cut(repeat_df["RepeatCount"], bins=bins, labels=labels, right=True)
    binned = (
        repeat_df.groupby(["RepeatBin", "ProductCategory"], observed=True)
        .size().reset_index(name="JumlahPelanggan")
    )

    fig5 = px.bar(
        binned, x="RepeatBin", y="JumlahPelanggan", color="ProductCategory",
        barmode="group", text_auto=True
    )
    st.plotly_chart(fig5, use_container_width=True)
