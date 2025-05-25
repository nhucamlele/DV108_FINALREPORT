from django.shortcuts import render
import pandas as pd
import json
import os
from django.conf import settings
from django.http import HttpResponse
import seaborn as sns
import os
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from django.conf import settings
from django.shortcuts import render

import os
import io
import base64
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import matplotlib.patches as mpatches
from matplotlib.cm import Greens, Blues, Oranges
from matplotlib.ticker import FuncFormatter

from django.conf import settings
from django.shortcuts import render
import plotly.graph_objs as go

def load_or_cache_csv():
    csv_path = os.path.join(settings.BASE_DIR, 'dashboard', 'data', 'D108.csv')
    pkl_path = os.path.join(settings.BASE_DIR, 'dashboard', 'data', 'D108.pkl')

    if os.path.exists(pkl_path):
        print("Đọc dữ liệu từ file cache D108.pkl")
        return pd.read_pickle(pkl_path)
    
    print("Đọc từ CSV và tạo file cache D108.pkl")
    df = pd.read_csv(csv_path, low_memory=False)
    df.to_pickle(pkl_path)
    return df
def dashboard_all_charts(request):
    blue_pink_palette = [
        '#0d47a1', 
        '#1976d2', 
        '#64b5f6', 
        '#880e4f', 
        '#c2185b',  
        '#f06292'  
    ]
    csv_path = os.path.join(settings.BASE_DIR, 'dashboard', 'data', 'D108.csv')
    df = pd.read_csv(csv_path, low_memory=False)
    df['datetime'] = pd.to_datetime(df['datetime'], errors='coerce')
    # === 1. Data cho chart_bar_category (BD1) ===
    df_grouped = df.groupby('Product_Category')['Total_Purchases'].sum().reset_index()
    df_sorted = df_grouped.sort_values(by='Total_Purchases', ascending=False)
    categories = df_sorted['Product_Category'].tolist()
    totals = df_sorted['Total_Purchases'].tolist()
    colors_bd1 = [blue_pink_palette[i % len(blue_pink_palette)] for i in range(len(categories))]
    # === 2. Data cho chart_stacked_feedback (BD2) ===
    feedback_df = df.groupby(['Product_Category', 'Feedback']).size().unstack(fill_value=0)
    feedback_order = ['Excellent', 'Good', 'Average', 'Bad']
    feedback_df = feedback_df.reindex(columns=feedback_order, fill_value=0)
    percent_feedback_df = feedback_df.div(feedback_df.sum(axis=1), axis=0) * 100
    categories_bd2 = percent_feedback_df.index.tolist()
    methods_bd2 = percent_feedback_df.columns.tolist()
    datasets_bd2 = []
    for i, method in enumerate(methods_bd2):
        datasets_bd2.append({
            'label': method,
            'data': percent_feedback_df[method].round(2).tolist(),
            'backgroundColor': blue_pink_palette[i % len(blue_pink_palette)],
        })
    # === 3. Data cho chart_treemap (BD3) ===
    product_sales = df.groupby('products')['Total_Purchases'].sum().sort_values(ascending=False).head(20)
    labels_bd3 = product_sales.index.tolist()
    values_bd3 = product_sales.values.tolist()
    colors_bd3 = [blue_pink_palette[i % len(blue_pink_palette)] for i in range(len(labels_bd3))]
    # === 4. Data cho chart_line_monthly (BD4) ===
    monthly_sales = df.groupby([df['datetime'].dt.month.rename('Month'), 'Product_Category'])['Total_Purchases'].sum().reset_index()
    months_bd4 = list(range(1, 13))
    categories_bd4 = monthly_sales['Product_Category'].unique()
    colors_bd4 = [blue_pink_palette[i % len(blue_pink_palette)] for i in range(len(categories_bd4))]
    datasets_bd4 = []
    for i, category in enumerate(categories_bd4):
        data_by_month = []
        for month in months_bd4:
            filtered = monthly_sales[(monthly_sales['Month'] == month) & (monthly_sales['Product_Category'] == category)]
            value = filtered['Total_Purchases'].values[0] if not filtered.empty else 0
            data_by_month.append(value)
        datasets_bd4.append({
            'label': category,
            'data': data_by_month,
            'fill': False,
            'borderColor': colors_bd4[i],
            'tension': 0.3,  
        })
    # === 5. Data cho chart_combined_brand_sales_rating (BD5) ===
    df['Rating'] = pd.to_numeric(df['Ratings'], errors='coerce')
    df_clean_rating = df.dropna(subset=['Rating'])
    brand_stats = df_clean_rating.groupby('Product_Brand').agg(total_sales=('Total_Purchases', 'sum'), avg_rating=('Rating', 'mean')).reset_index()
    brand_stats = brand_stats.sort_values(by='total_sales', ascending=False)
    labels_bd5 = brand_stats['Product_Brand'].tolist()
    total_sales_bd5 = brand_stats['total_sales'].tolist()
    avg_ratings_bd5 = brand_stats['avg_rating'].round(2).tolist()
    # === 6. Data cho chart_bd6_stacked_shipping (BD6) ===
    count_df = df.groupby(['Product_Type', 'Shipping_Method']).size().unstack(fill_value=0)
    percent_df = count_df.div(count_df.sum(axis=1), axis=0) * 100
    categories_bd6 = percent_df.index.tolist()
    methods_bd6 = percent_df.columns.tolist()
    datasets_bd6 = []
    for i, method in enumerate(methods_bd6):
        datasets_bd6.append({
            'label': method,
            'data': percent_df[method].round(2).tolist(),
            'backgroundColor': blue_pink_palette[i % len(blue_pink_palette)],
        })
    # === 7. Data cho chart_top_products_by_country (BD7) ===
    top_countries = df.groupby('Country')['Total_Purchases'].sum().nlargest(5).index.tolist()
    df_top = df[df['Country'].isin(top_countries)]
    final_data_bd7 = []
    for country in top_countries:
        df_country = df_top[df_top['Country'] == country]
        top_products = df_country.groupby('products')['Total_Purchases'].sum().nlargest(5).reset_index()
        for _, row in top_products.iterrows():
            final_data_bd7.append({
                'country': country,
                'product': row['products'],
                'total': row['Total_Purchases']
            })
    context = {
        'bd1': {
            'categories': categories,
            'totals': totals,
            'colors': colors_bd1,
        },
        'bd2': {
            'categories': categories_bd2,
            'datasets': datasets_bd2,
        },
        'bd3': {
            'labels': labels_bd3,
            'values': values_bd3,
            'colors': colors_bd3,
        },
        'bd4': {
            'months': months_bd4,
            'datasets': datasets_bd4,
            'colors': colors_bd4,
        },
        'bd5': {
            'labels': labels_bd5,
            'total_sales': total_sales_bd5,
            'avg_ratings': avg_ratings_bd5,
        },
        'bd6': {
            'categories': categories_bd6,
            'datasets': datasets_bd6,
        },
        'bd7': {
            'chart_data': final_data_bd7,
        }
    }
    context_json = {k: json.dumps(v) for k, v in context.items()}
    return render(request, 'dashboard/product.html', context_json)

