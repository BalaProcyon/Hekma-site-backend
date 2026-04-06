# Hekma Backend Service

This is the FastAPI backend service for Hekma Site.

## Setup Instructions

1. **Create Virtual Environment**
   ```bash
   python3 -m venv venv
   ```

2. **Activate Virtual Environment**
   - On macOS/Linux:
     ```bash
     source venv/bin/activate
     ```
   - On Windows:
     ```bash
     venv\Scripts\activate
     ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the Development Server**
   ```bash
   uvicorn main:app --reload
   ```

5. **API Documentation**
   - Swagger UI: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
   - ReDoc: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)
