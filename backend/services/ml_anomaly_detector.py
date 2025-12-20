"""
ML-Powered Anomaly Detection for Security
Uses Isolation Forest to detect unusual resource configurations
"""
import boto3
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import pickle
import os
from datetime import datetime
from pathlib import Path


class AnomalyDetector:
    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        self.feature_names = []
        self.model_path = Path(__file__).parent.parent / "models" / "anomaly_detector.pkl"
        self.scaler_path = Path(__file__).parent.parent / "models" / "anomaly_scaler.pkl"
        
        # Create models directory if it doesn't exist
        self.model_path.parent.mkdir(exist_ok=True)
        
        # Try to load existing model
        self._load_model()
    
    def _load_model(self):
        """Load trained model and scaler if they exist"""
        try:
            if self.model_path.exists() and self.scaler_path.exists():
                with open(self.model_path, 'rb') as f:
                    self.model = pickle.load(f)
                with open(self.scaler_path, 'rb') as f:
                    self.scaler = pickle.load(f)
                print("✅ Loaded existing anomaly detection model")
            else:
                print("ℹ️ No trained anomaly model found. Will train on first scan.")
        except Exception as e:
            print(f"⚠️ Error loading model: {e}")
            self.model = None
    
    def _save_model(self):
        """Save trained model and scaler"""
        try:
            with open(self.model_path, 'wb') as f:
                pickle.dump(self.model, f)
            with open(self.scaler_path, 'wb') as f:
                pickle.dump(self.scaler, f)
            print("✅ Saved anomaly detection model")
        except Exception as e:
            print(f"⚠️ Error saving model: {e}")
    
    def extract_ec2_features(self, instance):
        """
        Extract feature vector from EC2 instance
        
        Features:
        1. Number of security groups
        2. Number of open ports
        3. Has public IP (0/1)
        4. EBS encrypted (0/1)
        5. Has Name tag (0/1)
        6. Has Owner tag (0/1)
        7. Has Environment tag (0/1)
        8. Instance size score (0-1)
        9. Number of IAM roles
        10. Days since creation
        """
        tags = {tag['Key']: tag['Value'] for tag in instance.get('Tags', [])}
        
        # Security groups and ports
        security_groups = instance.get('SecurityGroups', [])
        num_sg = len(security_groups)
        
        # Count open ports from security group rules
        open_ports = self._count_open_ports(security_groups, instance.get('Placement', {}).get('AvailabilityZone', '')[:-1])
        
        # Public IP
        has_public_ip = 1 if instance.get('PublicIpAddress') else 0
        
        # EBS encryption
        ebs_encrypted = self._check_ebs_encryption(instance.get('BlockDeviceMappings', []))
        
        # Tags
        has_name = 1 if 'Name' in tags else 0
        has_owner = 1 if 'Owner' in tags else 0
        has_environment = 1 if 'Environment' in tags else 0
        
        # Instance size score
        instance_type = instance.get('InstanceType', 't2.micro')
        size_score = self._get_instance_size_score(instance_type)
        
        # IAM roles
        iam_profile = instance.get('IamInstanceProfile', {})
        num_iam_roles = 1 if iam_profile else 0
        
        # Age
        launch_time = instance.get('LaunchTime')
        if launch_time:
            days_old = (datetime.now(launch_time.tzinfo) - launch_time).days
        else:
            days_old = 0
        
        return np.array([
            num_sg,
            open_ports,
            has_public_ip,
            ebs_encrypted,
            has_name,
            has_owner,
            has_environment,
            size_score,
            num_iam_roles,
            days_old
        ])
    
    def _count_open_ports(self, security_groups, region):
        """Count number of open ports from security group rules"""
        if not security_groups:
            return 0
        
        try:
            ec2 = boto3.client('ec2', region_name=region)
            sg_ids = [sg['GroupId'] for sg in security_groups]
            
            response = ec2.describe_security_groups(GroupIds=sg_ids)
            
            open_ports = set()
            for sg in response['SecurityGroups']:
                for rule in sg.get('IpPermissions', []):
                    from_port = rule.get('FromPort', 0)
                    to_port = rule.get('ToPort', 0)
                    
                    if from_port == to_port:
                        open_ports.add(from_port)
                    else:
                        # Port range
                        open_ports.update(range(from_port, to_port + 1))
            
            return len(open_ports)
        except Exception as e:
            print(f"Error counting ports: {e}")
            return 0
    
    def _check_ebs_encryption(self, block_devices):
        """Check if all EBS volumes are encrypted"""
        if not block_devices:
            return 0
        
        for device in block_devices:
            ebs = device.get('Ebs', {})
            if not ebs.get('Encrypted', False):
                return 0
        
        return 1
    
    def _get_instance_size_score(self, instance_type):
        """
        Convert instance type to size score (0-1)
        Larger instances = higher score
        """
        size_map = {
            'nano': 0.1, 'micro': 0.2, 'small': 0.3, 'medium': 0.4,
            'large': 0.5, 'xlarge': 0.6, '2xlarge': 0.7, '4xlarge': 0.8,
            '8xlarge': 0.9, '12xlarge': 0.95, '16xlarge': 1.0
        }
        
        for size, score in size_map.items():
            if size in instance_type.lower():
                return score
        
        return 0.5  # Default medium
    
    def train_baseline(self, resources, contamination=0.1):
        """
        Train Isolation Forest on current infrastructure
        
        Args:
            resources: List of AWS resources
            contamination: Expected proportion of anomalies (0.1 = 10%)
        
        Returns:
            Number of resources used for training
        """
        print(f"🧠 Training anomaly detection baseline on {len(resources)} resources...")
        
        # Extract features from all resources
        feature_vectors = []
        for resource in resources:
            try:
                features = self.extract_ec2_features(resource)
                feature_vectors.append(features)
            except Exception as e:
                print(f"⚠️ Error extracting features: {e}")
        
        if len(feature_vectors) < 2:
            print("❌ Not enough resources to train model (need at least 2)")
            return 0
        
        X = np.array(feature_vectors)
        
        # Normalize features
        X_scaled = self.scaler.fit_transform(X)
        
        # Train Isolation Forest
        self.model = IsolationForest(
            contamination=contamination,
            random_state=42,
            n_estimators=100,
            max_samples='auto',
            max_features=1.0
        )
        
        self.model.fit(X_scaled)
        
        # Save model
        self._save_model()
        
        print(f"✅ Trained anomaly detector on {len(feature_vectors)} resources")
        return len(feature_vectors)
    
    def predict_anomaly(self, resource, region):
        """
        Predict if resource is an anomaly
        
        Returns:
            {
                'is_anomaly': bool,
                'anomaly_score': float (-1 to 1, lower = more anomalous),
                'confidence': float (0-1),
                'risk_level': str,
                'explanation': str,
                'features': dict
            }
        """
        if self.model is None:
            return {
                'is_anomaly': False,
                'anomaly_score': 0.0,
                'confidence': 0.0,
                'risk_level': 'UNKNOWN',
                'explanation': 'No baseline model trained yet',
                'features': {}
            }
        
        # Extract features
        features = self.extract_ec2_features(resource)
        X = features.reshape(1, -1)
        X_scaled = self.scaler.transform(X)
        
        # Predict
        prediction = self.model.predict(X_scaled)[0]  # -1 = anomaly, 1 = normal
        score = self.model.score_samples(X_scaled)[0]  # Lower = more anomalous
        
        is_anomaly = (prediction == -1)
        
        # Convert score to 0-1 confidence
        # Scores typically range from -0.5 to 0.5
        confidence = 1 - ((score + 0.5) / 1.0)  # Normalize to 0-1
        confidence = max(0, min(1, confidence))
        
        # Risk level
        if confidence >= 0.8:
            risk_level = 'CRITICAL'
            color = '#D13212'
        elif confidence >= 0.6:
            risk_level = 'HIGH'
            color = '#FF9900'
        elif confidence >= 0.4:
            risk_level = 'MEDIUM'
            color = '#FFD700'
        else:
            risk_level = 'LOW'
            color = '#146EB4'
        
        # Generate explanation
        explanation = self._generate_explanation(resource, features, confidence)
        
        # Feature breakdown
        feature_names = [
            'num_security_groups', 'open_ports', 'has_public_ip', 'ebs_encrypted',
            'has_name_tag', 'has_owner_tag', 'has_environment_tag',
            'instance_size_score', 'num_iam_roles', 'days_old'
        ]
        
        feature_dict = {name: float(val) for name, val in zip(feature_names, features)}
        
        return {
            'is_anomaly': is_anomaly,
            'anomaly_score': float(score),
            'confidence': float(confidence),
            'risk_level': risk_level,
            'risk_color': color,
            'explanation': explanation,
            'features': feature_dict
        }
    
    def _generate_explanation(self, resource, features, confidence):
        """Generate human-readable explanation for anomaly"""
        reasons = []
        
        # Unpack features
        (num_sg, open_ports, has_public_ip, ebs_encrypted,
         has_name, has_owner, has_env, size_score, num_iam, days_old) = features
        
        if confidence >= 0.6:
            reasons.append(f"⚠️ Configuration differs significantly from baseline")
        
        if open_ports > 10:
            reasons.append(f"Unusual number of open ports ({int(open_ports)})")
        
        if has_public_ip and open_ports > 5:
            reasons.append("Public IP with many open ports")
        
        if not ebs_encrypted:
            reasons.append("Unencrypted EBS volumes")
        
        if not has_name or not has_owner:
            reasons.append("Missing critical tags")
        
        if num_sg > 5:
            reasons.append(f"Unusual number of security groups ({int(num_sg)})")
        
        if size_score > 0.7:
            reasons.append("Large instance size")
        
        if days_old < 1:
            reasons.append("Newly created resource")
        
        if not reasons:
            reasons.append("Pattern deviates from established baseline")
        
        confidence_pct = int(confidence * 100)
        explanation = f"{confidence_pct}% confidence anomaly: {', '.join(reasons)}"
        
        return explanation


if __name__ == "__main__":
    # Test the feature extraction
    detector = AnomalyDetector()
    print("✅ Anomaly Detector initialized")