def customer_dashboard(request):
    csv_path = os.path.join(settings.BASE_DIR, 'dashboard', 'data', 'D108.csv')
    df = pd.read_csv(csv_path, low_memory=False)
    # Biểu đồ 1: Customer Segment (bar chart)
    blue_pink_palette = [
    '#0d47a1',  # Xanh dương đậm (blue navy) – làm nền hoặc tiêu đề chính
    '#1976d2',  # Xanh dương trung bình – nút chính, đường viền nổi bật
    '#64b5f6',  # Xanh dương sáng – background phụ hoặc hover
    '#880e4f',  # Hồng đậm ánh tím – nhấn mạnh, nút hành động
    '#c2185b',  # Hồng rực – dùng để thu hút sự chú ý
    '#f06292'   # Hồng pastel – tạo sự mềm mại, nhẹ nhàng, nền nhẹ
    ]


    segment_counts = df.groupby('Customer_Segment')['Customer_ID'].nunique().sort_values(ascending=False).reset_index()
    fig1 = px.bar(
        segment_counts,
        x='Customer_ID',
        y='Customer_Segment',
        orientation='h',
        color='Customer_Segment',
        labels={'Customer_ID': 'Số lượng khách hàng', 'Customer_Segment': 'Phân khúc'},
        color_discrete_sequence=blue_pink_palette
    )
    fig1.update_layout(yaxis=dict(categoryorder='total ascending'))
    chart1_html = fig1.to_html(full_html=False)


    # Biểu đồ 2: Heatmap phân khúc - thu nhập
    heatmap_data = df.pivot_table(index='Customer_Segment', columns='Income', values='Customer_ID', aggfunc='nunique', fill_value=0)
    fig2 = go.Figure(data=go.Heatmap(
        z=heatmap_data.values,
        x=heatmap_data.columns,
        y=heatmap_data.index,
        colorscale='Blues',
        hoverongaps=False,
        colorbar=dict(title='Số KH')
    ))
    chart2_html = fig2.to_html(full_html=False)


    # Biểu đồ 3: Pie chart giới tính khách hàng
    gender_counts = df.groupby('Gender')['Customer_ID'].nunique().reset_index()
    fig3 = px.pie(
        gender_counts,
        values='Customer_ID',
        names='Gender',
        color_discrete_sequence=blue_pink_palette
    )
    chart3_html = fig3.to_html(full_html=False)


    # Biểu đồ 4: Choropleth khách hàng theo quốc gia
    country_counts = df.groupby('Country')['Customer_ID'].nunique().reset_index()
    fig4 = px.choropleth(
        country_counts,
        locations="Country",
        locationmode='country names',
        color="Customer_ID",
        color_continuous_scale="Blues",
        labels={'Customer_ID': 'Số lượng khách hàng'}
    )
    fig4.update_layout(margin=dict(r=0, t=30, l=0, b=0))
    chart4_html = fig4.to_html(full_html=False)


    # Biểu đồ 5: Khách hàng theo độ tuổi và số đơn hàng trung bình
    df_age = pd.read_csv(os.path.join(settings.BASE_DIR, 'dashboard', 'data', 'D108.csv'), low_memory=False)


    def age_group(age):
        if 18 <= age <= 24:
            return "18-24"
        elif age <= 34:
            return "25-34"
        elif age <= 44:
            return "35-44"
        elif age <= 54:
            return "45-54"
        else:
            return "55+"


    df_age['Age_Group'] = df_age['Age'].apply(age_group)
    customer_counts = df_age.groupby('Age_Group')['Customer_ID'].nunique()
    transactions_per_customer = df_age.groupby(['Age_Group', 'Customer_ID'])['Transaction_ID'].nunique()
    avg_transactions = transactions_per_customer.groupby('Age_Group').mean()
    age_order = ['18-24', '25-34', '35-44', '45-54', '55+']
    plot_df = pd.DataFrame({'Customer_Count': customer_counts, 'Avg_Transactions': avg_transactions}).reindex(age_order).reset_index()


    fig5 = go.Figure()
    fig5.add_bar(x=plot_df['Age_Group'], y=plot_df['Customer_Count'], name='Số KH', marker_color='#1976d2')
    fig5.add_trace(go.Scatter(x=plot_df['Age_Group'], y=plot_df['Avg_Transactions'],
                              mode='lines+markers+text', name='Số đơn hàng TB',
                              text=[f'{v:.1f}' for v in plot_df['Avg_Transactions']],
                              textposition='top center', line=dict(color='red')))
    fig5.update_layout(
        yaxis=dict(title='Số KH'),
        yaxis2=dict(overlaying='y', side='right', title='Số đơn hàng TB'),
    )
    chart5_html = fig5.to_html(full_html=False)


    # Biểu đồ 6: Tỷ lệ khách hàng theo thu nhập
    income_customer_counts = df_age.groupby('Income')['Customer_ID'].nunique().reset_index()
    income_customer_counts['Percent'] = (income_customer_counts['Customer_ID'] / income_customer_counts['Customer_ID'].sum()) * 100


    fig6 = px.pie(
        income_customer_counts,
        names='Income',
        values='Customer_ID',
        color_discrete_sequence=blue_pink_palette
    )
    chart6_html = fig6.to_html(full_html=False)


    context = {
        'chart1_html': chart1_html,
        'chart2_html': chart2_html,
        'chart3_html': chart3_html,
        'chart4_html': chart4_html,
        'chart5_html': chart5_html,
        'chart6_html': chart6_html,
    }


    return render(request, 'dashboard/customer.html', context)

