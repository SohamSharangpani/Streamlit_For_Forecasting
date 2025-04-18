# -*- coding: utf-8 -*-
"""Streamlit_For_Forecasting.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1mCHYFU1ftfQNgTn9ogcpop4oua6dkvEz

# Creating a Stremlit application for time series forecasting

## Group Memebrs

1. Francis Castro
2. Ryan Joseph
3. Soham Sharangpani
4. Wichayaporn Patadee

Setting up environment
"""

"""Importing Libraries"""

import streamlit as st
import pandas as pd
from sklearn.metrics import mean_squared_error, mean_absolute_error
from statsmodels.tsa.seasonal import seasonal_decompose
from statsmodels.tsa.holtwinters import SimpleExpSmoothing
import matplotlib.pyplot as plt
import numpy as np

"""Upload CSV"""

uploaded_file = st.file_uploader("Upload a CSV file containing date (DD-MM-YYYY) and a value", type=["csv"])

if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file)
        st.subheader("Uploaded Data Preview")
        st.dataframe(df.head())

        date_column = st.selectbox("Select the date column (DD-MM-YYYY)", df.columns)
        value_column = st.selectbox("Select the value column", df.columns)

        if date_column and value_column:
            try:
                df['ds'] = pd.to_datetime(df[date_column], format='%d-%m-%Y')
                df['y'] = pd.to_numeric(df[value_column])
                df = df[['ds', 'y']].sort_values('ds')
                df = df.set_index('ds')
                st.success("Data loaded and processed successfully!")
            except ValueError as e:
                st.error(f"Error processing date or value columns: {e}. Please ensure the date format is DD-MM-YYYY and the value column contains numbers.")
                st.stop()
    except Exception as e:
        st.error(f"Error reading CSV file: {e}")
        st.stop()

if 'df' in locals():
    st.subheader("Time Series Decomposition")
    decomposition_type = st.radio("Select decomposition type", ("Additive", "Multiplicative"))

    try:
        if decomposition_type == "Additive":
            decomposition = seasonal_decompose(df['y'], model='additive', period=30, extrapolate_trend='freq') # Adjust 'period' as needed
        else:
            decomposition = seasonal_decompose(df['y'], model='multiplicative', period=30, extrapolate_trend='freq') # Adjust 'period' as needed

        st.subheader("Decomposition Plots")
        fig, axes = plt.subplots(4, 1, figsize=(10, 8))
        decomposition.observed.plot(ax=axes[0], title='Observed')
        decomposition.trend.plot(ax=axes[1], title='Trend')
        decomposition.seasonal.plot(ax=axes[2], title='Seasonal')
        decomposition.resid.plot(ax=axes[3], title='Residual')
        plt.tight_layout()
        st.pyplot(fig)

    except Exception as e:
        st.error(f"Error performing decomposition: {e}. Ensure your data has enough points for meaningful decomposition and adjust the 'period' if necessary.")

if 'df' in locals():
    st.subheader("Forecasting")
    forecast_methods = st.multiselect("Select forecasting methods", ["Simple Moving Average", "Exponential Smoothing", "Lag Plot"])

def forecast_sma(data, window, periods):
    sma = data['y'].rolling(window=window).mean().shift(1)
    last_value = data['y'].iloc[-1]
    forecast_values = [last_value] * periods
    forecast_index = pd.date_range(start=data.index[-1], periods=periods + 1, freq=data.index.freq)[1:]
    forecast_series = pd.Series(forecast_values, index=forecast_index)
    return pd.concat([sma, forecast_series]).dropna()

def forecast_exponential_smoothing(data, periods, alpha=0.2):
    model = SimpleExpSmoothing(data['y']).fit(smoothing_level=alpha, optimized=False)
    forecast = model.forecast(periods)
    return forecast

def plot_lag(data, lag=1):
    plt.figure(figsize=(8, 6))
    pd.plotting.lag_plot(data['y'], lag=lag)
    plt.title(f'Lag Plot (Lag={lag})')
    plt.xlabel('t')
    plt.ylabel(f't+{lag}')
    st.pyplot(plt)

if 'df' in locals() and 'forecast_methods' in locals() and forecast_methods:
    st.subheader("Forecast Visualization")
    train_size = int(len(df) * 0.8)
    train, test = df[:train_size], df[train_size:]
    periods_to_forecast = len(test)

    predictions = {}
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(train.index, train['y'], label='Training Data')
    ax.plot(test.index, test['y'], label='Testing Data')

    if "Simple Moving Average" in forecast_methods:
        try:
            sma_window = st.slider("SMA Window", min_value=2, max_value=30, value=7)
            sma_predictions = forecast_sma(train.copy(), sma_window, periods_to_forecast)
            predictions['Simple Moving Average'] = sma_predictions
            ax.plot(sma_predictions.index, sma_predictions, label=f'SMA (Window={sma_window}) Forecast')
        except Exception as e:
            st.error(f"Error with Simple Moving Average: {e}")

    if "Exponential Smoothing" in forecast_methods:
        try:
            es_alpha = st.slider("Exponential Smoothing Alpha", min_value=0.01, max_value=0.99, value=0.2, step=0.01)
            es_predictions = forecast_exponential_smoothing(train.copy(), periods_to_forecast, alpha=es_alpha)
            forecast_index_es = pd.date_range(start=train.index[-1], periods=periods_to_forecast + 1, freq=train.index.freq)[1:]
            predictions['Exponential Smoothing'] = pd.Series(es_predictions, index=forecast_index_es)
            ax.plot(forecast_index_es, es_predictions, label=f'Exponential Smoothing (Alpha={es_alpha:.2f}) Forecast')
        except Exception as e:
            st.error(f"Error with Exponential Smoothing: {e}")

    if "Lag Plot" in forecast_methods:
        try:
            lag_value = st.slider("Lag Value for Plot", min_value=1, max_value=20, value=1)
            plot_lag(df, lag=lag_value)
        except Exception as e:
            st.error(f"Error with Lag Plot: {e}")

    ax.set_xlabel("Date")
    ax.set_ylabel("Value")
    ax.legend()
    st.pyplot(fig)

def calculate_metrics(y_true, y_pred):
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    mae = mean_absolute_error(y_true, y_pred)
    mape = np.mean(np.abs((y_true - y_pred) / y_true)) * 100
    mse = mean_squared_error(y_true, y_pred)
    return rmse, mae, mape, mse

if 'predictions' in locals() and predictions and not test.empty:
    st.subheader("Forecasting Accuracy")
    for method, preds in predictions.items():
        if method == 'Simple Moving Average':
            y_true = test['y']
            y_pred = preds[-len(test):].values
            if len(y_pred) != len(y_true):
                st.warning(f"Could not align SMA predictions for evaluation.")
                continue
        elif method == 'Exponential Smoothing':
            y_true = test['y']
            y_pred = preds.values
            if len(y_pred) < len(y_true):
                st.warning(f"Not enough predictions from {method} to evaluate.")
                continue
        else:
            continue

        rmse, mae, mape, mse = calculate_metrics(y_true, y_pred)
        st.write(f"**{method} Accuracy:**")
        st.write(f"  - RMSE: {rmse:.2f}")
        st.write(f"  - MAE: {mae:.2f}")
        st.write(f"  - MAPE: {mape:.2f}%")
        st.write(f"  - MSE: {mse:.2f}")
