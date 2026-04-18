# 💰 Expense Tracker - Financial Intelligence Dashboard

<palign="center">
![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.56-FF4B4B?logo=streamlit&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![Status](https://img.shields.io/badge/Status-Active-success)
![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)
</p>

> A data-driven FinTech application for real-time expense tracking, automated categorization, and visual spending analytics.

---

## 📸 Dashboard Preview

```
┌─────────────────────────────────────────────────────────────────┐
│                    💰 Expense Tracker                            │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐         │
│  │  Income  │  │ Expenses │  │  Balance │  │ Savings  │         │
│  │ 15,843   │  │  8,521   │  │  7,322   │  │  46.2%   │         │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘         │
├─────────────────────────────────────────────────────────────────┤
│         📊 Category Breakdown      │    📈 Monthly Trends        │
│                                    │                            │
│         [Pie Charts]               │    [Bar + Line Charts]      │
├─────────────────────────────────────────────────────────────────┤
│              💳 Transaction History                              │
│              [Interactive Data Table]                            │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Key Features

| Feature | Description |
|---------|-------------|
| 📊 **Real-time Dashboard** | Instant overview of total balance, monthly spending, and top expense categories |
| 🔍 **Dynamic Filtering** | Filter transactions by date range, category, or payment account |
| 📈 **Visual Analytics** | Interactive charts for spending patterns and budget variances using Plotly |
| 💳 **Multi-Account Support** | Track expenses across multiple accounts (acct_1, acct_2, acct_3) |
| 📁 **Export Functionality** | Download filtered data as CSV for external analysis |
| 🌙 **Dark Theme** | Modern, eye-friendly dark mode interface |

---

## 🛠 Tech Stack

<p align="center">
  <img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python"/>
  <img src="https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white" alt="Streamlit"/>
  <img src="https://img.shields.io/badge/Pandas-150458?style=for-the-badge&logo=pandas&logoColor=white" alt="Pandas"/>
  <img src="https://img.shields.io/badge/Plotly-3F4F75?style=for-the-badge&logo=plotly&logoColor=white" alt="Plotly"/>
  <img src="https://img.shields.io/badge/NumPy-013243?style=for-the-badge&logo=numpy&logoColor=white" alt="NumPy"/>
</p>

---

## 📁 Project Structure

```
expense-tracker/
│
├── 📄 app.py                    # Main Streamlit application
├── 📄 requirements.txt          # Python dependencies
├── 📄 README.md                 # Project documentation
│
├── 📂 src/
│   └── 📄 data_processor.py     # Data loading & processing module
│
├── 📂 data/
│   ├── 📄 Expenses_clean.csv    # Expense transaction data
│   └── 📄 Income_clean.csv      # Income transaction data
│
└── 📂 .venv/                    # Virtual environment
```

---

## ⚡ Quick Start

### Prerequisites

- Python 3.11+
- `uv` package manager (recommended) or `pip`

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/maddaikaran/expense-tracker.git
   cd expense-tracker
   ```

2. **Create virtual environment**
   ```bash
   uv venv
   ```

3. **Activate the environment**
   ```bash
   # Windows
   .venv\Scripts\activate
   
   # Linux/macOS
   source .venv/bin/activate
   ```

4. **Install dependencies**
   ```bash
   uv pip install -r requirements.txt
   ```

5. **Run the application**
   ```bash
   streamlit run app.py
   ```

6. **Open in browser**
   ```
   http://localhost:8501
   ```

---

## 📊 Data Format

### Expenses CSV (`Expenses_clean.csv`)

| Column | Description |
|--------|-------------|
| `date_time` | Transaction timestamp |
| `category` | Expense category (Food, Transport, Cafe, Health, etc.) |
| `account` | Account used (acct_1, acct_2, acct_3) |
| `amount` | Transaction amount in BYN |
| `currency` | Currency code (BYN - Belarusian Ruble) |
| `tags` | Custom tags for categorization |

### Income CSV (`Income_clean.csv`)

| Column | Description |
|--------|-------------|
| `date_time` | Income timestamp |
| `category` | Income source (Job, Second work, Gift, etc.) |
| `account` | Receiving account |
| `amount` | Income amount in BYN |
| `currency` | Currency code |
| `tags` | Custom tags |

---

## 📈 Features in Action

### Dashboard Metrics
- **Total Income**: Sum of all income transactions
- **Total Expenses**: Sum of all expense transactions
- **Net Balance**: Income minus expenses
- **Savings Rate**: Percentage of income saved

### Visualizations
| Chart Type | Purpose |
|------------|---------|
| Donut Chart | Category-wise expense/income distribution |
| Bar Chart | Monthly income vs expenses comparison |
| Line Chart | Savings trend over time |
| Area Chart | Daily spending patterns |
| Bar Chart | Account-wise distribution |

### Filtering Options
- **Date Range**: Select custom start and end dates
- **Categories**: Multi-select expense/income categories
- **Accounts**: Filter by specific payment accounts

---

## 📋 Expense Categories

| Category | Description |
|----------|-------------|
| 🍕 Food | Groceries and food items |
| ☕ Cafe | Cafes and restaurants |
| 🚌 Public transport | Bus, metro, public transit |
| 🚕 Taxi | Cab services |
| 🏥 Health | Medical expenses |
| 🎬 Leisure | Entertainment and hobbies |
| 🎁 Gifts | Gift purchases |
| 👔 Clothes | Clothing and apparel |
| 💵 Loan given | Money lent to others |

---

## 🔮 Roadmap

- [ ] Add budget setting and alerts
- [ ] Implement recurring transaction tracking
- [ ] Add investment portfolio tracking
- [ ] Machine learning for expense prediction
- [ ] Multi-currency support
- [ ] Mobile-responsive improvements

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request


<p align="center">
  <b>Made with ❤️ for Personal Finance Management</b>
</p>

<p align="center">
  <a href="#-expense-tracker---financial-intelligence-dashboard">⬆️ Back to Top</a>
</p>
