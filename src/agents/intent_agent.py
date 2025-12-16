import torch
import pickle
import os
import json
from transformers import DistilBertTokenizer, DistilBertForSequenceClassification
from src.agents.base_agent import BaseAgent

class IntentAgent(BaseAgent):
    def __init__(self):
        super().__init__("Intent")
        
        # Konfigurasi Path Model
        self.base_model_path = "models" 
        self.intent_path = os.path.join(self.base_model_path, "main_intent_classifier_pytorch")
        self.problem_path = os.path.join(self.base_model_path, "doctor_problem_classifier_pytorch")
        
        self.models_loaded = False
        self._load_models()

        # --- Load Daftar Nama Bean untuk Rule-Based Matching ---
        # Load JSON mentah saja agar cepat (tidak perlu Frame object yang berat)
        try:
            with open('datasets/coffee_beans.json', 'r', encoding='utf-8') as f:
                beans_data = json.load(f)
                # Simpan nama-nama bean dalam huruf kecil untuk pencarian
                self.known_bean_names = [b['name'].lower() for b in beans_data]
        except Exception as e:
            self.logger.error(f"Gagal memuat nama bean: {e}")
            self.known_bean_names = []

    def _load_models(self):
        try:
            self.logger.info("Memuat model klasifikasi...")
            self.intent_tokenizer = DistilBertTokenizer.from_pretrained(self.intent_path)
            self.intent_model = DistilBertForSequenceClassification.from_pretrained(self.intent_path)
            with open(os.path.join(self.intent_path, 'label_encoder.pkl'), 'rb') as f:
                self.intent_le = pickle.load(f)

            self.doc_tokenizer = DistilBertTokenizer.from_pretrained(self.problem_path)
            self.doc_model = DistilBertForSequenceClassification.from_pretrained(self.problem_path)
            with open(os.path.join(self.problem_path, 'label_encoder.pkl'), 'rb') as f:
                self.doc_le = pickle.load(f)
            self.models_loaded = True
        except Exception as e:
            self.logger.error(f"Gagal memuat model: {e}")
            self.models_loaded = False

    def _predict(self, text, model, tokenizer, label_encoder):
        inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True, max_length=64)
        with torch.no_grad():
            logits = model(**inputs).logits
        predicted_id = torch.argmax(logits, dim=1).item()
        return label_encoder.inverse_transform([predicted_id])[0]

    def process(self):
        """
        Hybrid Intent Detection: Database Check -> PyTorch Model
        """
        user_input = self.blackboard.get_last_user_input()
        if not user_input: return

        user_input_lower = user_input.lower()

        # --- RULE 1: EXACT BEAN MATCHING ---
        # Jika user hanya menyebut nama bean (atau mengandung nama bean),
        # Prioritaskan Master Brewer (untuk resep) atau Sommelier.
        # Set default ke 'master_brewer' karena biasanya user cari resep.
        
        is_bean_mentioned = any(bean in user_input_lower for bean in self.known_bean_names)
        
        if is_bean_mentioned:
            # Sek wait, kalau dia bilang "My Ethiopia is sour", itu Doctor.
            # Berarti cek keyword masalah sederhana.
            problem_keywords = ['sour', 'bitter', 'weak', 'bad', 'tastes', 'acidic', 'hollow']
            has_problem_keyword = any(k in user_input_lower for k in problem_keywords)

            if not has_problem_keyword:
                self.logger.info(f"Rule-Based Override: Bean detected ('{user_input}'), routing to Master Brewer.")
                self.blackboard.set_intent('master_brewer')
                return

        # --- RULE 2: PYTORCH MODEL (FALLBACK) ---
        if not self.models_loaded: return

        intent = self._predict(user_input, self.intent_model, self.intent_tokenizer, self.intent_le)
        self.logger.info(f"Model Prediction: {intent}")
        
        self.blackboard.set_intent(intent)

        if intent == 'doctor':
            problem = self._predict(user_input, self.doc_model, self.doc_tokenizer, self.doc_le)
            self.blackboard.update_evidence("initial_problem_classification", problem)
            self.blackboard.update_evidence(f"problem_{problem}", 1.0)