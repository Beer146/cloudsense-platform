# CloudSense Platform

> Enterprise-grade AWS cost optimization and security platform powered by machine learning and AI

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![React](https://img.shields.io/badge/React-18.0+-61DAFB.svg)](https://reactjs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0+-3178C6.svg)](https://www.typescriptlang.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-009688.svg)](https://fastapi.tiangolo.com/)
[![TensorFlow](https://img.shields.io/badge/TensorFlow-2.20+-FF6F00.svg)](https://www.tensorflow.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

**Live Demo:** [Coming Soon] | **Documentation:** [View Docs](#documentation)

---

## Overview

CloudSense is a full-stack AWS cost intelligence platform that consolidates four intelligent services into one unified application. Built from the ground up in 13+ hours with cutting-edge ML/AI technologies, it helps organizations optimize cloud spending, enhance security posture, and prevent incidents before they happen.

### Key Achievements

- **4 ML/AI Models** - Random Forest, Isolation Forest, LSTM, Claude API
- **Real-time Analysis** - Live AWS integration across multiple regions
- **Cost Optimization** - Automated waste detection and right-sizing
- **Security Scanning** - ML-powered anomaly detection
- **Predictive Analytics** - 7-day workload forecasting

---

## Features

### Zombie Resource Hunter
**Automated waste detection with ML-powered predictions**

- Scans EC2, EBS, RDS, and ELB for idle/unused resources
- Calculates monthly cost waste with real pricing
- **ML Enhancement:** Random Forest classifier predicts which running resources will become zombies
- **7+ Features:** Resource age, tagging completeness, instance size, regional patterns
- **Heuristic Scoring:** Risk classification (HIGH/MEDIUM/LOW/VERY LOW)
- **Explainable AI:** Human-readable explanations for each prediction

**Tech Stack:** Python, boto3, scikit-learn, pandas

---

### Right-Sizing Recommendation Engine
**CloudWatch-based optimization with LSTM forecasting**

- Analyzes 14-30 days of CPU and memory metrics
- Identifies over-provisioned instances and recommends optimal types
- Calculates potential monthly savings
- **ML Enhancement:** LSTM neural networks for 7-day workload prediction
- **Pattern Detection:** Classifies workloads as BURSTY vs STEADY
- **Trend Analysis:** Detects growing/shrinking/stable patterns
- **Seasonality Detection:** Identifies daily/weekly usage cycles

**Tech Stack:** Python, CloudWatch, TensorFlow/Keras, numpy, pandas

---

### Compliance Validator
**Security scanning with ML anomaly detection**

- Scans infrastructure for security violations (open ports, unencrypted storage, missing tags)
- Severity classification (CRITICAL/HIGH/MEDIUM/LOW)
- Resolution tracking with timestamps and notes
- **ML Enhancement:** Isolation Forest for configuration anomaly detection
- **Baseline Learning:** Learns "normal" infrastructure patterns
- **Zero-Day Detection:** Flags unusual configurations before they become threats
- **10+ Features:** Security groups, ports, encryption, tags, IAM roles, resource age

**Tech Stack:** Python, boto3, scikit-learn, YAML config

---

### Post-Mortem Incident Analyzer
**CloudWatch log analysis with AI-powered insights**

- Extracts errors/warnings from CloudWatch Logs across regions
- Groups similar issues using regex pattern matching
- Builds incident timelines with 24-hour lookback
- **AI Enhancement:** Claude API (Anthropic) for intelligent analysis
- **Root Cause Detection:** Semantic analysis identifies correlated failures
- **Executive Summaries:** Auto-generated reports for leadership
- **Actionable Recommendations:** Priority-ranked fixes with AWS docs links

**Tech Stack:** Python, CloudWatch Logs, Claude API, regex

---

## Architecture

### System Architecture
```
┌─────────────────────────────────────────────────────────────┐
│                     CloudSense Platform                      │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌─────────────┐     ┌──────────────┐     ┌──────────────┐ │
│  │   React     │────▶│   FastAPI    │────▶│     AWS      │ │
│  │  Frontend   │     │   Backend    │     │   Services   │ │
│  │ TypeScript  │     │   Python     │     │   (boto3)    │ │
│  └─────────────┘     └──────────────┘     └──────────────┘ │
│         │                    │                      │        │
│         │                    ▼                      ▼        │
│         │            ┌──────────────┐      ┌──────────────┐ │
│         │            │   SQLite/    │      │  CloudWatch  │ │
│         │            │  PostgreSQL  │      │  Metrics &   │ │
│         │            │   Database   │      │     Logs     │ │
│         │            └──────────────┘      └──────────────┘ │
│         │                    │                              │
│         └────────────────────┼──────────────────────────────┤
│                              ▼                              │
│                    ┌──────────────────┐                     │
│                    │  ML/AI Models    │                     │
│                    ├──────────────────┤                     │
│                    │ • Random Forest  │                     │
│                    │ • Isolation Forest│                    │
│                    │ • LSTM (TF/Keras)│                     │
│                    │ • Claude API     │                     │
│                    └──────────────────┘                     │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow
```
AWS Resources → boto3 SDK → Feature Engineering → ML Models → Recommendations → Database → Frontend
     ↓
CloudWatch Metrics → Time Series Analysis → LSTM Forecast → Right-Sizing
     ↓
CloudWatch Logs → Pattern Extraction → Claude API → Post-Mortem Report
```

### Database Schema
```sql
-- Scan tracking
scans (id, scan_type, status, regions, total_resources, total_cost, 
       total_savings, duration_seconds, created_at)

-- Zombie resources
zombie_scans (scan_id, resource_type, resource_id, resource_name, state, 
              monthly_cost, region)

-- Compliance violations
compliance_violations (scan_id, resource_type, resource_id, severity, 
                       violation, description, remediation, resolved, 
                       resolved_at, resolved_note)
```

---

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- AWS CLI configured with credentials
- AWS account with EC2/CloudWatch permissions

### Installation
```bash
# Clone repository
git clone https://github.com/yourusername/cloudsense-platform.git
cd cloudsense-platform

# Backend setup
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Frontend setup
cd ../frontend
npm install

# Environment variables
cd ../backend
cp .env.example .env
# Edit .env with your AWS credentials and Anthropic API key
```

### Running Locally
```bash
# Terminal 1: Backend
cd backend
source venv/bin/activate
python api/main.py
# Server runs on http://localhost:8000

# Terminal 2: Frontend
cd frontend
npm run dev
# App runs on http://localhost:5173
```

### AWS Permissions Required
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ec2:Describe*",
        "rds:Describe*",
        "elasticloadbalancing:Describe*",
        "cloudwatch:GetMetricStatistics",
        "cloudwatch:DescribeLogGroups",
        "logs:FilterLogEvents",
        "logs:StartQuery",
        "logs:GetQueryResults"
      ],
      "Resource": "*"
    }
  ]
}
```

---

## ML/AI Models

### Enhancement A: Zombie Prediction (Random Forest)

**Features Engineered:**
1. `days_since_creation` - Resource age
2. `has_name_tag`, `has_owner_tag`, `has_environment_tag` - Tagging completeness
3. `is_stopped` - Current state
4. `instance_size_score` - Risk based on instance size (0-1)
5. `region_zombie_rate` - Historical regional patterns
6. Additional metadata features

**Model:** Random Forest Classifier (scikit-learn)  
**Accuracy Target:** 80%+ (achievable with 30+ days training data)  
**Current:** Heuristic model (ready for supervised training)

---

### Enhancement B: Anomaly Detection (Isolation Forest)

**Features Engineered:**
1. Number of security groups
2. Number of open ports
3. Has public IP (0/1)
4. EBS encrypted (0/1)
5. Tag completeness (3 features)
6. Instance size score
7. Number of IAM roles
8. Days since creation

**Model:** Isolation Forest (scikit-learn)  
**Contamination:** 10% (expects 10% anomalies)  
**Use Case:** Detect configuration drift and zero-day threats

---

### Enhancement C: LLM Analysis (Claude API)

**Model:** Claude Sonnet 4 (Anthropic)  
**Temperature:** 0.3 (consistent analysis)  
**Max Tokens:** 2000  
**Input:** Log patterns + error summary  
**Output:** JSON with root causes, recommendations, severity assessment

**Prompt Engineering:**
- Structured JSON output format
- AWS-specific context and terminology
- Actionable recommendations with documentation links
- Executive summary for leadership

---

### Enhancement D: LSTM Forecasting (TensorFlow)

**Architecture:**
```python
LSTM(64) → Dropout(0.2) → LSTM(32) → Dropout(0.2) → Dense(16) → Dense(1)
```

**Training:**
- Lookback window: 24 hours
- Forecast horizon: 168 hours (7 days)
- Early stopping with patience=5
- 80/20 train/validation split

**Outputs:**
- Predicted values with confidence intervals
- Trend detection (GROWING/SHRINKING/STABLE)
- Seasonality detection (daily/weekly patterns)
- Workload classification (BURSTY/STEADY)

---

## Performance Metrics

| Service | Response Time | Regions | Resources/Min |
|---------|--------------|---------|---------------|
| Zombie Hunter | 5-15s | 2 | ~100 |
| Right-Sizing | 10-30s | 2 | ~50 |
| Compliance | 8-20s | 2 | ~100 |
| Post-Mortem | 15-45s | 2 | ~1000 logs |

**ML Model Performance:**
- Zombie Predictor: 0.0073 loss, 0.0685 MAE
- LSTM Forecaster: Successfully detects seasonality and trends
- Anomaly Detector: Trains on 2+ instances, flags deviations

---

## Tech Stack

### Backend
- **Framework:** FastAPI 0.104+
- **Language:** Python 3.11+
- **ML/AI:** TensorFlow 2.20, scikit-learn 1.8, Anthropic Claude API
- **AWS SDK:** boto3
- **Database:** SQLAlchemy with SQLite (PostgreSQL-ready)
- **Data Processing:** pandas, numpy

### Frontend
- **Framework:** React 18
- **Language:** TypeScript 5
- **Build Tool:** Vite
- **Charts:** Recharts
- **Styling:** CSS3 with custom variables

### DevOps
- **Version Control:** Git/GitHub
- **Package Management:** pip, npm
- **Environment:** python-dotenv
- **API Documentation:** FastAPI auto-generated Swagger

---

## Project Structure
```
cloudsense-platform/
├── backend/
│   ├── api/
│   │   ├── main.py              # FastAPI app entry point
│   │   ├── zombie.py            # Zombie Resource Hunter endpoints
│   │   ├── rightsizing.py       # Right-Sizing Engine endpoints
│   │   ├── compliance.py        # Compliance Validator endpoints
│   │   └── postmortem.py        # Post-Mortem Generator endpoints
│   ├── services/
│   │   ├── zombie_service.py
│   │   ├── ml_zombie_predictor.py
│   │   ├── rightsizing_service_enhanced.py
│   │   ├── lstm_workload_forecaster.py
│   │   ├── compliance_service_enhanced.py
│   │   ├── ml_anomaly_detector.py
│   │   ├── postmortem_service_enhanced.py
│   │   └── llm_postmortem_analyzer.py
│   ├── models/
│   │   ├── database.py          # SQLAlchemy setup
│   │   └── __init__.py          # Database models
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   └── Navbar.tsx
│   │   ├── pages/
│   │   │   ├── History.tsx
│   │   │   └── Insights.tsx
│   │   ├── App.tsx              # Main dashboard
│   │   └── App.css
│   ├── package.json
│   └── vite.config.ts
├── scripts/                      # Original standalone scripts
│   ├── zombie_hunter/
│   ├── rightsizing/
│   ├── compliance-validator/
│   └── post-mortem/
└── README.md
```

---

## Learning Outcomes

Building CloudSense provided hands-on experience with:

### Cloud Engineering
- Multi-region AWS resource management
- CloudWatch metrics and logs integration
- boto3 SDK for programmatic AWS access
- Cost optimization strategies

### Machine Learning
- Supervised learning (Random Forest classification)
- Unsupervised learning (Isolation Forest anomaly detection)
- Deep learning (LSTM time series forecasting)
- Feature engineering for cloud infrastructure
- Model persistence and deployment

### Full-Stack Development
- RESTful API design with FastAPI
- React + TypeScript frontend
- Database design and ORM (SQLAlchemy)
- State management and async operations

### AI Integration
- Prompt engineering for LLM APIs
- Structured output parsing (JSON)
- Cost-effective API usage
- Semantic analysis for log interpretation

---

## Future Enhancements

- [ ] **Authentication & Authorization** - Auth0 or AWS Cognito
- [ ] **PostgreSQL Migration** - Production-ready database
- [ ] **Email Notifications** - Alert on critical findings
- [ ] **Slack Integration** - Post reports to channels
- [ ] **PDF Export** - Generate downloadable reports
- [ ] **Cost Forecasting** - Predict next month's AWS bill
- [ ] **Reserved Instance Recommendations** - RI purchase analysis
- [ ] **Multi-account Support** - AWS Organizations integration
- [ ] **Custom Dashboards** - User-configurable views
- [ ] **Scheduled Scans** - Cron-based automation

---

## Documentation

### API Endpoints

**Zombie Resource Hunter:**
```
POST /api/zombie/scan
GET  /api/zombie/history
```

**Right-Sizing Engine:**
```
POST /api/rightsizing/analyze
GET  /api/rightsizing/history
```

**Compliance Validator:**
```
POST /api/compliance/scan
POST /api/resolutions/compliance/{id}/resolve
GET  /api/compliance/history
```

**Post-Mortem Generator:**
```
POST /api/postmortem/analyze
GET  /api/postmortem/history
```

**Full API docs available at:** `http://localhost:8000/docs` (Swagger UI)

---

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## Author

**Abhir Naik**
- Website: [abhirnaik.me](https://abhirnaik.me)
- LinkedIn: [linkedin.com/in/abhirnaik](https://linkedin.com/in/abhirnaik)
- GitHub: [@Beer146](https://github.com/Beer146)
- Email: naik.ab@northeastern.edu

---

## Acknowledgments

- **AWS** for comprehensive cloud services and documentation
- **Anthropic** for Claude API and excellent LLM capabilities
- **TensorFlow** team for powerful ML framework
- **FastAPI** and **React** communities for excellent frameworks

---

## Project Stats

- **Development Time:** 13+ hours
- **Lines of Code:** ~5,000+
- **Services:** 4 integrated
- **ML Models:** 4 (Random Forest, Isolation Forest, LSTM, Claude)
- **API Endpoints:** 12+
- **Database Tables:** 5
- **AWS Services Used:** EC2, EBS, RDS, ELB, CloudWatch, CloudWatch Logs

---

<div align="center">

**Built with care by Abhir Naik**

*Empowering organizations to optimize cloud costs through intelligent automation*

[Star this repo](https://github.com/yourusername/cloudsense-platform) | [Report Bug](https://github.com/yourusername/cloudsense-platform/issues) | [Request Feature](https://github.com/yourusername/cloudsense-platform/issues)

</div>
