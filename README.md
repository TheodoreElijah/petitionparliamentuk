# AI Petition Search Prototype

## 🚀 What It Does
An interactive web app that lets users search UK petitions using natural language, powered by OpenAI.

## 🧠 How It Works
- Accepts freeform user input
- Uses OpenAI to interpret intent
- Ranks and returns relevant results

## 🏗️ Tech Stack

- Frontend: Streamlit web framework

  - Interactive web interface with sidebar controls
  - Data visualization using Plotly Express and Plotly Graph Objects
  - Responsive design with wide layout configuration

- Backend: Python with Streamlit server

  - Application layer: app.py (main Streamlit application)
  - Data service layer: data_service.py (handles external API calls)
  - Query processing layer: query_processor.py (AI integration)
  
- LLM: OpenAI GPT-4o

  - Natural language query interpretation
  - Intelligent data filtering and analysis
  - AI-powered insights generation
  
- CSV Handling: Pandas DataFrame

  - JSON to DataFrame conversion from Google Apps Script
  - Data validation and cleaning
  - Numeric processing for signature counts
  - Filtering, sorting, and aggregation operations

- Additional Components:

  - Data Source: Google Apps Script Web App
  - HTTP Client: Python requests library for API communication
  - Visualization: Plotly for interactive charts and graphs
  - Configuration: Streamlit config.toml for server settings

## 📦 How to Run

- Prerequisites
  - Python 3.11 or higher
  - OpenAI API key

- Installation & Setup
  - Clone this repo
  - Install dependencies:
  - pip install streamlit pandas plotly requests openai

- Set up your OpenAI API key:
  - export OPENAI_API_KEY="your-api-key-here"
  - Or create a .env file with:
  - OPENAI_API_KEY=your-api-key-here

- Running the Application
  - Start the Streamlit server:
  - streamlit run app.py --server.port 5000
  - Open your browser to http://localhost:5000

- Usage
  - Click "Load/Refresh Data" to fetch UK Parliament petition data
  - Ask natural language questions like:
  - "Show me petitions with over 100,000 signatures"
  - "Find healthcare-related petitions"
  - "What are the most popular petition topics?"
  - View AI-powered insights and interactive visualizations

- Research & Development Summary URL:
  - https://miro.com/app/board/uXjVJXqf3EI=/?share_link_id=634162919138
- Web App URL:
  - https://unboxed-petitionparliamentuk.replit.app
