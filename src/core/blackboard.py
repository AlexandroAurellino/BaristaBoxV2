import streamlit as st
from src.utils.logger import setup_logger

logger = setup_logger("Blackboard")

class Blackboard:
    """
    Pusat Memori Bersama (Shared Memory) untuk Arsitektur Blackboard.
    Bertindak sebagai Single Source of Truth bagi semua agen.
    """
    
    # Kunci-kunci standar untuk menghindari Typo
    KEY_MESSAGES = 'chat_history'
    KEY_LAST_INPUT = 'last_user_input'
    KEY_INTENT = 'current_intent'
    KEY_CONTEXT_BEAN = 'context_bean_frame'     # Akan menyimpan Objek BeanFrame
    KEY_CONTEXT_RECIPE = 'context_recipe_frame' # Akan menyimpan Objek RecipeFrame
    KEY_DIAGNOSIS_STATE = 'diagnosis_state'     # State internal dokter (misal: 'GATHERING', 'SOLVED')
    KEY_EVIDENCE = 'collected_evidence'         # Bukti gejala yang dikumpulkan

    def __init__(self):
        """Inisialisasi state jika belum ada."""
        self._init_state(self.KEY_MESSAGES, [])
        self._init_state(self.KEY_LAST_INPUT, None)
        self._init_state(self.KEY_INTENT, None)
        self._init_state(self.KEY_CONTEXT_BEAN, None)
        self._init_state(self.KEY_CONTEXT_RECIPE, None)
        self._init_state(self.KEY_DIAGNOSIS_STATE, None)
        self._init_state(self.KEY_EVIDENCE, {}) # Dictionary untuk menyimpan {gejala: CF}

    def _init_state(self, key, default_value):
        if key not in st.session_state:
            st.session_state[key] = default_value

    # --- PUBLIC API: CHAT HISTORY ---

    def add_user_message(self, message):
        st.session_state[self.KEY_MESSAGES].append({"role": "user", "content": message})
        st.session_state[self.KEY_LAST_INPUT] = message
        logger.info(f"User Input received: {message}")

    def add_bot_message(self, message):
        st.session_state[self.KEY_MESSAGES].append({"role": "assistant", "content": message})
        logger.info(f"Bot Output generated: {message[:50]}...") # Log pendek saja

    def get_chat_history(self):
        return st.session_state[self.KEY_MESSAGES]

    def get_last_user_input(self):
        return st.session_state[self.KEY_LAST_INPUT]

    # --- PUBLIC API: SHARED KNOWLEDGE (WRITE) ---

    def set_intent(self, intent):
        old_intent = st.session_state.get(self.KEY_INTENT)
        
        # Hanya lakukan sesuatu jika intent benar-benar BERUBAH
        if old_intent != intent:
            logger.debug(f"INTENT CHANGE DETECTED: '{old_intent}' -> '{intent}'")
            st.session_state[self.KEY_INTENT] = intent
            
            # --- AUTO-CLEANUP LOGIC ---
            # Jika intent berubah, reset state internal agen lain agar UI bersih
            # dan logika tidak bertabrakan.
            
            # Reset Doctor
            self.set_doctor_state('INIT')
            self.set_diagnosis_queue([]) # Kosongkan antrian diagnosa lama
            
            # Reset Brewer
            self.set_brewer_state('INIT')
            
            # Reset Evidence (Opsional: Tergantung apakah kita mau ingatan masalah hilang saat ganti topik)
            # Untuk sekarang kita KEEP evidence agar sistem terasa punya memori jangka panjang,
            # tapi kita reset pointer diagnosis saat ini.
            st.session_state['current_diagnosis_item'] = None

    def set_context_bean(self, bean_frame):
        """Menyimpan objek BeanFrame yang sedang dibicarakan."""
        st.session_state[self.KEY_CONTEXT_BEAN] = bean_frame
        logger.debug(f"CONTEXT UPDATE: Bean set to {bean_frame.name if bean_frame else 'None'}")

    def set_context_recipe(self, recipe_frame):
        st.session_state[self.KEY_CONTEXT_RECIPE] = recipe_frame
        logger.debug(f"CONTEXT UPDATE: Recipe set to {recipe_frame.recipe_id if recipe_frame else 'None'}")

    def update_evidence(self, symptom_key, certainty_factor):
        """Dokter mencatat bukti gejala baru."""
        st.session_state[self.KEY_EVIDENCE][symptom_key] = certainty_factor
        logger.debug(f"EVIDENCE ADDED: {symptom_key} (CF={certainty_factor})")

    # --- PUBLIC API: SHARED KNOWLEDGE (READ) ---

    def get_intent(self):
        return st.session_state[self.KEY_INTENT]

    def get_context_bean(self):
        return st.session_state[self.KEY_CONTEXT_BEAN]

    def get_evidence(self):
        return st.session_state[self.KEY_EVIDENCE]
    
    def get_context_recipe(self):
        return st.session_state.get(self.KEY_CONTEXT_RECIPE)

    # --- UTILITY ---
    
    def clear_short_term_memory(self):
        """
        Mereset konteks percakapan saat topik berubah drastis,
        tapi tetap menyimpan history chat.
        """
        logger.info("--- MEMORY RESET (Context Cleared) ---")
        st.session_state[self.KEY_INTENT] = None
        st.session_state[self.KEY_CONTEXT_BEAN] = None
        st.session_state[self.KEY_CONTEXT_RECIPE] = None
        st.session_state[self.KEY_EVIDENCE] = {}

    # --- DOCTOR SPECIFIC MEMORY ---

    def get_doctor_state(self):
        """Mengambil state diagnosis saat ini (misal: 'INIT', 'ASK_BEAN', 'DIAGNOSING')."""
        return st.session_state.get('doctor_internal_state', 'INIT')

    def set_doctor_state(self, state):
        st.session_state['doctor_internal_state'] = state
        logger.debug(f"DOCTOR STATE: {state}")

    def get_diagnosis_queue(self):
        """Mengambil antrian penyebab yang harus diperiksa."""
        return st.session_state.get('diagnosis_queue', [])

    def set_diagnosis_queue(self, queue):
        st.session_state['diagnosis_queue'] = queue

    def pop_diagnosis_queue(self):
        """Mengambil item pertama dari antrian dan menyimpannya sebagai 'current_check'."""
        queue = self.get_diagnosis_queue()
        if queue:
            item = queue.pop(0)
            self.set_diagnosis_queue(queue)
            st.session_state['current_diagnosis_item'] = item
            return item
        return None

    def get_current_diagnosis_item(self):
        return st.session_state.get('current_diagnosis_item')
    
    def set_current_diagnosis_item(self, item):
        st.session_state['current_diagnosis_item'] = item

    # --- BREWER SPECIFIC MEMORY ---
    
    def get_brewer_state(self):
        return st.session_state.get('brewer_state', 'INIT')

    def set_brewer_state(self, state):
        st.session_state['brewer_state'] = state
        logger.debug(f"BREWER STATE: {state}")