# UK Parliament Petitions Query Tool

## Overview

This is a Streamlit-based web application that provides natural language querying capabilities for UK Parliament petition data. The application allows users to ask questions in plain English about petition data and receive intelligent responses powered by OpenAI's GPT models. Users can explore petitions by topic, signature count, status, and other criteria through an intuitive interface that combines data visualization with AI-powered analysis.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture
- **Framework**: Streamlit web framework for rapid prototyping and deployment
- **Layout**: Wide layout with expandable sidebar for data management controls
- **State Management**: Session-based state management using Streamlit's built-in session state
- **Visualization**: Plotly Express and Plotly Graph Objects for interactive charts and data visualization
- **User Interface**: Clean, government-themed interface with emoji icons and responsive design

### Backend Architecture
- **Application Layer**: Single-file Streamlit application (`app.py`) serving as the main entry point
- **Data Service Layer**: Dedicated service module (`data_service.py`) for external data fetching and processing
- **Query Processing Layer**: AI-powered natural language processing module (`query_processor.py`) using OpenAI GPT models
- **Data Processing**: Pandas-based data manipulation and analysis pipeline

### Data Architecture
- **Data Source**: External Google Apps Script endpoint providing UK Parliament petition data
- **Data Format**: JSON response converted to Pandas DataFrame with structured columns (Petition title, URL, State, Signatures Count)
- **Data Validation**: Numeric validation for signature counts with error handling for malformed data
- **Caching Strategy**: Session-based caching to avoid repeated API calls during user session

### AI Integration
- **Model**: OpenAI GPT-4o for natural language understanding and query interpretation
- **Processing Pipeline**: Structured prompt engineering with data context generation
- **Response Format**: JSON-structured responses containing query interpretation, filtering criteria, and analytical insights
- **Error Handling**: Graceful fallback mechanisms for API failures or invalid responses

## External Dependencies

### Third-Party Services
- **OpenAI API**: GPT-4o model for natural language processing and query interpretation
- **Google Apps Script**: External data endpoint for UK Parliament petition information
- **UK Parliament**: Underlying data source for petition information

### Python Libraries
- **streamlit**: Web application framework and user interface
- **pandas**: Data manipulation and analysis
- **plotly**: Interactive data visualization (express and graph_objects modules)
- **requests**: HTTP client for external API communication
- **openai**: Official OpenAI Python client library

### Environment Configuration
- **OPENAI_API_KEY**: Required environment variable for OpenAI API authentication
- **Timeout Settings**: 30-second timeout for external data requests
- **Error Handling**: Comprehensive exception handling for network failures and data parsing errors