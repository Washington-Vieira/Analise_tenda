# Análise Temporal de Arquivos Excel

## Overview

This is a Streamlit-based web application designed for temporal analysis of Excel files, specifically focused on analyzing entry/exit peaks by project lines. The application processes Excel data containing movement records with timestamps and provides visualizations to identify patterns and trends in the data.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture
- **Framework**: Streamlit
- **Layout**: Wide layout with expandable sidebar
- **Components**: File uploader, data visualization dashboard, configuration panel
- **Styling**: Custom page configuration with emoji icons and responsive design

### Backend Architecture
- **Processing Layer**: Modular utility classes for data processing and visualization
- **Data Pipeline**: Excel file ingestion → Data validation → Temporal processing → Visualization
- **Error Handling**: Comprehensive exception handling with user-friendly error messages

## Key Components

### 1. Main Application (`app.py`)
- **Purpose**: Entry point and UI orchestration
- **Features**: 
  - File upload interface
  - Progress indicators with spinners
  - Sidebar configuration panel
  - Main dashboard area for visualizations

### 2. Data Processor (`utils/data_processor.py`)
- **Purpose**: Handle Excel file processing and data cleaning
- **Key Functions**:
  - Multi-engine Excel file loading (openpyxl, xlrd)
  - Column validation for required fields
  - Temporal data processing with datetime conversion
  - Data cleaning and normalization

### 3. Visualizer (`utils/visualizer.py`)
- **Purpose**: Generate interactive charts and visualizations
- **Key Functions**:
  - Timeline charts for temporal analysis
  - Project line comparison visualizations
  - Hourly data aggregation
  - Interactive Plotly charts with hover functionality

## Data Flow

1. **File Upload**: User uploads Excel file through Streamlit interface
2. **Data Ingestion**: DataProcessor loads and validates Excel file
3. **Data Processing**: 
   - Convert date/time columns to proper datetime format
   - Clean and validate data structure
   - Aggregate data by time periods and project lines
4. **Visualization**: Visualizer creates interactive charts
5. **Display**: Results presented in main dashboard area

## External Dependencies

### Core Libraries
- **streamlit**: Web application framework
- **pandas**: Data manipulation and analysis
- **plotly**: Interactive visualization library
- **numpy**: Numerical computing
- **scipy**: Scientific computing (specifically signal processing for peak detection)

### Excel Processing
- **openpyxl**: Primary Excel engine for .xlsx files
- **xlrd**: Fallback engine for older Excel formats

### Data Processing
- **datetime**: Date and time manipulation
- **io.BytesIO**: In-memory file handling

## Deployment Strategy

### Development Environment
- **Platform**: Streamlit local development server
- **Configuration**: Wide layout with expanded sidebar by default
- **File Handling**: In-memory processing for uploaded files

### Production Considerations
- **Scalability**: Designed for single-user sessions with file-based processing
- **Memory Management**: Uses in-memory DataFrame operations
- **Error Recovery**: Graceful degradation with multiple Excel engine fallbacks

### Key Architectural Decisions

1. **Modular Design**: Separated concerns into utility classes for maintainability
   - **Rationale**: Easier testing, debugging, and feature extension
   - **Benefits**: Clean code organization, reusable components

2. **Multi-Engine Excel Support**: Implemented fallback mechanism for Excel processing
   - **Problem**: Different Excel formats and potential library conflicts
   - **Solution**: Try openpyxl first, fallback to xlrd
   - **Benefits**: Broader file format compatibility

3. **Dual File Processing**: Implemented separate upload for entrada/saída files
   - **Date**: July 23, 2025
   - **Rationale**: User requested separate analysis of positive (entrada) and negative (saída) values
   - **Implementation**: Two file uploaders with automatic type marking and value normalization
   - **Benefits**: Clear separation of concerns, accurate entrada/saída comparison

4. **Enhanced Date Processing**: Extract day number and hour from DD/MM/YYYY HH:MM:SS format
   - **Date**: July 23, 2025
   - **Features**: Extracts day (1-31) and hour (0-23) for granular temporal analysis
   - **Benefits**: More precise peak detection and temporal pattern analysis

5. **Streamlit Framework Choice**: Selected for rapid prototyping and deployment
   - **Rationale**: Quick development cycle, built-in UI components
   - **Trade-offs**: Limited customization vs. faster development

6. **Plotly for Visualizations**: Interactive charts with hover functionality
   - **Benefits**: Rich interactivity, professional appearance
   - **Features**: Timeline analysis, entrada/saída comparisons, responsive design

7. **Real-time Processing**: File processing occurs immediately after upload
   - **Approach**: In-memory processing with progress indicators
   - **Benefits**: Immediate feedback, no persistent storage requirements