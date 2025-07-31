# card_generator

1. Setup environment variables:
```sh
cp .env.example .env
```

2. Install dependencies:
```sh 
pip install -r requirements.txt
```

3. Run backend:
```sh
uvicorn api.main:app --port <your-port>
```

4. Run frontend:
```sh
streamlit run app.py
```
