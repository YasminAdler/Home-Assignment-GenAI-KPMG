# Medical Services Chatbot

A microservice-based chatbot system that answers questions about medical services for Israeli health funds (Maccabi, Meuhedet, and Clalit) based on user-specific information.

## Features

- Stateless microservice architecture using FastAPI
- Streamlit frontend with bilingual interface (Hebrew/English)
- Azure OpenAI integration for intelligent conversation
- User information collection and validation
- Q&A functionality for health fund services
- Client-side state management for multi-user support
- Comprehensive error handling and logging

## Project Structure

```
medical-chatbot/
├── backend/               # FastAPI backend service
├── frontend/              # Streamlit frontend application
├── data/                  # Knowledge base data
├── tests/                 # Test files
├── logs/                  # Log files directory
├── requirements.txt       # Project dependencies
├── README.md              # Project documentation
└── .env.example           # Example environment variables
```

## Setup and Installation

### Prerequisites

- Python 3.8+
- Access to Azure OpenAI Service
- HTML knowledge base files

### Step 1: Clone the Repository

```bash
git clone https://github.com/YasminAdler/Home-Assignment-GenAI-KPMG.git
cd medical-chatbot
```

### Step 2: Set Up Virtual Environment

```bash
python -m venv venv
venv\Scripts\activate
pip install -r part_2_medical-chatbot/logs/requirements.txt
```


### Step 3: Add Knowledge Base Files

Place your HTML knowledge base files in the `data/phase2_data/` directory:

```bash
mkdir -p data/phase2_data
# Copy your HTML files to data/phase2_data/
```

### Step 4: Run the Backend Service

```bash
cd part_2_medical-chatbot/backend
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at http://localhost:8000

### Step 5: Run the Frontend Application

In a new terminal, run:

```bash
cd part_2_medical-chatbot/frontend
streamlit run app.py
```

The frontend will be available at http://localhost:8501

## Usage

1. Open the frontend application in your browser
2. Select your preferred language (English or Hebrew)
3. Follow the chatbot's instructions to provide your personal information
4. Once information collection is complete, you can start asking questions about healthcare services

## API Documentation

Once the backend is running, you can access the API documentation at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Testing

Run the tests using pytest:

```bash
pytest tests/
```

## Logging

Logs are stored in the `logs/` directory. The log level can be configured in the `.env` file.


## Contact

Yasmin Adler- 

0587811146
adleryasmin@gmail.com

