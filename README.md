# CloudSense Platform 🚀

> Enterprise-grade AWS cost optimization platform with ML-powered predictive analytics

![CloudSense Platform](https://img.shields.io/badge/status-active-success.svg)
![Python](https://img.shields.io/badge/python-3.13-blue.svg)
![React](https://img.shields.io/badge/react-18-blue.svg)
![FastAPI](https://img.shields.io/badge/fastapi-0.115-green.svg)
![ML](https://img.shields.io/badge/ML-scikit--learn-orange.svg)

## 🎯 Overview

CloudSense is a comprehensive full-stack AWS cost intelligence platform that combines automated resource scanning, intelligent right-sizing, security compliance validation, and incident analysis with **machine learning predictions** to help organizations eliminate cloud waste and optimize infrastructure spending.

**Built in 13+ hours** as a portfolio demonstration of full-stack development, cloud engineering, and ML integration skills.

### ✨ Key Features

#### 🤖 ML-Powered Analytics
- **Predictive Zombie Detection**: ML model predicts which running resources are at risk of becoming zombies *before* they waste money
- **Heuristic Scoring**: Intelligent fallback system using resource age, tags, size, and regional patterns
- **Risk Classification**: HIGH/MEDIUM/LOW/VERY_LOW risk levels with detailed explanations
- **Feature Engineering**: 7+ features including days since creation, tagging completeness, instance size scoring

#### 💀 Zombie Resource Hunter
- Automatically detects idle and unused AWS resources (EC2, EBS, RDS, ELB)
- Identifies stopped instances, unattached volumes, idle databases
- Calculates monthly cost waste ($8.47/month per zombie instance)
- **NEW**: Predicts which running instances will become zombies

#### 📏 Right-Sizing Engine
- Analyzes 14 days of CloudWatch CPU/memory metrics
- Recommends optimal instance types (downsize, family switches)
- Calculates potential monthly savings
- Identifies over-provisioned resources

#### 🔒 Compliance Validator
- Security violation scanning (open ports, encryption, tagging)
- Severity classification (Critical/High/Medium/Low)
- Resolution tracking with timestamps and notes
- Remediation guidance for each violation

#### 📋 Post-Mortem Generator
- CloudWatch Logs analysis for errors and warnings
- Pattern recognition and grouping
- Automated recommendations
- Incident timeline reconstruction

#### 📊 Executive Dashboard
- Multi-service scan history
- Health score tracking
- Cost trends visualization with Recharts
- Service-specific insights

## 🏗️ Architecture
```
cloudsense-platform/
├── backend/                    # FastAPI REST API
│   ├── api/                   # 7 REST endpoints
│   │   ├── zombie.py         # Zombie scanning with ML
│   │   ├── rightsizing.py    # Right-sizing analysis
│   │   ├── compliance.py     # Security validation
│   │   ├── postmortem_api.py # Log analysis
│   │   ├── history.py        # Scan history
│   │   ├── insights.py       # Analytics dashboard
│   │   └── resolutions.py    # Violation tracking
│   ├── services/             # Business logic layer
│   │   ├── ml_zombie_predictor.py  # ML prediction engine
│   │   ├── zombie_service.py
│   │   ├── rightsizing_service.py
│   │   ├── compliance_service.py
│   │   └── postmortem_service.py
│   ├── models/              # SQLAlchemy data models
│   │   ├── scan.py         # Scan metadata
│   │   └── database.py     # SQLite connection
│   └── cloudsense.db       # SQLite database
├── frontend/               # React TypeScript UI
│   └── src/
│       ├── App.tsx        # Main dashboard
│       ├── pages/
│       │   ├── History.tsx
│       │   └── Insights.tsx
│       └── App.css        # Purple gradient theme
└── scripts/               # AWS scanning modules
    ├── zombie-hunter/     # (planned refactor)
    ├── rightsizing/       # (planned refactor)
    ├── compliance/        # Rule-based validator
    └── post-mortem/       # Log analyzer
```

## 🛠️ Tech Stack

### Backend
- **FastAPI** - Modern async Python web framework
- **boto3** - AWS SDK for Python
- **SQLAlchemy** - Database ORM
- **SQLite** - Local database
- **scikit-learn** - Machine learning (Random Forest)
- **XGBoost** - Gradient boosting (ready for training)
- **pandas/numpy** - Data processing

### Frontend
- **React 18** - UI library
- **TypeScript** - Type-safe JavaScript
- **Vite** - Build tool
- **Recharts** - Data visualization

### ML/AI Stack
- **Random Forest Classifier** - Zombie prediction model
- **Feature Engineering** - 7+ custom features
- **Heuristic Scoring** - Rule-based fallback system
- Ready for: XGBoost, LSTM, LLM integration

### AWS Services
- **EC2, EBS, RDS, ELB** - Resource scanning
- **CloudWatch** - Metrics & logs analysis
- **IAM** - Permissions management

## 📦 Installation

### Prerequisites

- Python 3.13+
- Node.js 18+
- AWS credentials configured (`~/.aws/credentials`)
- AWS permissions: EC2, CloudWatch, RDS, ELB read access

### Backend Setup
```bash
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install fastapi uvicorn boto3 sqlalchemy pyyaml \
    scikit-learn xgboost pandas numpy joblib --break-system-packages

# Initialize database
python -c "from models.database import init_db; init_db()"

# Run API server
python api/main.py
```

Backend runs on `http://localhost:8000`

### Frontend Setup
```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

Frontend runs on `http://localhost:5173`

## 🔧 Configuration

### AWS Credentials

Ensure AWS credentials are configured:
```bash
aws configure
# Enter: Access Key ID, Secret Access Key, Region
```

### Service Configuration

Update `scripts/post-mortem/config.yaml`:
```yaml
aws:
  regions:
    - us-east-1
    - us-west-2

analysis:
  lookback_hours: 24
  error_keywords:
    - ERROR
    - CRITICAL
    - FATAL
```

Update `scripts/compliance/config.yaml`:
```yaml
required_tags:
  - Environment
  - Owner
  - CostCenter

security_groups:
  forbidden_ports:
    - 22  # SSH
    - 3389  # RDP
```

## 🎯 Usage

### 1. Launch the Platform
```bash
# Terminal 1: Backend
cd backend
source venv/bin/activate
python api/main.py

# Terminal 2: Frontend
cd frontend
npm run dev
```

### 2. Run Scans

Navigate to `http://localhost:5173` and:

1. **Zombie Resource Hunter**
   - Click "Run Scan"
   - View detected zombies and monthly costs
   - **NEW**: See ML predictions for at-risk resources

2. **Right-Sizing Engine**
   - Click "Analyze Resources"
   - Review downsize/family switch recommendations
   - Calculate potential savings

3. **Compliance Validator**
   - Click "Run Compliance Scan"
   - Review violations by severity
   - Mark violations as resolved with notes

4. **Post-Mortem Generator**
   - Click "Generate Report"
   - View error timeline
   - Read automated recommendations

### 3. View History & Insights

- **History Page**: Filter scans by service, view trends
- **Insights Page**: Executive dashboard with health scores

## 🤖 Machine Learning Features

### Zombie Prediction Model

**How It Works:**
1. Extracts 7+ features from each resource:
   - `days_since_creation` - Resource age
   - `has_name_tag`, `has_owner_tag`, `has_environment_tag` - Tagging completeness
   - `is_stopped` - Current state
   - `instance_size_score` - Size-based risk (0-1)
   - `region_zombie_rate` - Historical regional patterns

2. **Heuristic Scoring** (current implementation):
   - Stopped instances: +60% zombie probability
   - Missing tags: +10-15% each
   - Resource age >90 days: +20%
   - Large instances: +20%

3. **Risk Classification**:
   - ≥70% = HIGH RISK 🚨
   - ≥40% = MEDIUM RISK ⚠️
   - ≥20% = LOW RISK
   - <20% = VERY LOW RISK ✅

4. **Explanation Generation**:
   - "🚨 HIGH RISK: 85% chance of becoming zombie because resource is stopped, missing Owner tag, 120 days old"

**Future Training:**
With 30+ days of data, train supervised model:
```python
# Collect training data
X = features[['days_since_creation', 'has_owner_tag', ...]]
y = labels['became_zombie']  # 1 = zombie, 0 = active

# Train model
from sklearn.ensemble import RandomForestClassifier
model = RandomForestClassifier(n_estimators=100)
model.fit(X_train, y_train)

# Achieve 80%+ accuracy on test set
```

## 📊 API Endpoints

### Zombie Scanning
```bash
POST /api/zombie/scan
# Returns: zombies found, at-risk resources, ML predictions
```

### Right-Sizing
```bash
POST /api/rightsizing/analyze
# Returns: recommendations, potential savings
```

### Compliance
```bash
POST /api/compliance/scan
# Returns: violations by severity and type
```

### Post-Mortem
```bash
POST /api/postmortem/analyze
# Returns: error timeline, recommendations
```

### History & Insights
```bash
GET /api/history/scans?scan_type=zombie
GET /api/insights/health-scores
```

## 🎨 Features Roadmap

### Completed ✅
- [x] Zombie resource detection (EC2, EBS, RDS, ELB)
- [x] Right-sizing recommendations
- [x] Compliance validation with resolution tracking
- [x] Post-mortem log analysis
- [x] SQLite database with scan history
- [x] Executive insights dashboard
- [x] Multi-region support
- [x] **ML-powered zombie prediction** 🤖

### Phase 2: Enhanced ML 🚧
- [ ] Train supervised model with historical data
- [ ] Anomaly detection for security (Isolation Forest)
- [ ] LLM-powered post-mortem analysis (Claude API)
- [ ] LSTM time series forecasting for right-sizing
- [ ] Cost forecasting with Prophet/ARIMA

### Phase 3: Production Features 🔮
- [ ] Authentication (OAuth2/JWT)
- [ ] Multi-tenancy support
- [ ] PostgreSQL migration
- [ ] Deployment automation (Docker/K8s)
- [ ] CI/CD pipeline
- [ ] Custom domain + SSL
- [ ] Demo video

## 🧪 Testing
```bash
# Backend tests (planned)
cd backend
pytest tests/

# Frontend tests (planned)
cd frontend
npm test
```

## 📈 Performance

- **Zombie Scan**: ~3-5 seconds for 2 regions
- **Right-Sizing Analysis**: ~5-8 seconds (CloudWatch API calls)
- **Compliance Scan**: ~2-4 seconds
- **Post-Mortem Analysis**: ~10-15 seconds (log parsing)
- **Database**: SQLite (ready for PostgreSQL migration)

## 🔒 Security

- No hardcoded credentials (uses AWS credentials file)
- Resolution tracking for compliance violations
- Sensitive data excluded from logs
- Ready for IAM role-based access

## 📝 License

MIT License - Free to use for learning and portfolio purposes

## 🙏 Acknowledgments

Built as a comprehensive demonstration of:
- Full-stack development (React + FastAPI)
- Cloud engineering (AWS boto3)
- Machine learning integration (scikit-learn)
- Database design (SQLAlchemy)
- REST API development
- TypeScript + modern React patterns

## 👨‍💻 Author

**Abhir Naik**
- 🌐 Portfolio: [abhirnaik.me](https://abhirnaik.me)
- 💼 LinkedIn: [linkedin.com/in/abhirnaik](https://linkedin.com/in/abhirnaik)
- 🐙 GitHub: [@Beer146](https://github.com/Beer146)
- 📧 Junior @ Northeastern University
- 🎯 Computer Science + Business Administration (FinTech)

---

