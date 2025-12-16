# test_phase2.py
import streamlit as st
from src.core.llm_service import LLMService
from src.core.blackboard import Blackboard
from src.utils.logger import setup_logger

logger = setup_logger("TestPhase2")

def main():
    logger.info("=== TESTING PHASE 2: CORE SERVICES ===")

    # 1. Mocking Streamlit Session State (Agar jalan di terminal tanpa 'streamlit run')
    # Ini trik agar kita bisa debug logic tanpa UI
    if not hasattr(st, 'session_state'):
        class MockState(dict):
            def __getattr__(self, key): return self.get(key)
            def __setattr__(self, key, val): self[key] = val
        st.session_state = MockState()

    # 2. Test LLM Service
    logger.info("--- Testing LLM Service (Connection & CF) ---")
    llm = LLMService()
    
    if llm.model:
        # Skenario 1: Jawaban Yakin
        input_text = "Iya, kerasa banget kasarnya."
        context = "Apakah gilingan kopi terasa kasar?"
        tipe, cf = llm.interpret_certainty(input_text, context)
        print(f"Q: {context}\nA: {input_text}\nResult: Tipe={tipe}, CF={cf}")
        
        # Skenario 2: Jawaban Ragu
        input_text = "Nggak tau deh, mungkin?"
        tipe, cf = llm.interpret_certainty(input_text, context)
        print(f"Q: {context}\nA: {input_text}\nResult: Tipe={tipe}, CF={cf}")
    else:
        logger.error("Skip test LLM karena API Key tidak terdeteksi/gagal.")

    # 3. Test Blackboard
    logger.info("--- Testing Blackboard (Memory) ---")
    board = Blackboard()
    
    # Simulasi interaksi
    board.add_user_message("Kopi saya pahit.")
    board.set_intent("DOCTOR")
    board.update_evidence("taste_bitter", 1.0)
    
    # Cek apakah data tersimpan
    print(f"Current Intent: {board.get_intent()}")
    print(f"Evidence: {board.get_evidence()}")
    print(f"History Count: {len(board.get_chat_history())}")

if __name__ == "__main__":
    main()