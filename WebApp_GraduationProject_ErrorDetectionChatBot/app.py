from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
import logging
import numpy as np
import pandas as pd
from sklearn.preprocessing import LabelEncoder
from functools import lru_cache
import time

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Allow frontend requests (adjust for production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Global variables for model and tokenizer
MODEL_DIR = r"C:\Users\Dell\Downloads\cwe_classifier_model-20250526T111351Z-1-001-New\cwe_classifier_model"
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Load model and tokenizer at startup
logger.info("Loading model and tokenizer...")
tokenizer = AutoTokenizer.from_pretrained(MODEL_DIR)
model = AutoModelForSequenceClassification.from_pretrained(MODEL_DIR)
model = model.to(device)
model.eval()  # Set model to evaluation mode
logger.info("Model and tokenizer loaded successfully!")

# Load CWE lookup data
logger.info("Loading CWE lookup data...")
cwe_lookup = pd.read_csv(r"C:\Users\Dell\Downloads\cwe_lookup (1).csv")
label_encoder = LabelEncoder()
label_encoder.fit(cwe_lookup['cwe_id'])
logger.info("CWE lookup data loaded successfully!")

# Input schema
class CodeInput(BaseModel):
    code: str

@lru_cache(maxsize=100)
def predict_cwe_and_description(code_snippet: str):
    inputs = tokenizer(code_snippet, return_tensors='pt', truncation=True, padding=True).to(device)
    logits = model(**inputs).logits.cpu().detach().numpy()
    class_id = int(np.argmax(logits, axis=1)[0])
    cwe_id = label_encoder.inverse_transform([class_id])[0]
    desc = cwe_lookup.loc[cwe_lookup.cwe_id == cwe_id, 'description'].item()
    # Optionally, you can also return the cwe_name or other details
    cwe_name = cwe_lookup.loc[cwe_lookup.cwe_id == cwe_id, 'cwe_name'].item()
    label_name = cwe_lookup.loc[cwe_lookup.cwe_id == cwe_id, 'label_name'].item()
    return cwe_id,cwe_name ,desc, label_name

@app.get("/")
async def read_root():
    return FileResponse("index.html")

@app.post("/predict")
async def predict(data: CodeInput, background_tasks: BackgroundTasks):
    try:
        logger.info(f"Received code for analysis: {data.code[:100]}...")
        
        # Run prediction
        cwe_id, cwe_name, description, label_name = predict_cwe_and_description(data.code)
        
        logger.info(f"Prediction result: CWE-{cwe_id}: {cwe_name}")
        return {
            "cwe_id": cwe_id,
            "cwe_name": cwe_name,
            "description": description,
            "label_name": label_name
        }
    except Exception as e:
        logger.error(f"Error during prediction: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Add startup event
@app.on_event("startup")
async def startup_event():
    logger.info("Server starting up...")
    # Warm up the model with a dummy prediction
    dummy_code = "function test() { return true; }"
    try:
        predict_cwe_and_description(dummy_code)
        logger.info("Model warm-up completed successfully!")
    except Exception as e:
        logger.error(f"Model warm-up failed: {str(e)}")