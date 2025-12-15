# CloudSense Platform

> Unified AWS cost optimization platform with ML-powered resource analysis

![CloudSense Platform](https://img.shields.io/badge/status-active-success.svg)
![Python](https://img.shields.io/badge/python-3.13-blue.svg)
![React](https://img.shields.io/badge/react-18-blue.svg)
![FastAPI](https://img.shields.io/badge/fastapi-0.115-green.svg)

## 🚀 Overview

CloudSense is a full-stack AWS cost intelligence platform that helps organizations identify and eliminate cloud waste through automated resource scanning and intelligent right-sizing recommendations.

### Key Features

- **💀 Zombie Resource Hunter**: Automatically detects idle and unused AWS resources (EC2, EBS, RDS, ELB)
- **📏 Right-Sizing Engine**: Analyzes CloudWatch metrics to recommend optimal instance types
- **🔄 Multi-Region Support**: Scans across multiple AWS regions simultaneously
- **📊 Real-Time Analysis**: Processes live CloudWatch data for accurate recommendations
- **💰 Cost Optimization**: Calculates potential monthly and annual savings

## 🏗️ Architecture
```
cloudsense-platform/
├── backend/              # FastAPI REST API
│   ├── api/             # API endpoints
│   ├── services/        # Business logic layer
│   └── models/          # Data models
├── frontend/            # React TypeScript UI
│   └── src/
│       ├── components/
│       └── pages/
└── scripts/             # AWS scanning modules
    ├── zombie_hunter/   # Zombie resource detection
    └── rightsizing/     # Right-sizing analysis
```

## 🛠️ Tech Stack

**Backend:**
- FastAPI (Python 3.13)
- boto3 (AWS SDK)
- SQLAlchemy (planned)

**Frontend:**
- React 18
- TypeScript
- Vite

**AWS Services:**
- EC2, EBS, RDS, ELB
- CloudWatch

## 📦 Installation

### Prerequisites

- Python 3.13+
- Node.js 18+
- AWS credentials configured (`~/.aws/credentials`)

### Backend Setup
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python api/main.py
```

Backend runs on `http://localhost:8000`

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

Frontend runs on `http://localhost:5173`

## 🔧 Configuration

Update `scripts/zombie_hunter/config.yaml` and `scripts/rightsizing/config.yaml`:
```yaml
aws:
  regions:
    - us-east-1
    - us-west-2

thresholds:
  ec2:
    stopped_days: 7
    cpu_threshold: 5
```

## 🎯 Usage

1. Navigate to `http://localhost:5173`
2. Click "Run Scan" to detect zombie resources
3. Click "Analyze Resources" for right-sizing recommendations
4. Review cost savings opportunities

## 📊 Features Roadmap

- [x] Zombie resource detection (EC2, EBS, RDS, ELB)
- [x] Right-sizing recommendations
- [ ] Historical scan tracking with PostgreSQL
- [ ] ML-powered cost forecasting
- [ ] AI-generated insights (OpenAI integration)
- [ ] Compliance-as-Code validator
- [ ] Post-mortem generator
- [ ] Authentication & multi-tenancy
- [ ] Deployment automation

## 🤝 Contributing

This is a personal portfolio project. Feedback and suggestions are welcome!

## 📝 License

MIT License - feel free to use for learning purposes

## 👨‍💻 Author

**Abhir Naik**
- Portfolio: [abhirnaik.me](https://abhirnaik.me)
- LinkedIn: [linkedin.com/in/abhirnaik](https://linkedin.com/in/abhirnaik)
- GitHub: [@abhirnaik](https://github.com/abhirnaik)

---

*Built with ☕ and late-night coding sessions*
