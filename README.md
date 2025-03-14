# 🚀 AI Model Gateway - AI Model Serving & Secure Gateway

## Overview
The **AI Model Gateway** is a **FastAPI-based model serving gateway** designed to securely handle AI model execution requests across distributed **Kubernetes clusters**. It provides a **scalable, secure, and efficient way to manage AI model inference**, ensuring authentication, authorization, caching, and robust pre/post-processing mechanisms.

🔹 **Key Features:**
- **🚀 AI Model Gateway** – Routes inference requests to ML models deployed in Kubernetes clusters.
- **🔐 Authentication & Authorization** – Validates requests via JWT & API tokens.
- **🛠 Data Transformation & Processing** – Prepares input/output for seamless model execution.
- **⚡ Caching for Low Latency** – Implements Redis-based caching to optimize performance.
- **🌍 Multi-Model Orchestration** – Manages multiple models efficiently across clusters.
- **🛡️ Secure API Proxying** – Uses NGINX for request routing & load balancing.

---

## 📌 Architecture & Components
### **1️⃣ Secure Model Gateway (FastAPI + NGINX)**
- Handles **incoming model inference requests**.
- Routes traffic securely via **NGINX reverse proxy**.
- Supports **multi-tenant AI inference execution**.

### **2️⃣ Authentication & Authorization**
- **User authentication via JWT-based tokens** (`validate_auth_token_util.py`).
- **Authorization to prevent unauthorized model access**.

### **3️⃣ AI Model Execution Pipeline**
- **Preprocessing layer**: Normalizes & transforms input (`transform_input_data_for_model_util.py`).
- **Model execution handler**: Routes calls to the correct ML model.
- **Post-processing layer**: Converts outputs into structured responses.

### **4️⃣ High-Performance Caching with Redis**
- **Speeds up model responses** for frequently accessed data.
- Implemented in **`redis_feature_plugin.py`**.

### **5️⃣ Secure Model Deployment & Routing (NGINX + Docker)**
- Uses **NGINX reverse proxy** (`vps-nginx/nginx.conf`).
- Deploys containerized **FastAPI app** via **Docker** (`vps-model-gateway/Dockerfile`).

### **6️⃣ Kubernetes-Ready for Large-Scale AI Inference**
- Designed to run in **distributed Kubernetes clusters**.
- Ensures **scalability & load balancing** for AI model execution.

---

## 🚀 Quick Start Guide
### **1️⃣ Clone the Repository**
```sh
git clone https://github.com/vinay-jayanna/ai-model-gateway.git
cd ai-model-gateway
```

### **2️⃣ Install Dependencies**
```sh
pip install -r vps-model-gateway/requirements.txt
```

### **3️⃣ Run the FastAPI Application**
```sh
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

### **4️⃣ Start the NGINX Reverse Proxy**
```sh
docker build -t vps-nginx ./vps-nginx
docker run -p 8080:80 vps-nginx
```

### **5️⃣ Run Tests**
```sh
pytest vps-model-gateway/tests
```

---

## 🔥 Why Use This?
🔹 **Enterprise-Grade AI Model Serving** – Secure, scalable, and Kubernetes-ready.  
🔹 **Optimized for Low Latency AI Inference** – Redis caching speeds up responses.  
🔹 **Multi-Model Support** – Easily orchestrate and manage multiple AI models.  
🔹 **Production-Ready API Gateway** – Secure model execution with JWT authentication.  
🔹 **NGINX-Powered Load Balancing** – Ensures optimal performance and availability.  

---

## 📚 Additional Resources
- **🔗 Model Routing & Authentication:** [`src/utils/`](vps-model-gateway/src/utils)
- **📦 Model Execution Services:** [`src/services/`](vps-model-gateway/src/services)
- **⚡ Test Cases for API & Models:** [`tests/`](vps-model-gateway/tests)
- **🛠 NGINX Configuration for Secure Routing:** [`vps-nginx/nginx.conf`](vps-nginx/nginx.conf)


