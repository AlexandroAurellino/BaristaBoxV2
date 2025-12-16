from src.core.blackboard import Blackboard
from src.agents.intent_agent import IntentAgent
from src.agents.doctor_agent import DoctorAgent
from src.utils.logger import setup_logger
import streamlit as st

# Mocking State
if not hasattr(st, 'session_state'):
    class MockState(dict):
        def __getattr__(self, key): return self.get(key)
        def __setattr__(self, key, val): self[key] = val
    st.session_state = MockState()

logger = setup_logger("TestDoctorFlow")

def main():
    logger.info("=== TESTING PHASE 4: DOCTOR FULL FLOW (ENGLISH & LOCKED) ===")
    
    board = Blackboard()
    intent_agent = IntentAgent()
    doctor_agent = DoctorAgent()
    
    # Skenario Percakapan (ENGLISH)
    # Kita sesuaikan jawaban agar alur logic ketemu (Positive path)
    conversation = [
        "My coffee tastes very sour and sharp.",  # Input 1: Keluhan (Trigger Doctor)
        "Ethiopia Yirgacheffe",                   # Input 2: Menjawab Bean
        "V60",                                    # Input 3: Menjawab Metode
        "No, it looks fine.",                     # Input 4: Jawaban (Gilingan kasar?) -> NO
        "Yes, it drained very fast."              # Input 5: Jawaban (Waktu cepat?) -> YES
    ]
    
    for i, user_text in enumerate(conversation):
        logger.info(f"\n--- TURN {i+1}: User says '{user_text}' ---")
        board.add_user_message(user_text)
        
        # --- ORCHESTRATOR LOGIC (SMART) ---
        
        # 1. Cek apakah Dokter sedang sibuk?
        # (Kita intip memori dokter di blackboard)
        doctor_state = board.get_doctor_state()
        is_doctor_busy = doctor_state != 'INIT' and doctor_state != 'DONE'
        
        if is_doctor_busy:
            logger.info(f"🔒 ORCHESTRATOR: Doctor is busy ({doctor_state}). Locking context.")
            # JANGAN panggil IntentAgent. Biarkan Dokter lanjut.
            # Pastikan intent tetap 'doctor' agar agen dokter mau jalan
            board.set_intent('doctor') 
            doctor_agent.process()
            
        else:
            # 2. Jika tidak sibuk, biarkan IntentAgent mendengar
            logger.info("🔓 ORCHESTRATOR: listening for new intent...")
            intent_agent.process()
            
            # Jika IntentAgent mendeteksi Doctor, baru panggil Dokter
            if board.get_intent() == 'doctor':
                doctor_agent.process()
            
        # Tampilkan respons terakhir bot
        history = board.get_chat_history()
        if history and history[-1]['role'] == 'assistant':
            # Ambil pesan terakhir
            last_msg = history[-1]['content']
            # Bersihkan newline agar log rapi
            clean_msg = last_msg.replace('\n', ' ')[:100] 
            print(f"🤖 BOT: {clean_msg}...")

if __name__ == "__main__":
    main()