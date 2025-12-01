
# AI-assisted Unit Test Generation

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Code Style: Black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

---

## 📖 Project Overview

**AI-assisted Unit Test Generation** is an intelligent system designed to help software developers automatically generate high-quality unit tests for their code. Writing unit tests is often time-consuming and repetitive, but this project leverages advanced AI models to generate tests quickly and efficiently. 

The system also provides detailed metrics, hallucination detection, and performance analysis to ensure that the generated tests are accurate, useful, and maintainable. It supports multiple AI models and integrates visualization tools to make test evaluation easier.

---

## ✨ Key Features

- **AI-Powered Test Generation**: Automatically generates unit tests for your code.
- **Hallucination Detection**: Detects potential inaccuracies or irrelevant outputs in generated tests.
- **Comprehensive Metrics**: Tracks quality using BLEU, ROUGE, hallucination rates, code coverage, and test effectiveness.
- **Interactive Dashboard**: Visualizes test generation results and model performance.
- **Multi-Model Support**: Works with multiple LLM providers (OpenAI, Anthropic, etc.) for flexibility.

---

## 🚀 Installation

1. **Clone the repository**:

git clone https://github.com/yehiahesham2938/AI-assisted-Unit-Test-Generation.git
cd AI-assisted-Unit-Test-Generation


2. **Create a virtual environment**:


python -m venv venv
# Linux/macOS
source venv/bin/activate
# Windows
venv\Scripts\activate


3. **Install dependencies**:


pip install -r requirements.txt


---

## 🛠️ Usage

### Generate Unit Tests

python -m ai_testgen.generate_tests --input your_code.py --output tests/


### Analyze Hallucinations


python -m analysis.analyze_hallucination_metrics


### Generate Metrics Dashboard


python -m analysis.generate_dashboard




## 📁 Project Structure

AI-assisted-Unit-Test-Generation/
├── ai_testgen/              
│   ├── generators/          # Test generation modules
│   ├── models/              # AI model integrations
│   └── utils/               # Helper functions
│
├── analysis/                
│   ├── Hallucination&Plots/ # Metrics & visualizations
│   ├── analyze_hallucination_metrics.py
│   └── generate_dashboard.py
│
├── tests/                   # Example test files
├── examples/                # Sample usage scripts
├── docs/                    # Documentation
├── requirements.txt         # Dependencies
└── README.md                # Project overview




## 📊 Metrics & Analysis

The project includes robust evaluation tools:

* **Hallucination Rate**: Percentage of generated tests that contain inaccuracies.
* **Code Coverage**: Measures how well the generated tests cover the original code.
* **Test Effectiveness**: Evaluates the quality and reliability of generated tests.
* **Model Comparison**: Compare the performance of different AI models in test generation.

### Viewing Metrics


python -m analysis.analyze_hallucination_metrics


Open the generated `hallucination_analysis.html` in a browser to explore the interactive dashboard.


## 🤝 Contributing

We welcome contributions!

1. Fork the repository
2. Create a new branch:


git checkout -b feature/your-feature


3. Commit your changes:


git commit -m "Add new feature"


4. Push to the branch:


git push origin feature/your-feature


5. Open a Pull Request



## 📄 License

This project is licensed under the **MIT License**. See the [LICENSE](LICENSE) file for details.



## 📧 Contact

For questions or feedback, please open an issue or contact the maintainers.



