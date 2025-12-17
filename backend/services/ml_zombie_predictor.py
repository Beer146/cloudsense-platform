"""
ML-Powered Zombie Resource Predictor
Predicts which resources are likely to become zombies
"""
import boto3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Any
import pickle
import os
from pathlib import Path


class ZombiePredictor:
    def __init__(self):
        self.model = None
        self.model_path = Path(__file__).parent.parent / 'models' / 'zombie_predictor.pkl'
        self.feature_columns = [
            'days_since_creation',
            'has_name_tag',
            'has_owner_tag',
            'has_environment_tag',
            'is_stopped',
            'instance_size_score',  # Larger instances = higher score
            'region_zombie_rate',  # Historical zombie rate in region
        ]
        
        # Try to load existing model
        self._load_model()
    
    def _load_model(self):
        """Load trained model if it exists"""
        if self.model_path.exists():
            try:
                with open(self.model_path, 'rb') as f:
                    self.model = pickle.load(f)
                print(f"✅ Loaded model from {self.model_path}")
            except Exception as e:
                print(f"⚠️ Could not load model: {e}")
                self.model = None
        else:
            print("ℹ️ No trained model found. Will use heuristic scoring.")
    
    def extract_features(self, resource: Dict[str, Any], region: str) -> Dict[str, float]:
        """Extract features from a resource for prediction"""
        
        # Calculate days since creation
        creation_time = resource.get('launch_time') or resource.get('create_time')
        if isinstance(creation_time, str):
            creation_time = datetime.fromisoformat(creation_time.replace('Z', '+00:00'))
        
        days_since_creation = (datetime.now(creation_time.tzinfo) - creation_time).days if creation_time else 0
        
        # Extract tags
        tags = resource.get('tags', {})
        has_name_tag = 1 if tags.get('Name') else 0
        has_owner_tag = 1 if tags.get('Owner') else 0
        has_environment_tag = 1 if tags.get('Environment') else 0
        
        # Check if stopped
        is_stopped = 1 if resource.get('state', {}).get('Name') == 'stopped' else 0
        
        # Instance size score (larger = higher risk of waste)
        instance_type = resource.get('instance_type', '')
        instance_size_score = self._get_instance_size_score(instance_type)
        
        # Region zombie rate (would be calculated from historical data)
        region_zombie_rate = 0.15  # Placeholder: 15% of resources become zombies
        
        features = {
            'days_since_creation': days_since_creation,
            'has_name_tag': has_name_tag,
            'has_owner_tag': has_owner_tag,
            'has_environment_tag': has_environment_tag,
            'is_stopped': is_stopped,
            'instance_size_score': instance_size_score,
            'region_zombie_rate': region_zombie_rate,
        }
        
        return features
    
    def _get_instance_size_score(self, instance_type: str) -> float:
        """Score instance type by size (larger = higher score)"""
        if not instance_type:
            return 0.0
        
        # Extract size from instance type (e.g., t2.micro, m5.2xlarge)
        size_mapping = {
            'nano': 0.1, 'micro': 0.2, 'small': 0.3, 'medium': 0.4,
            'large': 0.5, 'xlarge': 0.7, '2xlarge': 0.8, '4xlarge': 0.9,
            '8xlarge': 1.0, '12xlarge': 1.0, '16xlarge': 1.0, '24xlarge': 1.0
        }
        
        for size, score in size_mapping.items():
            if size in instance_type.lower():
                return score
        
        return 0.5  # Default
    
    def predict_zombie_probability(self, resource: Dict[str, Any], region: str) -> Dict[str, Any]:
        """Predict probability that a resource will become a zombie"""
        
        # Extract features
        features = self.extract_features(resource, region)
        
        if self.model is not None:
            # Use trained ML model
            feature_vector = [features[col] for col in self.feature_columns]
            probability = self.model.predict_proba([feature_vector])[0][1]  # Prob of zombie class
        else:
            # Use heuristic scoring (rule-based fallback)
            probability = self._heuristic_score(features)
        
        # Classify risk level
        if probability >= 0.7:
            risk_level = 'HIGH'
            risk_color = '#ff6b6b'
        elif probability >= 0.4:
            risk_level = 'MEDIUM'
            risk_color = '#ffa500'
        elif probability >= 0.2:
            risk_level = 'LOW'
            risk_color = '#ffd93d'
        else:
            risk_level = 'VERY_LOW'
            risk_color = '#42d392'
        
        # Generate explanation
        explanation = self._generate_explanation(features, probability)
        
        return {
            'zombie_probability': float(probability),
            'risk_level': risk_level,
            'risk_color': risk_color,
            'explanation': explanation,
            'features': features
        }
    
    def _heuristic_score(self, features: Dict[str, float]) -> float:
        """Calculate zombie probability using heuristics (no ML model)"""
        score = 0.0
        
        # Already stopped = very high risk
        if features['is_stopped'] == 1:
            score += 0.6
        
        # Old resources = higher risk
        days = features['days_since_creation']
        if days > 90:
            score += 0.2
        elif days > 30:
            score += 0.1
        
        # Missing tags = higher risk (unmanaged)
        if features['has_name_tag'] == 0:
            score += 0.1
        if features['has_owner_tag'] == 0:
            score += 0.15
        if features['has_environment_tag'] == 0:
            score += 0.05
        
        # Large instances = higher waste risk
        score += features['instance_size_score'] * 0.2
        
        # Regional zombie rate
        score += features['region_zombie_rate'] * 0.3
        
        return min(score, 1.0)  # Cap at 100%
    
    def _generate_explanation(self, features: Dict[str, float], probability: float) -> str:
        """Generate human-readable explanation for prediction"""
        reasons = []
        
        if features['is_stopped'] == 1:
            reasons.append("resource is currently stopped")
        
        if features['days_since_creation'] > 90:
            reasons.append(f"resource is {int(features['days_since_creation'])} days old")
        
        if features['has_owner_tag'] == 0:
            reasons.append("missing Owner tag (unmanaged)")
        
        if features['has_name_tag'] == 0:
            reasons.append("missing Name tag")
        
        if features['instance_size_score'] > 0.7:
            reasons.append("large instance size (high waste potential)")
        
        if probability >= 0.7:
            explanation = f"🚨 HIGH RISK: This resource has a {probability*100:.0f}% chance of becoming a zombie because {', '.join(reasons)}."
        elif probability >= 0.4:
            explanation = f"⚠️ MEDIUM RISK: {probability*100:.0f}% chance of becoming a zombie. {', '.join(reasons) if reasons else 'Monitor this resource closely.'}"
        else:
            explanation = f"✅ LOW RISK: Only {probability*100:.0f}% chance of becoming a zombie. Resource appears well-managed."
        
        return explanation
    
    def train_model(self, training_data: pd.DataFrame):
        """Train the zombie prediction model"""
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.model_selection import train_test_split
        from sklearn.metrics import classification_report, roc_auc_score
        
        # Prepare features and labels
        X = training_data[self.feature_columns]
        y = training_data['is_zombie']  # 1 = became zombie, 0 = still active
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        # Train Random Forest
        print("🔄 Training Random Forest model...")
        model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42,
            class_weight='balanced'  # Handle imbalanced data
        )
        
        model.fit(X_train, y_train)
        
        # Evaluate
        y_pred = model.predict(X_test)
        y_proba = model.predict_proba(X_test)[:, 1]
        
        print("\n📊 Model Performance:")
        print(classification_report(y_test, y_pred, target_names=['Active', 'Zombie']))
        print(f"ROC AUC Score: {roc_auc_score(y_test, y_proba):.3f}")
        
        # Feature importance
        feature_importance = pd.DataFrame({
            'feature': self.feature_columns,
            'importance': model.feature_importances_
        }).sort_values('importance', ascending=False)
        
        print("\n🎯 Feature Importance:")
        print(feature_importance)
        
        # Save model
        self.model = model
        os.makedirs(self.model_path.parent, exist_ok=True)
        with open(self.model_path, 'wb') as f:
            pickle.dump(model, f)
        
        print(f"\n✅ Model saved to {self.model_path}")
        
        return {
            'accuracy': (y_pred == y_test).mean(),
            'roc_auc': roc_auc_score(y_test, y_proba),
            'feature_importance': feature_importance.to_dict('records')
        }
