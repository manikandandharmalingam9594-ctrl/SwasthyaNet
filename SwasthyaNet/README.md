# SwasthyaNet

SwasthyaNet is a real-time, multilingual AI platform for district-level healthcare administration. It manages PHCs and CHCs and provides dashboards for district administrators and data-entry functionality for PHC/CHC staff.

## Project Structure

- `frontend/`: React + Vite frontend
- `backend/`: FastAPI backend
- `database/`: Database scripts and migrations
- `ai/`: AI/ML models and scripts
- `docs/`: Project documentation

## How to start

### Frontend
1. Navigate to the `frontend/` directory.
2. Install dependencies: `npm install`
3. Start the dev server: `npm run dev`

### Backend
1. Navigate to the `backend/` directory.
2. Create and activate a virtual environment: `python -m venv venv` and `venv\Scripts\activate` (Windows) or `source venv/bin/activate` (Mac/Linux).
3. Install dependencies: `pip install -r requirements.txt`
4. Start the dev server: `uvicorn main:app --reload`