def sales_dashboard(request):
    blue_pink_palette = [
    '#0d47a1',  # Xanh dương đậm (blue navy)
    '#1976d2',  # Xanh dương trung bình
    '#64b5f6',  # Xanh dương sáng
    '#880e4f',  # Hồng đậm ánh tím
    '#c2185b',  # Hồng rực
    '#f06292'   # Hồng pastel
]
   
    csv_path = os.path.join(settings.BASE_DIR, 'dashboard', 'data', 'D108.csv')
    df = pd.read_csv(csv_path, low_memory=False)


    df['datetime'] = pd.to_datetime(df['datetime'])
    df['Year'] = df['datetime'].dt.year
    df['Month'] = df['datetime'].dt.month
    df['Total_Purchases'] = pd.to_numeric(df['Total_Purchases'], errors='coerce').fillna(0)


    # === CHART 1: Doanh thu hàng tháng ===
    monthly = df.groupby(['Year', 'Month']).agg({
        'Total_Amount': lambda x: x.sum() / 1000,
        'Amount': 'sum',
        'Transaction_ID': 'count'
    }).reset_index()
    pivot_sales = monthly.pivot(index='Month', columns='Year', values='Total_Amount')


    chart1_html = "<p style='color:red'>Không đủ dữ liệu cho cả năm 2023 và 2024 để hiển thị biểu đồ.</p>"
    if 2023 in pivot_sales.columns and 2024 in pivot_sales.columns:
        fig1 = go.Figure()
        fig1.add_trace(go.Scatter(x=pivot_sales.index, y=pivot_sales[2023], name='2023',
                                  line=dict(color='#64b5f6', dash='dash'), mode='lines+markers'))
        fig1.add_trace(go.Scatter(x=pivot_sales.index, y=pivot_sales[2024], name='2024',
                                  line=dict(color='#1976d2'), mode='lines+markers'))


        min_month = pivot_sales[2024].idxmin()
        max_month = pivot_sales[2024].idxmax()
        fig1.add_trace(go.Scatter(x=[min_month], y=[pivot_sales[2024][min_month]],
                                  mode='markers+text', marker=dict(color='#880e4f', size=10),
                                  name='Min 2024', text=["Min"], textposition="top center"))
        fig1.add_trace(go.Scatter(x=[max_month], y=[pivot_sales[2024][max_month]],
                                  mode='markers+text', marker=dict(color='#0d47a1', size=10),
                                  name='Max 2024', text=["Max"], textposition="top center"))


        fig1.update_layout(xaxis_title='Tháng', yaxis_title='Doanh thu (K USD)',
                           template='plotly_white', height=500)
        chart1_html = fig1.to_html(full_html=False)


    # === CHART 2: Tổng lượt mua hàng ===
    monthly_sales = df.groupby(['Year', 'Month'])['Total_Purchases'].sum().reset_index()
    pivot_purchases = monthly_sales.pivot(index='Month', columns='Year', values='Total_Purchases').fillna(0)


    fig2 = go.Figure()
    colors = ['#64b5f6', '#1976d2']  # xanh đậm, xanh nhạt


    for i, year in enumerate(pivot_purchases.columns):
        fig2.add_trace(go.Scatter(
            x=pivot_purchases.index,
            y=pivot_purchases[year],
            name=str(year),
            mode='lines+markers',
                    line=dict(
            color=colors[i % len(colors)],
            dash='dash' if year == 2023 else 'solid')  # nét đứt cho năm 2023
        ))


    if 2024 in pivot_purchases.columns:
        min_month = pivot_purchases[2024].idxmin()
        max_month = pivot_purchases[2024].idxmax()
        fig2.add_trace(go.Scatter(x=[min_month], y=[pivot_purchases.loc[min_month, 2024]],
                                mode='markers+text', marker=dict(color='#880e4f', size=10),
                                name='Min 2024', text=["Min"], textposition="top center"))
        fig2.add_trace(go.Scatter(x=[max_month], y=[pivot_purchases.loc[max_month, 2024]],
                                mode='markers+text', marker=dict(color='#0d47a1', size=10),
                                name='Max 2024', text=["Max"], textposition="top center"))


    fig2.update_layout(
                    xaxis_title='Tháng', yaxis_title='Tổng mua hàng',
                    template='plotly_white', height=500)


    chart2_html = fig2.to_html(full_html=False)




    # === CHART 3: Số đơn hàng theo tháng (Matplotlib) ===
    monthly_orders = df.groupby(['Year', 'Month'])['Transaction_ID'].nunique().reset_index()
    pivot_orders = monthly_orders.pivot(index='Month', columns='Year', values='Transaction_ID')
    plt.figure(figsize=(10, 6))
    fig3 = go.Figure()
    for i, year in enumerate(pivot_orders.columns):
        fig3.add_trace(go.Scatter(
            x=pivot_orders.index,
            y=pivot_orders[year],
            name=str(year),
            mode='lines+markers',
            line=dict(
            color=colors[i % len(colors)],
            dash='dash' if year == 2023 else 'solid')  # nét đứt cho năm 2023
        ))


    if 2024 in pivot_orders.columns:
        min_m = pivot_orders[2024].idxmin()
        max_m = pivot_orders[2024].idxmax()
        fig3.add_trace(go.Scatter(x=[min_m], y=[pivot_orders.loc[min_m, 2024]],
                                mode='markers+text', marker=dict(color='#880e4f', size=10),
                                name='Min 2024', text=["Min"], textposition="top center"))
        fig3.add_trace(go.Scatter(x=[max_m], y=[pivot_orders.loc[max_m, 2024]],
                                mode='markers+text', marker=dict(color='#0d47a1', size=10),
                                name='Max 2024', text=["Max"], textposition="top center"))


    fig3.update_layout(
                    xaxis_title='Tháng', yaxis_title='Số đơn hàng',
                    template='plotly_white', height=500)


    chart3_html = fig3.to_html(full_html=False)


    # === CHART 4: Doanh thu theo quốc gia ===
    country_sales = df.groupby('Country')['Total_Amount'].sum().sort_values(ascending=False) / 1000
    country_sales = country_sales.round(2)


    fig4 = go.Figure(go.Bar(
        x=country_sales.values,
        y=country_sales.index,
        orientation='h',
        marker=dict(
            color=country_sales.values,      # dùng giá trị để tô màu
            colorscale='Blues',              # dùng bảng màu 'Blues'
            showscale=True                   # (tùy chọn) hiện thanh màu
        )
    ))


    fig4.update_layout(
        xaxis_title='Doanh thu (K USD)',
        yaxis=dict(autorange='reversed'),
        template='plotly_white',
        height=600
    )


    chart4_html = fig4.to_html(full_html=False)


    # === CHART: Top 5 sản phẩm doanh thu cao nhất (Plotly) ===
    if 'products' in df.columns and 'Total_Amount' in df.columns:
        product_sales = df.groupby('products')['Total_Amount'].sum().sort_values(ascending=False) / 1000
        top5_products = product_sales.head(5).round(2)


        # Đảo ngược để sản phẩm doanh thu cao nhất hiển thị trên cùng
        top5_products = top5_products[::-1]


        # Màu sắc: thanh cuối cùng là cao nhất nên đặt màu đậm
        colors = ['#64b5f6'] * 5
        colors[-1] = '#0d47a1'  # thanh cuối là cao nhất sau khi đảo ngược


        fig_top5 = go.Figure(go.Bar(
            x=top5_products.values,
            y=top5_products.index,
            orientation='h',
            marker=dict(color=colors),
            text=[f'{v:,.0f}K' for v in top5_products.values],
            textposition='outside'
        ))


        fig_top5.update_layout(
            xaxis_title='Doanh thu (K USD)',
            yaxis_title='',
            template='plotly_white',
            height=500,
            margin=dict(l=100, r=30, t=60, b=40)
        )


        chart5_html = fig_top5.to_html(full_html=False)
    else:
        chart5_html = ""


    # === CHART: Top 5 khách hàng có doanh thu cao nhất (Plotly) ===
    if 'Customer_ID' in df.columns and 'Total_Amount' in df.columns and 'Name' in df.columns:
        customer_sales = df.groupby('Customer_ID')['Total_Amount'].sum()
        customer_names = df.groupby('Customer_ID')['Name'].first()


        # Tạo bảng tổng hợp
        customer_summary = pd.DataFrame({
            'Total_Amount': customer_sales,
            'Name': customer_names
        })


        top5_customers = customer_summary.sort_values('Total_Amount', ascending=False).head(5)
        top5_customers['Total_Amount_K'] = (top5_customers['Total_Amount'] / 1000).round(2)


        # Đảo ngược để khách có doanh thu cao nhất hiển thị trên cùng
        top5_customers = top5_customers[::-1]


        # Màu sắc: thanh đầu đậm hơn
        colors = ['#64b5f6'] * 4 + ['#0d47a1']
        colors = colors[::-1]


        fig_top5_cust = go.Figure(go.Bar(
            x=top5_customers['Total_Amount_K'],
            y=top5_customers['Name'],
            orientation='h',
            marker=dict(color=colors),
            text=[f'{v:,.0f}K' for v in top5_customers['Total_Amount_K']],
            textposition='outside'
        ))


        fig_top5_cust.update_layout(
            xaxis_title='Doanh thu (K USD)',
            yaxis_title='',
            template='plotly_white',
            height=500,
            margin=dict(l=100, r=30, t=60, b=40)
        )


        chart6_html = fig_top5_cust.to_html(full_html=False)
    else:
        chart6_html = ""


    # === CHART: Tổng Doanh Thu Theo Danh Mục Sản Phẩm (Plotly) ===
    if 'Product_Category' in df.columns and 'Total_Amount' in df.columns:
        category_sales = df.groupby('Product_Category')['Total_Amount'].sum().sort_values(ascending=False)
        category_sales_k = (category_sales / 1000).round(2)


        fig_category = go.Figure(go.Bar(
            x=category_sales_k.index,
            y=category_sales_k.values,
            marker=dict(color='#1976d2'),
            text=[f'{v:,.0f}K' for v in category_sales_k.values],
            textposition='outside'
        ))


        fig_category.update_layout(
            xaxis_title='Danh mục sản phẩm',
            yaxis_title='Doanh thu (K USD)',
            template='plotly_white',
            height=500,
            margin=dict(l=60, r=30, t=60, b=100),
            xaxis_tickangle=-45
        )


        chart7_html = fig_category.to_html(full_html=False)
    else:
        chart7_html = ""




    context = {
        'chart1': chart1_html,
        'chart2': chart2_html,
        'chart3': chart3_html,
        'chart4': chart4_html,
        'chart5': chart5_html,
        'chart6': chart6_html,
        'chart7': chart7_html,
    }


    return render(request, 'dashboard/sale.html', context)
def dashboard_main(request):
    return render(request, 'dashboard/dashboard_main.html')