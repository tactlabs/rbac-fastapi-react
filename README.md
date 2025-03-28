# rbac-fastapi-react

A Role-Based Access Control (RBAC) implementation using FastAPI for the backend and React for the frontend.

## Features

- Role-Based Access Control (RBAC)
- FastAPI backend with modern Python
- React frontend with TypeScript
- Secure authentication and authorization
- RESTful API endpoints
- Modern and responsive UI

## Prerequisites

- Python 3.8+
- Node.js 14+
- PostgreSQL (or your chosen database)

## Backend Setup

1. activate conda 
```
python --version
    - got a result like this     
    Python 3.12.4

conda activate py312
```

2. Install dependencies:
```
cd backend
pip install -r requirements.txt
```

3. Start the FastAPI server:
```
uvicorn app:app --reload
```

## Frontend Setup

1. Install dependencies:
```
cd user-auth-ui
```

2. activate conda 
```
python --version
    - got a result like this     
    Python 3.12.4

conda activate py312

```

3. start the server 

```
npm start
```