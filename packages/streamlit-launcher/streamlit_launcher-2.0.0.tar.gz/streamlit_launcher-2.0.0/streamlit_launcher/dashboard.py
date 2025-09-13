import pandas as pd
import numpy as np
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import matplotlib.pyplot as plt
from scipy import stats
import matplotlib.dates as mdates
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# Konfigurasi halaman
st.set_page_config(
    page_title="Dashboard Statistik Profesional",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS kustom untuk styling
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1.5rem;
        border-radius: 0.5rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .stButton>button {
        width: 100%;
        background-color: #1f77b4;
        color: white;
    }
    .data-table {
        width: 100%;
        border-collapse: collapse;
        margin: 1rem 0;
    }
    .data-table th, .data-table td {
        border: 1px solid #ddd;
        padding: 8px;
        text-align: left;
    }
    .data-table th {
        background-color: #f2f2f2;
    }
    .data-table tr:nth-child(even) {
        background-color: #f9f9f9;
    }
    .up-trend {
        color: green;
        font-weight: bold;
    }
    .down-trend {
        color: red;
        font-weight: bold;
    }
    .stock-summary {
        background-color: #f8f9fa;
        padding: 15px;
        border-radius: 5px;
        margin-bottom: 20px;
        border-left: 5px solid #1f77b4;
    }
</style>
""", unsafe_allow_html=True)

# Fungsi untuk menampilkan dataframe sebagai HTML (menggantikan st.dataframe)
def display_dataframe(df, num_rows=5):
    st.markdown(df.head(num_rows).to_html(classes='data-table', escape=False), unsafe_allow_html=True)

# Fungsi untuk memproses file yang diupload
def process_uploaded_file(uploaded_file):
    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        elif uploaded_file.name.endswith('.xlsx') or uploaded_file.name.endswith('.xls'):
            df = pd.read_excel(uploaded_file)
        else:
            st.error("Format file tidak didukung. Harap unggah file CSV atau Excel.")
            return None
        
        return df
    except Exception as e:
        st.error(f"Terjadi kesalahan saat memproses file: {str(e)}")
        return None

# Fungsi untuk menggabungkan beberapa dataset
def merge_datasets(datasets, merge_method='concat'):
    if not datasets:
        return None
    
    if merge_method == 'concat':
        # Gabungkan dataset secara vertikal (menambah baris)
        return pd.concat(datasets, ignore_index=True)
    else:
        # Untuk penggabungan berdasarkan kolom (join)
        merged_df = datasets[0]
        for i in range(1, len(datasets)):
            merged_df = pd.merge(merged_df, datasets[i], how=merge_method)
        return merged_df

# Fungsi untuk membuat visualisasi data
def create_visualizations(df):
    # Menentukan kolom numerik dan non-numerik
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    non_numeric_cols = df.select_dtypes(exclude=[np.number]).columns.tolist()
    
    # Jika tidak ada kolom numerik, beri pesan error
    if not numeric_cols:
        st.error("Tidak ditemukan kolom numerik dalam dataset.")
        return
    
    # Default kolom untuk sumbu X dan Y
    default_x = non_numeric_cols[0] if non_numeric_cols else df.index.name if df.index.name else "Index"
    default_y = numeric_cols[0]
    
    # Sidebar untuk konfigurasi chart
    st.sidebar.header("Konfigurasi Visualisasi")
    
    # Pilihan jenis chart
    chart_type = st.sidebar.selectbox(
        "Pilih Jenis Chart",
        ["Line Chart", "Bar Chart", "Histogram", "Scatter Plot", "Pie Chart", "Box Plot", "Heatmap", "Candlestick", "Area Chart", "Histogram dengan Multiple Variables"]
    )
    
    # Pilihan kolom berdasarkan jenis chart
    if chart_type in ["Line Chart", "Bar Chart", "Scatter Plot", "Area Chart"]:
        x_col = st.sidebar.selectbox("Pilih kolom untuk sumbu X", [default_x] + non_numeric_cols + numeric_cols)
        y_col = st.sidebar.selectbox("Pilih kolom untuk sumbu Y", numeric_cols, index=0)
        
        if chart_type == "Line Chart":
            fig = px.line(df, x=x_col, y=y_col, title=f"{y_col} over {x_col}")
        elif chart_type == "Bar Chart":
            fig = px.bar(df, x=x_col, y=y_col, title=f"{y_col} by {x_col}")
        elif chart_type == "Scatter Plot":
            color_col = st.sidebar.selectbox("Pilih kolom untuk warna (opsional)", [None] + non_numeric_cols + numeric_cols)
            size_col = st.sidebar.selectbox("Pilih kolom untuk ukuran (opsional)", [None] + numeric_cols)
            fig = px.scatter(df, x=x_col, y=y_col, color=color_col, size=size_col, 
                            title=f"Scatter Plot: {y_col} vs {x_col}")
        elif chart_type == "Area Chart":
            fig = px.area(df, x=x_col, y=y_col, title=f"{y_col} over {x_col} (Area Chart)")
    
    elif chart_type == "Histogram":
        col = st.sidebar.selectbox("Pilih kolom", numeric_cols)
        fig = px.histogram(df, x=col, title=f"Distribusi {col}")
    
    elif chart_type == "Histogram dengan Multiple Variables":
        selected_cols = st.sidebar.multiselect("Pilih kolom untuk histogram", numeric_cols, default=numeric_cols[:min(3, len(numeric_cols))])
        
        if len(selected_cols) > 0:
            # Buat histogram dengan multiple variables
            fig = go.Figure()
            
            for col in selected_cols:
                # Pastikan tidak ada nilai NaN atau infinite
                clean_data = df[col].replace([np.inf, -np.inf], np.nan).dropna()
                
                if len(clean_data) > 0:
                    fig.add_trace(go.Histogram(
                        x=clean_data,
                        name=col,
                        opacity=0.75
                    ))
            
            fig.update_layout(
                barmode='overlay',
                title_text='Distribusi Beberapa Variabel',
                xaxis_title_text='Nilai',
                yaxis_title_text='Frekuensi'
            )
            
            # Atur opacity untuk melihat overlap
            fig.update_traces(opacity=0.75)
        else:
            st.error("Pilih setidaknya satu kolom untuk histogram")
            return
    
    elif chart_type == "Pie Chart":
        # Untuk pie chart, kita butuh kolom kategori dan nilai
        cat_col = st.sidebar.selectbox("Pilih kolom kategori", non_numeric_cols)
        value_col = st.sidebar.selectbox("Pilih kolom nilai", numeric_cols)
        
        # Opsi untuk menggabungkan kategori kecil
        combine_threshold = st.sidebar.slider(
            "Gabungkan kategori dengan persentase di bawah (%)", 
            min_value=0, max_value=20, value=5, step=1
        )
        
        # Hitung total untuk setiap kategori
        pie_data = df.groupby(cat_col)[value_col].sum().reset_index()
        total = pie_data[value_col].sum()
        pie_data['percentage'] = (pie_data[value_col] / total) * 100
        
        # Gabungkan kategori kecil
        if combine_threshold > 0:
            other_data = pie_data[pie_data['percentage'] < combine_threshold]
            main_data = pie_data[pie_data['percentage'] >= combine_threshold]
            
            if len(other_data) > 0:
                other_sum = other_data[value_col].sum()
                other_percentage = other_data['percentage'].sum()
                
                # Buat dataframe baru dengan kategori "Lainnya"
                main_data = pd.concat([
                    main_data,
                    pd.DataFrame({cat_col: ['Lainnya'], value_col: [other_sum], 'percentage': [other_percentage]})
                ], ignore_index=True)
            
            pie_data = main_data
        
        fig = px.pie(pie_data, names=cat_col, values=value_col, title=f"Proporsi {value_col} oleh {cat_col}")
    
    elif chart_type == "Box Plot":
        col = st.sidebar.selectbox("Pilih kolom", numeric_cols)
        fig = px.box(df, y=col, title=f"Box Plot {col}")
    
    elif chart_type == "Heatmap":
        if len(numeric_cols) < 2:
            st.error("Heatmap memerlukan setidaknya 2 kolom numerik")
            return
        selected_cols = st.sidebar.multiselect("Pilih kolom untuk heatmap", numeric_cols, default=numeric_cols[:min(5, len(numeric_cols))])
        if len(selected_cols) < 2:
            st.error("Pilih setidaknya 2 kolom untuk heatmap")
            return
        
        # Pastikan tidak ada nilai NaN atau infinite
        clean_df = df[selected_cols].replace([np.inf, -np.inf], np.nan).dropna()
        
        if len(clean_df) < 2:
            st.error("Tidak cukup data setelah pembersihan nilai NaN/infinite")
            return
            
        corr_matrix = clean_df.corr()
        fig = px.imshow(corr_matrix, text_auto=True, aspect="auto", title="Heatmap Korelasi")
    
    elif chart_type == "Candlestick":
        # Untuk candlestick, kita butuh kolom OHLC
        st.sidebar.info("Candlestick memerlukan kolom Open, High, Low, Close")
        date_col = st.sidebar.selectbox("Pilih kolom tanggal", non_numeric_cols)
        open_col = st.sidebar.selectbox("Pilih kolom Open", numeric_cols)
        high_col = st.sidebar.selectbox("Pilih kolom High", numeric_cols)
        low_col = st.sidebar.selectbox("Pilih kolom Low", numeric_cols)
        close_col = st.sidebar.selectbox("Pilih kolom Close", numeric_cols)
        
        # Pastikan kolom tanggal dalam format datetime
        try:
            df[date_col] = pd.to_datetime(df[date_col])
            df_sorted = df.sort_values(by=date_col).copy()
            
            fig = go.Figure(data=[go.Candlestick(
                x=df_sorted[date_col],
                open=df_sorted[open_col],
                high=df_sorted[high_col],
                low=df_sorted[low_col],
                close=df_sorted[close_col],
                name='Harga Saham'
            )])
            
            fig.update_layout(
                title='Chart Candlestick',
                yaxis_title='Harga',
                xaxis_title='Tanggal'
            )
        except Exception as e:
            st.error(f"Error membuat candlestick chart: {str(e)}")
            return
    
    # Tampilkan chart
    st.plotly_chart(fig, use_container_width=True)
    
    # Tampilkan beberapa chart otomatis berdasarkan data
    st.subheader("Visualisasi Otomatis")
    
    # Pilih beberapa kolom numerik untuk ditampilkan
    if len(numeric_cols) > 0:
        selected_cols = st.multiselect(
            "Pilih kolom untuk divisualisasikan",
            numeric_cols,
            default=numeric_cols[:min(3, len(numeric_cols))]
        )
        
        if selected_cols:
            col1, col2 = st.columns(2)
            
            with col1:
                # Line chart untuk kolom terpilih
                # Pastikan tidak ada nilai NaN atau infinite
                clean_df = df[selected_cols].replace([np.inf, -np.inf], np.nan).dropna()
                fig_multi = px.line(clean_df, y=selected_cols, title="Trend Data")
                st.plotly_chart(fig_multi, use_container_width=True)
            
            with col2:
                # Correlation heatmap
                if len(selected_cols) > 1:
                    # Pastikan tidak ada nilai NaN atau infinite
                    clean_df = df[selected_cols].replace([np.inf, -np.inf], np.nan).dropna()
                    
                    if len(clean_df) > 1:
                        corr_matrix = clean_df.corr()
                        fig_corr = px.imshow(corr_matrix, text_auto=True, aspect="auto", 
                                            title="Korelasi antar Variabel")
                        st.plotly_chart(fig_corr, use_container_width=True)
                    else:
                        st.error("Tidak cukup data untuk menghitung korelasi setelah pembersihan")
                else:
                    # Jika hanya satu kolom, tampilkan box plot
                    clean_data = df[selected_cols[0]].replace([np.inf, -np.inf], np.nan).dropna()
                    if len(clean_data) > 0:
                        fig_box = px.box(y=clean_data, title=f"Distribusi {selected_cols[0]}")
                        st.plotly_chart(fig_box, use_container_width=True)
                    else:
                        st.error("Tidak ada data yang valid untuk ditampilkan")

# Fungsi untuk menampilkan statistik deskriptif lengkap
def show_statistics(df):
    st.header("Statistik Deskriptif")
    
    # Tampilkan statistik dasar
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Jumlah Baris", df.shape[0])
    
    with col2:
        st.metric("Jumlah Kolom", df.shape[1])
    
    with col3:
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        st.metric("Kolom Numerik", len(numeric_cols))
    
    with col4:
        non_numeric_cols = df.select_dtypes(exclude=[np.number]).columns.tolist()
        st.metric("Kolom Non-Numerik", len(non_numeric_cols))
    
    # Tampilkan preview data menggunakan HTML
    st.subheader("Preview Data")
    display_dataframe(df)
    
    # Tampilkan statistik deskriptif untuk kolom numerik
    if numeric_cols:
        st.subheader("Statistik Numerik Lengkap")
        
        # Bersihkan data dari nilai infinite
        clean_df = df[numeric_cols].replace([np.inf, -np.inf], np.nan)
        
        # Hitung berbagai statistik
        desc_stats = clean_df.describe()
        
        # Tambahkan statistik tambahan
        additional_stats = pd.DataFrame({
            'median': clean_df.median(),
            'variance': clean_df.var(),
            'skewness': clean_df.skew(),
            'kurtosis': clean_df.kurtosis(),
            'range': clean_df.max() - clean_df.min(),
            'Q1': clean_df.quantile(0.25),
            'Q3': clean_df.quantile(0.75),
            'IQR': clean_df.quantile(0.75) - clean_df.quantile(0.25)
        }).T
        
        # Gabungkan dengan statistik deskriptif standar
        full_stats = pd.concat([desc_stats, additional_stats])
        st.markdown(full_stats.to_html(classes='data-table', escape=False), unsafe_allow_html=True)
        
        # Uji normalitas untuk setiap kolom numerik
        st.subheader("Uji Normalitas (Shapiro-Wilk)")
        normality_results = []
        for col in numeric_cols:
            # Bersihkan data dari nilai infinite dan NaN
            data = df[col].replace([np.inf, -np.inf], np.nan).dropna()
            if len(data) > 3 and len(data) < 5000:  # Shapiro-Wilk bekerja untuk 3 < n < 5000
                try:
                    stat, p_value = stats.shapiro(data)
                    normality_results.append({
                        'Kolom': col,
                        'Statistik': f"{stat:.4f}",
                        'p-value': f"{p_value:.4f}",
                        'Normal': "Ya" if p_value > 0.05 else "Tidak"
                    })
                except Exception as e:
                    normality_results.append({
                        'Kolom': col,
                        'Statistik': f"Error: {str(e)}",
                        'p-value': "Error",
                        'Normal': "Error"
                    })
            else:
                normality_results.append({
                    'Kolom': col,
                    'Statistik': "N/A",
                    'p-value': "N/A",
                    'Normal': "Sample size tidak sesuai"
                })
        
        normality_df = pd.DataFrame(normality_results)
        st.markdown(normality_df.to_html(classes='data-table', escape=False, index=False), unsafe_allow_html=True)
    
    # Tampilkan informasi tentang missing values
    st.subheader("Informasi Missing Values")
    missing_data = df.isnull().sum()
    missing_df = pd.DataFrame({
        'Kolom': missing_data.index,
        'Jumlah Missing': missing_data.values,
        'Persentase Missing': (missing_data.values / len(df)) * 100
    })
    st.markdown(missing_df.to_html(classes='data-table', escape=False, index=False), unsafe_allow_html=True)
    
    # Tampilkan informasi tentang infinite values
    st.subheader("Informasi Infinite Values")
    if numeric_cols:
        inf_data = {}
        for col in numeric_cols:
            inf_count = np.isinf(df[col]).sum()
            inf_data[col] = inf_count
        
        inf_df = pd.DataFrame({
            'Kolom': list(inf_data.keys()),
            'Jumlah Infinite': list(inf_data.values()),
            'Persentase Infinite': [f"{(v / len(df)) * 100:.2f}%" for v in inf_data.values()]
        })
        st.markdown(inf_df.to_html(classes='data-table', escape=False, index=False), unsafe_allow_html=True)
    
    # Tampilkan informasi tipe data
    st.subheader("Informasi Tipe Data")
    dtype_info = pd.DataFrame({
        'Kolom': df.columns,
        'Tipe Data': df.dtypes.values,
        'Nilai Unik': [df[col].nunique() for col in df.columns]
    })
    st.markdown(dtype_info.to_html(classes='data-table', escape=False, index=False), unsafe_allow_html=True)
    
    # Analisis trend saham jika ada kolom yang sesuai
    analyze_stock_trends(df)

# Fungsi untuk menganalisis trend saham naik/turun
def analyze_stock_trends(df):
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    date_cols = df.select_dtypes(include=['datetime64']).columns.tolist()
    
    if not date_cols:
        # Coba konversi kolom string ke datetime
        for col in df.columns:
            if df[col].dtype == 'object':
                try:
                    df[col] = pd.to_datetime(df[col])
                    date_cols.append(col)
                    break
                except:
                    pass
    
    if date_cols and numeric_cols:
        st.subheader("Analisis Trend Saham")
        
        date_col = st.selectbox("Pilih kolom tanggal", date_cols)
        price_col = st.selectbox("Pilih kolom harga", numeric_cols)
        
        try:
            # Pastikan data diurutkan berdasarkan tanggal
            df_sorted = df.sort_values(by=date_col).copy()
            
            # Bersihkan data dari nilai infinite
            df_sorted[price_col] = df_sorted[price_col].replace([np.inf, -np.inf], np.nan)
            df_sorted = df_sorted.dropna(subset=[price_col])
            
            # Hitung perubahan harga
            df_sorted['Perubahan'] = df_sorted[price_col].pct_change() * 100
            df_sorted['Perubahan_Abs'] = df_sorted[price_col].diff()
            
            # Hitung statistik trend
            total_days = len(df_sorted)
            up_days = len(df_sorted[df_sorted['Perubahan_Abs'] > 0])
            down_days = len(df_sorted[df_sorted['Perubahan_Abs'] < 0])
            flat_days = len(df_sorted[df_sorted['Perubahan_Abs'] == 0])
            
            avg_change = df_sorted['Perubahan'].mean()
            max_gain = df_sorted['Perubahan'].max()
            max_loss = df_sorted['Perubahan'].min()
            
            # Tampilkan metrik trend
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                trend_icon = "📈" if avg_change > 0 else "📉"
                st.metric(f"Rata-rata Perubahan {trend_icon}", f"{avg_change:.2f}%")
            
            with col2:
                st.metric("Hari Naik", f"{up_days} ({up_days/total_days*100:.1f}%)")
            
            with col3:
                st.metric("Hari Turun", f"{down_days} ({down_days/total_days*100:.1f}%)")
            
            with col4:
                st.metric("Hari Datar", f"{flat_days} ({flat_days/total_days*100:.1f}%)")
            
            # Analisis volatilitas
            st.subheader("Analisis Volatilitas")
            
            # Hitung volatilitas (standar deviasi dari perubahan harga)
            volatility = df_sorted['Perubahan'].std()
            
            # Hitung moving averages
            df_sorted['MA_7'] = df_sorted[price_col].rolling(window=7).mean()
            df_sorted['MA_20'] = df_sorted[price_col].rolling(window=20).mean()
            
            # Hitung RSI (Relative Strength Index)
            delta = df_sorted[price_col].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            df_sorted['RSI'] = 100 - (100 / (1 + rs))
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Volatilitas (Std Dev)", f"{volatility:.2f}%")
            
            with col2:
                # Tentukan apakah dalam kondisi overbought atau oversold berdasarkan RSI
                if 'RSI' in df_sorted.columns and not df_sorted['RSI'].isna().all():
                    latest_rsi = df_sorted['RSI'].iloc[-1]
                    rsi_status = "Overbought (>70)" if latest_rsi > 70 else "Oversold (<30)" if latest_rsi < 30 else "Netral"
                    st.metric("RSI Terakhir", f"{latest_rsi:.2f}", rsi_status)
            
            with col3:
                # Tentukan trend berdasarkan moving averages
                if 'MA_7' in df_sorted.columns and 'MA_20' in df_sorted.columns:
                    latest_ma7 = df_sorted['MA_7'].iloc[-1]
                    latest_ma20 = df_sorted['MA_20'].iloc[-1]
                    ma_trend = "Uptrend" if latest_ma7 > latest_ma20 else "Downtrend"
                    st.metric("Trend MA", ma_trend)
            
            # Tampilkan grafik harga dengan matplotlib
            st.subheader("Grafik Harga dengan Analisis Teknikal")
            
            fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 10))
            
            # Plot harga dan moving averages
            ax1.plot(df_sorted[date_col], df_sorted[price_col], label='Harga', color='blue', linewidth=1)
            if 'MA_7' in df_sorted.columns:
                ax1.plot(df_sorted[date_col], df_sorted['MA_7'], label='MA 7', color='orange', linewidth=1)
            if 'MA_20' in df_sorted.columns:
                ax1.plot(df_sorted[date_col], df_sorted['MA_20'], label='MA 20', color='red', linewidth=1)
            ax1.set_ylabel('Harga')
            ax1.set_title('Harga dan Moving Averages')
            ax1.grid(True)
            ax1.legend()
            
            # Format tanggal pada sumbu x
            ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
            ax1.xaxis.set_major_locator(mdates.MonthLocator())
            plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45)
            
            # Plot perubahan harga
            colors = ['green' if x >= 0 else 'red' for x in df_sorted['Perubahan_Abs']]
            ax2.bar(df_sorted[date_col], df_sorted['Perubahan_Abs'], color=colors, alpha=0.7)
            ax2.set_ylabel('Perubahan')
            ax2.set_title('Perubahan Harga Harian')
            ax2.grid(True)
            
            # Format tanggal pada sumbu x
            ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
            ax2.xaxis.set_major_locator(mdates.MonthLocator())
            plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45)
            
            # Plot RSI jika tersedia
            if 'RSI' in df_sorted.columns:
                ax3.plot(df_sorted[date_col], df_sorted['RSI'], label='RSI', color='purple', linewidth=1)
                ax3.axhline(y=70, color='r', linestyle='--', alpha=0.7, label='Overbought (70)')
                ax3.axhline(y=30, color='g', linestyle='--', alpha=0.7, label='Oversold (30)')
                ax3.set_ylabel('RSI')
                ax3.set_title('Relative Strength Index (RSI)')
                ax3.grid(True)
                ax3.legend()
                
                # Format tanggal pada sumbu x
                ax3.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
                ax3.xaxis.set_major_locator(mdates.MonthLocator())
                plt.setp(ax3.xaxis.get_majorticklabels(), rotation=45)
            
            plt.tight_layout()
            st.pyplot(fig)
            
            # Tampilkan sinyal trading sederhana
            st.subheader("Sinyal Trading Sederhana")
            
            if 'RSI' in df_sorted.columns and 'MA_7' in df_sorted.columns and 'MA_20' in df_sorted.columns:
                # Ambil data terbaru
                latest_data = df_sorted.iloc[-1]
                
                # Generate sinyal berdasarkan RSI dan MA
                signals = []
                
                if latest_data['RSI'] < 30 and latest_data['MA_7'] > latest_data['MA_20']:
                    signals.append(("BUY", "RSI oversold dan MA7 > MA20"))
                elif latest_data['RSI'] > 70 and latest_data['MA_7'] < latest_data['MA_20']:
                    signals.append(("SELL", "RSI overbought dan MA7 < MA20"))
                elif latest_data['RSI'] < 30:
                    signals.append(("POTENTIAL BUY", "RSI oversold"))
                elif latest_data['RSI'] > 70:
                    signals.append(("POTENTIAL SELL", "RSI overbought"))
                elif latest_data['MA_7'] > latest_data['MA_20']:
                    signals.append(("BULLISH", "MA7 > MA20 (Uptrend)"))
                elif latest_data['MA_7'] < latest_data['MA_20']:
                    signals.append(("BEARISH", "MA7 < MA20 (Downtrend)"))
                else:
                    signals.append(("NEUTRAL", "Tidak ada sinyal kuat"))
                
                # Tampilkan sinyal
                for signal, reason in signals:
                    if signal == "BUY":
                        st.success(f"🚀 {signal}: {reason}")
                    elif signal == "SELL":
                        st.error(f"🔻 {signal}: {reason}")
                    elif signal in ["POTENTIAL BUY", "BULLISH"]:
                        st.info(f"📈 {signal}: {reason}")
                    elif signal in ["POTENTIAL SELL", "BEARISH"]:
                        st.warning(f"📉 {signal}: {reason}")
                    else:
                        st.info(f"📊 {signal}: {reason}")
            
        except Exception as e:
            st.error(f"Error dalam analisis trend: {str(e)}")

# Fungsi untuk membuat file contoh dengan data saham
def create_sample_file():
    dates = pd.date_range(start='2023-01-01', periods=100, freq='D')
    
    # Generate harga saham dengan random walk
    np.random.seed(42)
    price_changes = np.random.normal(0.001, 0.02, len(dates))
    prices = 100 * (1 + price_changes).cumprod()
    
    # Generate volume
    volumes = np.random.randint(1000, 10000, len(dates))
    
    example_data = pd.DataFrame({
        'Tanggal': dates,
        'Open': prices * (1 + np.random.normal(0, 0.01, len(dates))),
        'High': prices * (1 + np.abs(np.random.normal(0.005, 0.01, len(dates)))),
        'Low': prices * (1 - np.abs(np.random.normal(0.005, 0.01, len(dates)))),
        'Close': prices,
        'Volume': volumes,
        'Perusahaan': np.random.choice(['AAPL', 'GOOGL', 'MSFT', 'AMZN'], len(dates)),
        'Sektor': np.random.choice(['Teknologi', 'Kesehatan', 'Finansial', 'Konsumsi'], len(dates))
    })
    
    # Adjust OHLC untuk konsistensi
    for i in range(len(example_data)):
        example_data.loc[i, 'High'] = max(example_data.loc[i, 'Open'], example_data.loc[i, 'Close'], example_data.loc[i, 'High'])
        example_data.loc[i, 'Low'] = min(example_data.loc[i, 'Open'], example_data.loc[i, 'Close'], example_data.loc[i, 'Low'])
    
    return example_data

# Fungsi untuk analisis korelasi antar saham
def analyze_stock_correlation(df):
    st.header("Analisis Korelasi Antar Saham")
    
    # Identifikasi kolom yang mungkin berisi data harga saham
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    date_cols = df.select_dtypes(include=['datetime64']).columns.tolist()
    
    if not date_cols:
        for col in df.columns:
            if df[col].dtype == 'object':
                try:
                    df[col] = pd.to_datetime(df[col])
                    date_cols.append(col)
                    break
                except:
                    pass
    
    if date_cols and len(numeric_cols) > 1:
        date_col = st.selectbox("Pilih kolom tanggal untuk analisis korelasi", date_cols)
        price_cols = st.multiselect("Pilih kolom harga untuk analisis korelasi", numeric_cols, default=numeric_cols[:min(5, len(numeric_cols))])
        
        if len(price_cols) > 1:
            try:
                # Pastikan data diurutkan berdasarkan tanggal
                df_sorted = df.sort_values(by=date_col).copy()
                
                # Bersihkan data dari nilai infinite dan NaN
                clean_data = df_sorted[price_cols].replace([np.inf, -np.inf], np.nan).dropna()
                
                if len(clean_data) > 1:
                    # Hitung korelasi
                    correlation_matrix = clean_data.corr()
                    
                    # Tampilkan heatmap korelasi
                    fig = px.imshow(correlation_matrix, 
                                   text_auto=True, 
                                   aspect="auto", 
                                   title="Korelasi Antar Saham",
                                   color_continuous_scale='RdBu_r',
                                   zmin=-1, zmax=1)
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Tampilkan matriks korelasi sebagai tabel
                    st.subheader("Matriks Korelasi")
                    st.dataframe(correlation_matrix.style.background_gradient(cmap='RdBu_r', vmin=-1, vmax=1).format("{:.2f}"))
                    
                    # Analisis pasangan dengan korelasi tertinggi dan terendah
                    st.subheader("Pasangan dengan Korelasi Ekstrem")
                    
                    # Dapatkan pasangan dengan korelasi tertinggi dan terendah
                    corr_pairs = []
                    for i in range(len(correlation_matrix.columns)):
                        for j in range(i+1, len(correlation_matrix.columns)):
                            corr_pairs.append({
                                'Pair': f"{correlation_matrix.columns[i]} - {correlation_matrix.columns[j]}",
                                'Correlation': correlation_matrix.iloc[i, j]
                            })
                    
                    corr_df = pd.DataFrame(corr_pairs)
                    top_corr = corr_df.nlargest(3, 'Correlation')
                    bottom_corr = corr_df.nsmallest(3, 'Correlation')
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("**Korelasi Tertinggi**")
                        for _, row in top_corr.iterrows():
                            st.write(f"{row['Pair']}: {row['Correlation']:.3f}")
                    
                    with col2:
                        st.markdown("**Korelasi Terendah**")
                        for _, row in bottom_corr.iterrows():
                            st.write(f"{row['Pair']}: {row['Correlation']:.3f}")
                
                else:
                    st.error("Tidak cukup data untuk analisis korelasi setelah pembersihan")
            except Exception as e:
                st.error(f"Error dalam analisis korelasi: {str(e)}")
        else:
            st.error("Pilih setidaknya 2 kolom harga untuk analisis korelasi")
    else:
        st.error("Data tidak memiliki cukup kolom tanggal atau numerik untuk analisis korelasi")

# UI utama
st.markdown('<h1 class="main-header">📊 Dashboard Statistik Profesional</h1>', unsafe_allow_html=True)
st.markdown("Unggah file CSV atau Excel untuk melihat visualisasi dan statistik data.")

# Sidebar untuk upload file dan kontrol
st.sidebar.header("Kontrol Aplikasi")

# Tombol untuk membuat dan mengunduh file contoh
if st.sidebar.button("Buat File Contoh"):
    example_data = create_sample_file()
    csv = example_data.to_csv(index=False)
    st.sidebar.download_button(
        label="Unduh Contoh CSV",
        data=csv,
        file_name="contoh_data_saham.csv",
        mime="text/csv"
    )

# Fitur untuk mengunggah dan menggabungkan beberapa file
st.sidebar.header("Unggah & Gabungkan Beberapa File")
uploaded_files = st.sidebar.file_uploader(
    "Pilih file CSV atau Excel (bisa multiple)",
    type=['csv', 'xlsx', 'xls'],
    help="Format yang didukung: CSV, XLSX, XLS",
    accept_multiple_files=True
)

# Pilihan metode penggabungan jika ada beberapa file
merge_method = "concat"
if uploaded_files and len(uploaded_files) > 1:
    merge_method = st.sidebar.selectbox(
        "Metode Penggabungan Data",
        ["concat", "inner", "outer", "left", "right"],
        help="Concat: menggabungkan baris, lainnya: menggabungkan berdasarkan kolom"
    )

# Proses file yang diupload
df = None
if uploaded_files:
    datasets = []
    for uploaded_file in uploaded_files:
        dataset = process_uploaded_file(uploaded_file)
        if dataset is not None:
            datasets.append(dataset)
            st.sidebar.success(f"File berhasil diunggah: {uploaded_file.name}")
    
    if datasets:
        if len(datasets) == 1:
            df = datasets[0]
        else:
            df = merge_datasets(datasets, merge_method)
            st.sidebar.success(f"Berhasil menggabungkan {len(datasets)} dataset")

# Jika file sudah diupload
if df is not None:
    # Tampilkan statistik
    show_statistics(df)
    
    # Tampilkan visualisasi
    st.header("Visualisasi Data")
    create_visualizations(df)
    
    # Analisis korelasi antar saham
    analyze_stock_correlation(df)
    
    # Tambahkan opsi untuk mengunduh data yang telah diproses
    st.sidebar.header("Unduh Data")
    if st.sidebar.button("Unduh Data yang Telah Diproses"):
        csv = df.to_csv(index=False)
        st.sidebar.download_button(
            label="Unduh sebagai CSV",
            data=csv,
            file_name="processed_data.csv",
            mime="text/csv"
        )
        
else:
    # Tampilkan contoh data jika belum ada file yang diupload
    st.info("Silakan unggah file CSV atau Excel melalui sidebar di sebelah kiri.")
    
    # Buat contoh data
    st.subheader("Contoh Data")
    example_data = create_sample_file()
    display_dataframe(example_data)
    
    # Tampilkan contoh visualisasi
    st.subheader("Contoh Visualisasi")
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig_example = px.line(example_data, x='Tanggal', y='Close', title='Contoh Trend Harga Saham')
        st.plotly_chart(fig_example, use_container_width=True)
    
    with col2:
        # Pie chart contoh
        sector_data = example_data.groupby('Sektor')['Volume'].sum().reset_index()
        fig_pie = px.pie(sector_data, names='Sektor', values='Volume', title='Volume Perdagangan per Sektor')
        st.plotly_chart(fig_pie, use_container_width=True)

# Footer
st.markdown("---")
st.markdown("Dashboard Statistik © 2025 - Dibuat oleh Dwi Bakti N Dev")