"""
LSTM-based Workload Forecasting for Right-Sizing
Predicts future CPU/memory usage patterns using time series analysis
"""
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple
import pickle
from pathlib import Path

# TensorFlow imports
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
from sklearn.preprocessing import MinMaxScaler


class LSTMWorkloadForecaster:
    def __init__(self):
        self.model = None
        self.scaler = MinMaxScaler()
        self.lookback_window = 24  # Use 24 hours of history to predict next hour
        self.forecast_horizon = 168  # Predict 7 days ahead (168 hours)
        self.model_path = Path(__file__).parent.parent / "models" / "lstm_forecaster.h5"
        self.scaler_path = Path(__file__).parent.parent / "models" / "lstm_scaler.pkl"
        
        # Create models directory
        self.model_path.parent.mkdir(exist_ok=True)
        
        # Try to load existing model
        self._load_model()
    
    def _load_model(self):
        """Load trained model if exists"""
        try:
            if self.model_path.exists() and self.scaler_path.exists():
                self.model = keras.models.load_model(self.model_path)
                with open(self.scaler_path, 'rb') as f:
                    self.scaler = pickle.load(f)
                print("✅ Loaded existing LSTM forecasting model")
            else:
                print("ℹ️ No trained LSTM model found. Will train on first analysis.")
        except Exception as e:
            print(f"⚠️ Error loading model: {e}")
            self.model = None
    
    def _save_model(self):
        """Save trained model"""
        try:
            self.model.save(self.model_path)
            with open(self.scaler_path, 'wb') as f:
                pickle.dump(self.scaler, f)
            print("✅ Saved LSTM forecasting model")
        except Exception as e:
            print(f"⚠️ Error saving model: {e}")
    
    def _build_model(self, input_shape: Tuple[int, int]):
        """Build LSTM neural network architecture"""
        model = keras.Sequential([
            # First LSTM layer with return sequences
            layers.LSTM(64, return_sequences=True, input_shape=input_shape),
            layers.Dropout(0.2),
            
            # Second LSTM layer
            layers.LSTM(32, return_sequences=False),
            layers.Dropout(0.2),
            
            # Dense layers
            layers.Dense(16, activation='relu'),
            layers.Dense(1)  # Output: predicted value
        ])
        
        model.compile(
            optimizer='adam',
            loss='mse',
            metrics=['mae']
        )
        
        return model
    
    def _prepare_sequences(self, data: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Create sequences for LSTM training"""
        X, y = [], []
        
        for i in range(len(data) - self.lookback_window):
            X.append(data[i:i + self.lookback_window])
            y.append(data[i + self.lookback_window])
        
        return np.array(X), np.array(y)
    
    def train(self, metrics_data: pd.DataFrame, metric_name: str = 'cpu_utilization'):
        """
        Train LSTM model on historical metrics
        
        Args:
            metrics_data: DataFrame with timestamps and metric values
            metric_name: Column name for the metric to forecast
        """
        print(f"\n🧠 Training LSTM model for {metric_name} forecasting...")
        
        if len(metrics_data) < self.lookback_window + 10:
            print(f"❌ Not enough data to train (need at least {self.lookback_window + 10} points)")
            return False
        
        # Extract and normalize data
        values = metrics_data[metric_name].values.reshape(-1, 1)
        scaled_data = self.scaler.fit_transform(values)
        
        # Prepare sequences
        X, y = self._prepare_sequences(scaled_data)
        
        if len(X) < 10:
            print("❌ Not enough sequences for training")
            return False
        
        # Split into train/validation
        split_idx = int(len(X) * 0.8)
        X_train, X_val = X[:split_idx], X[split_idx:]
        y_train, y_val = y[:split_idx], y[split_idx:]
        
        # Build model
        self.model = self._build_model(input_shape=(self.lookback_window, 1))
        
        # Train
        history = self.model.fit(
            X_train, y_train,
            validation_data=(X_val, y_val),
            epochs=50,
            batch_size=32,
            verbose=0,
            callbacks=[
                keras.callbacks.EarlyStopping(
                    monitor='val_loss',
                    patience=5,
                    restore_best_weights=True
                )
            ]
        )
        
        # Save model
        self._save_model()
        
        print(f"✅ LSTM model trained!")
        print(f"   Final loss: {history.history['loss'][-1]:.4f}")
        print(f"   Final MAE: {history.history['mae'][-1]:.4f}")
        
        return True
    
    def forecast(self, recent_data: np.ndarray, hours_ahead: int = 168) -> Dict[str, Any]:
        """
        Forecast future values
        
        Args:
            recent_data: Last N hours of data (N >= lookback_window)
            hours_ahead: How many hours to forecast (default 7 days)
        
        Returns:
            {
                'predictions': List[float],
                'confidence_intervals': List[Tuple[float, float]],
                'trend': str,
                'seasonality_detected': bool
            }
        """
        if self.model is None:
            return {
                'predictions': [],
                'confidence_intervals': [],
                'trend': 'UNKNOWN',
                'seasonality_detected': False,
                'error': 'Model not trained'
            }
        
        print(f"\n🔮 Forecasting next {hours_ahead} hours...")
        
        # Ensure we have enough data
        if len(recent_data) < self.lookback_window:
            return {
                'predictions': [],
                'confidence_intervals': [],
                'trend': 'INSUFFICIENT_DATA',
                'seasonality_detected': False,
                'error': f'Need at least {self.lookback_window} data points'
            }
        
        # Normalize
        recent_scaled = self.scaler.transform(recent_data.reshape(-1, 1))
        
        # Forecast iteratively
        predictions = []
        current_sequence = recent_scaled[-self.lookback_window:].copy()
        
        for _ in range(min(hours_ahead, self.forecast_horizon)):
            # Reshape for prediction
            X = current_sequence.reshape(1, self.lookback_window, 1)
            
            # Predict next value
            pred = self.model.predict(X, verbose=0)[0, 0]
            predictions.append(pred)
            
            # Update sequence (sliding window)
            current_sequence = np.append(current_sequence[1:], [[pred]], axis=0)
        
        # Inverse transform predictions
        predictions_actual = self.scaler.inverse_transform(
            np.array(predictions).reshape(-1, 1)
        ).flatten()
        
        # Calculate confidence intervals (simple approach using std)
        std = np.std(predictions_actual)
        confidence_intervals = [
            (max(0, pred - 1.96 * std), min(100, pred + 1.96 * std))
            for pred in predictions_actual
        ]
        
        # Detect trend
        trend = self._detect_trend(predictions_actual)
        
        # Detect seasonality
        seasonality = self._detect_seasonality(recent_data.flatten())
        
        print(f"✅ Forecast complete!")
        print(f"   Trend: {trend}")
        print(f"   Seasonality: {'Detected' if seasonality else 'Not detected'}")
        
        return {
            'predictions': predictions_actual.tolist(),
            'confidence_intervals': confidence_intervals,
            'trend': trend,
            'seasonality_detected': seasonality,
            'avg_predicted': float(np.mean(predictions_actual)),
            'max_predicted': float(np.max(predictions_actual)),
            'min_predicted': float(np.min(predictions_actual))
        }
    
    def _detect_trend(self, predictions: np.ndarray) -> str:
        """Detect if workload is growing, shrinking, or stable"""
        if len(predictions) < 24:
            return 'INSUFFICIENT_DATA'
        
        # Compare first 24h vs last 24h
        first_quarter = predictions[:24]
        last_quarter = predictions[-24:]
        
        avg_first = np.mean(first_quarter)
        avg_last = np.mean(last_quarter)
        
        # Calculate percentage change
        if avg_first == 0:
            return 'STABLE'
        
        pct_change = ((avg_last - avg_first) / avg_first) * 100
        
        if pct_change > 10:
            return 'GROWING'
        elif pct_change < -10:
            return 'SHRINKING'
        else:
            return 'STABLE'
    
    def _detect_seasonality(self, data: np.ndarray) -> bool:
        """Simple seasonality detection using autocorrelation"""
        if len(data) < 48:  # Need at least 2 days
            return False
        
        # Check for daily pattern (24-hour cycle)
        try:
            # Simple autocorrelation at lag 24
            mean = np.mean(data)
            var = np.var(data)
            
            if var == 0:
                return False
            
            n = len(data)
            lag = 24
            
            if n <= lag:
                return False
            
            autocorr = np.corrcoef(data[:-lag], data[lag:])[0, 1]
            
            # If correlation > 0.5, likely has daily seasonality
            return autocorr > 0.5
        except:
            return False
    
    def analyze_workload_pattern(self, data: np.ndarray) -> Dict[str, Any]:
        """Analyze if workload is bursty or steady"""
        if len(data) < 24:
            return {
                'pattern': 'INSUFFICIENT_DATA',
                'coefficient_of_variation': 0,
                'peak_to_avg_ratio': 0
            }
        
        mean = np.mean(data)
        std = np.std(data)
        peak = np.max(data)
        
        # Coefficient of variation
        cv = (std / mean) if mean > 0 else 0
        
        # Peak to average ratio
        peak_ratio = (peak / mean) if mean > 0 else 0
        
        # Classify pattern
        if cv > 0.5 or peak_ratio > 2:
            pattern = 'BURSTY'
        else:
            pattern = 'STEADY'
        
        return {
            'pattern': pattern,
            'coefficient_of_variation': float(cv),
            'peak_to_avg_ratio': float(peak_ratio),
            'recommendation': 'Consider auto-scaling' if pattern == 'BURSTY' else 'Reserved Instance suitable'
        }


if __name__ == "__main__":
    # Test the forecaster
    print("🧪 Testing LSTM Workload Forecaster...")
    
    forecaster = LSTMWorkloadForecaster()
    
    # Generate synthetic workload data (30 days, hourly)
    hours = 30 * 24
    timestamps = pd.date_range(end=datetime.now(), periods=hours, freq='H')
    
    # Simulate daily pattern + trend + noise
    t = np.arange(hours)
    daily_pattern = 30 * np.sin(2 * np.pi * t / 24)  # Daily cycle
    trend = 0.01 * t  # Slight upward trend
    noise = np.random.normal(0, 5, hours)
    cpu_usage = 50 + daily_pattern + trend + noise
    cpu_usage = np.clip(cpu_usage, 0, 100)
    
    df = pd.DataFrame({
        'timestamp': timestamps,
        'cpu_utilization': cpu_usage
    })
    
    print(f"\n📊 Generated {len(df)} hours of synthetic data")
    
    # Train model
    success = forecaster.train(df, 'cpu_utilization')
    
    if success:
        # Forecast
        recent = cpu_usage[-48:]  # Last 48 hours
        forecast_result = forecaster.forecast(recent, hours_ahead=168)
        
        print(f"\n🔮 Forecast Results:")
        print(f"   Trend: {forecast_result['trend']}")
        print(f"   Seasonality: {forecast_result['seasonality_detected']}")
        print(f"   Avg predicted: {forecast_result['avg_predicted']:.2f}%")
        print(f"   Max predicted: {forecast_result['max_predicted']:.2f}%")
        
        # Analyze pattern
        pattern = forecaster.analyze_workload_pattern(recent)
        print(f"\n📈 Workload Pattern:")
        print(f"   Type: {pattern['pattern']}")
        print(f"   Coefficient of Variation: {pattern['coefficient_of_variation']:.2f}")
        print(f"   Recommendation: {pattern['recommendation']}")
