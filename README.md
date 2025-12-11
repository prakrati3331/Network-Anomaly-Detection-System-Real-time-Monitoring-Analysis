# Network Anomaly Detection System

A comprehensive network traffic monitoring and anomaly detection system consisting of two main components: a web dashboard and a real-time detection service.

## Table of Contents
- [Overview](#overview)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Installation](#installation)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [API Endpoints](#api-endpoints)
- [Troubleshooting](#troubleshooting)
- [License](#license)

## Overview

This project consists of two main components:

1. **Main Dashboard** (`anomaly_detection/main.py`): A web-based dashboard for monitoring network traffic and viewing detection results.

2. **Live Detection Service** ([web/app.py](cci:7://file:///c:/Users/win10/Downloads/Anomaly%20Detection/Anomaly%20Detection/web/app.py:0:0-0:0)): A real-time service that processes network traffic and detects anomalies.

## Features

### Main Dashboard
- Real-time monitoring of network traffic
- Historical data visualization
- Anomaly detection alerts
- Severity level indicators (High, Medium, Low)
- Detailed traffic statistics
- Responsive design

### Live Detection Service
- Real-time network traffic analysis
- Anomaly detection using machine learning
- RESTful API for integration
- Logging and monitoring
- Scalable architecture

## Tech Stack

### Backend
- **Python 3.8+**
- **Flask**: Web framework
- **Scikit-learn**: Machine learning
- **Pandas**: Data processing
- **NumPy**: Numerical operations
- **Joblib**: Model persistence

### Frontend
- **HTML5/CSS3**
- **JavaScript (ES6+)**
- **Chart.js**: Data visualization
- **Tailwind CSS**: Styling
- **Font Awesome**: Icons

### Development Tools
- **Git**: Version control
- **Pip**: Package management
- **Virtualenv**: Environment management

## Installation

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)
- Git (optional)


## Running the Applications

### 1. Main Dashboard (Anomaly Prediction)
- python anomaly_detection/main.py web

### 2. Live Detection Service
- python -m web.app

### Setup

1. **Clone the repository**:
   ```bash
   git clone [ https://github.com/prakrati3331/Network-Anomaly-Detection-System-Real-time-Monitoring-Analysis ]
   cd network-anomaly-detection
