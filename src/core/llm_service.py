import google.generativeai as genai
import streamlit as st
import os
from src.utils.logger import setup_logger

logger = setup_logger("LLMService")

class LLMService:
    _instance = None

    def __new__(cls):
        """Singleton implementation."""
        if cls._instance is None:
            cls._instance = super(LLMService, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """Setup connection to Gemini API."""
        try:
            # Try getting API Key from Streamlit Secrets or Environment Variable
            api_key = None
            
            # Check Streamlit Secrets (Priority for deployment)
            if hasattr(st, "secrets") and "GEMINI_API_KEY" in st.secrets:
                api_key = st.secrets["GEMINI_API_KEY"]
            # Check Environment Variable (For local testing without streamlit run)
            elif "GEMINI_API_KEY" in os.environ:
                api_key = os.environ["GEMINI_API_KEY"]
            
            if not api_key:
                logger.warning("GEMINI_API_KEY not found. AI features will be disabled.")
                self.model = None
                return

            genai.configure(api_key=api_key)
            # Using flash model for speed and cost-efficiency
            self.model = genai.GenerativeModel('gemini-2.5-flash') 
            logger.info("LLMService initialized successfully with Gemini-2.5-Flash.")
            
        except Exception as e:
            logger.error(f"Failed to initialize LLMService: {e}")
            self.model = None

    def generate_response(self, prompt, context=""):
        """
        Safe wrapper for content generation.
        Returns response string or default error message.
        """
        if not self.model:
            return "Sorry, connection to the AI brain is currently unavailable (Missing API Key)."

        try:
            full_prompt = f"{context}\n\n{prompt}" if context else prompt
            response = self.model.generate_content(full_prompt)
            return response.text
        except Exception as e:
            logger.error(f"Error calling Gemini: {e}")
            return "I'm having trouble thinking right now. Please try again later."

    def interpret_certainty(self, user_input, question_context):
        """
        V2 SPECIAL FUNCTION:
        1. LLM: Classifies answer into discrete linguistic categories.
        2. Python: Maps categories to deterministic Certainty Factors (CF).
        
        Returns tuple: (ANSWER_TYPE, CF_VALUE)
        Where ANSWER_TYPE: 'YES', 'NO', 'UNSURE'
        Where CF_VALUE: 0.0 to 1.0
        """
        if not self.model:
            return "UNSURE", 0.0

        # Definition of Categories for LLM (Now in English)
        system_prompt = f"""
        Task: Analyze the user's response to a diagnostic question.
        Question Context: "{question_context}"
        User Response: "{user_input}"
        
        Instruction:
        Classify the user's response ONLY into one of the following categories:
        
        1. STRONG_YES  (Examples: "Yes definitely", "Exactly", "Very much so", "Correct")
        2. MILD_YES    (Examples: "I think so", "Maybe", "A little bit", "Looks like it")
        3. UNSURE      (Examples: "I don't know", "I'm confused", "Not sure", "Hard to tell")
        4. MILD_NO     (Examples: "I don't think so", "Probably not", "Doubt it")
        5. STRONG_NO   (Examples: "No", "Absolutely not", "Definitely not", "Wrong")
        
        Output ONLY one category word from the list above. Do not include any other text.
        """
        
        try:
            # 1. Get Linguistic Classification from LLM
            category = self.generate_response(system_prompt).strip().upper()
            
            # Cleanup punctuation just in case
            category = category.replace('.', '').replace("'", "").replace('"', '')

            # 2. Python Mapping (Deterministic Logic)
            # Format: CATEGORY -> (Logic Type, CF Value)
            cf_mapping = {
                "STRONG_YES": ("YES", 1.0),  # Very Certain
                "MILD_YES":   ("YES", 0.6),  # Somewhat Certain
                "UNSURE":     ("UNSURE", 0.0),
                "MILD_NO":    ("NO", 0.6),   # Somewhat Certain Not
                "STRONG_NO":  ("NO", 1.0)    # Very Certain Not
            }
            
            # Return mapping result, default to UNSURE if LLM hallucinates
            result = cf_mapping.get(category, ("UNSURE", 0.0))
            
            # Log for debugging (Traceability)
            logger.debug(f"Input: '{user_input}' -> Category: {category} -> Result: {result}")
            
            return result

        except Exception as e:
            logger.error(f"Failed to interpret certainty: {e}")
            return "UNSURE", 0.0
        
    def extract_weighted_preferences(self, user_input):
        """
        KHUSUS SOMMELIER: Mengubah input natural menjadi dictionary bobot.
        Contoh: "I want fruity but not bitter" -> {"fruity": 1.0, "bitter": -1.0}
        """
        system_prompt = f"""
        Task: Extract taste preferences and assign a weight (-1.0 to 1.0).
        Input: "{user_input}"
        
        Rules:
        - Strong desire ("love", "really want", "must") = 1.0
        - Moderate desire ("maybe", "a bit", "hints of") = 0.5
        - Neutral/Mentioned = 0.3
        - Avoid/Dislike ("no", "hate", "not") = -1.0
        
        Output format: JSON Dictionary ONLY. Keys must be single adjectives (lower case).
        Example: {{"fruity": 1.0, "nutty": 0.5, "bitter": -1.0}}
        """
        try:
            response = self.generate_response(system_prompt).strip()
            # Bersihkan markdown json jika ada
            response = response.replace("```json", "").replace("```", "")
            import json
            return json.loads(response)
        except Exception as e:
            logger.error(f"Weighted extraction failed: {e}")
            return {}

    def extract_numerical_value(self, user_input, parameter_name):
        """
        KHUSUS FUZZY LOGIC: Mengekstrak angka dari teks.
        Contoh: "Sekitar 88 derajat" -> 88.0
        """
        system_prompt = f"""
        Task: Extract the numerical value for '{parameter_name}' from the text.
        Input: "{user_input}"
        Output: ONLY the number (int or float). If no number found, output 'None'.
        """
        try:
            val = self.generate_response(system_prompt).strip()
            if val.lower() == 'none': return None
            return float(val)
        except:
            return None