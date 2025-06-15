import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide", page_title="Dashboard Penjualan Retail")

@st.cache_data(ttl=600)
def load_data():
    df_sales = pd.read_csv("fact_sales.csv", low_memory=False)
    df_customer = pd.read_csv("dim_customer.csv")
    df_date = pd.read_csv("dim_date.csv")

    df = df_sales.merge(df_date, how="left", on="TransactionDate") \
                 .merge(df_customer, how="left", on="CustomerID")
    return df

df = load_data()

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
    daily = filtered_df.groupby("TransactionDate")["TotalAmount"].sum().reset_index()
    fig1 = px.line(daily, x="TransactionDate", y="TotalAmount", markers=True)
    st.plotly_chart(fig1, use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("🏷️ Distribusi Penjualan per Kategori Produk")
        product_sales = filtered_df.groupby("ProductCategory")["TotalAmount"].sum().reset_index()
        fig2 = px.pie(product_sales, names="ProductCategory", values="TotalAmount", hole=0.3)
        st.plotly_chart(fig2, use_container_width=True)

    with col2:
        st.subheader("📆 Penjualan Bulanan per Kategori (Stacked Bar)")
        monthly = filtered_df.groupby(["Month", "ProductCategory"], observed=False)["TotalAmount"].sum().reset_index()
        fig3 = px.bar(monthly, x="Month", y="TotalAmount", color="ProductCategory", text_auto=".2s")
        fig3.update_layout(barmode="stack")
        st.plotly_chart(fig3, use_container_width=True)

# --- TAB 2 (Hanya 1 chart untuk uji coba) ---
with tab2:
    st.subheader("📉 Distribusi Diskon per Kategori Produk")

    # Hanya ambil kolom yang dibutuhkan & casting numerik
    df_box = filtered_df[["ProductCategory", "DiscountApplied"]].copy()
    df_box["DiscountApplied"] = pd.to_numeric(df_box["DiscountApplied"], errors="coerce")

    # Drop NA & ambil hanya ProductCategory dominan
    df_box = df_box.dropna(subset=["ProductCategory", "DiscountApplied"])
    top_cats = df_box["ProductCategory"].value_counts().nlargest(6).index
    df_box = df_box[df_box["ProductCategory"].isin(top_cats)]

    # Sampling agar tidak overload
    df_box = df_box.sample(n=min(2000, len(df_box)), random_state=42)

    if df_box.empty:
        st.warning("Tidak ada data yang cukup untuk menampilkan chart.")
    else:
        fig = px.box(
            df_box,
            x="ProductCategory",
            y="DiscountApplied",
            points="outliers",
            title="Distribusi Diskon per Kategori Produk (Top 6 Kategori)"
        )
        st.plotly_chart(fig, use_container_width=True)



