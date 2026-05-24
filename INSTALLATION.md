# Installation Guide

This guide provides step-by-step instructions to install and set up the DayPlanner application on your system.

## Prerequisites
Before you begin, ensure you have the following installed on your system:
- `Python 3.8 or higher`
- `pip` (Python package installer)
- `virtualenv` (optional but recommended for creating a virtual environment)

## Installation Steps
1. **Clone the Repository**
   ```bash
    git clone https://github.com/srinivasagudi0/Day-Planner
    ```

2. **Change Directory**
   ```bash
    cd Day-Planner
    ```

3. **Create a Virtual Environment (Optional)**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    ```

4. **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```
5. **Add OpenAI API Key**
    For intelligent task management features, you need to set your OpenAI API key as an environment variable:

     ```
     export OPENAI_API_KEY=your_api_key_here # On Windows, use `set OPENAI_API_KEY=your_api_key_here`
     ```

6. **Run the Application**
    ```bash
    streamlit run app.py
    ```
