from src.core.blackboard import Blackboard
from src.agents.intent_agent import IntentAgent
from src.utils.logger import setup_logger
import streamlit as st

# Mocking session state lagi untuk terminal
if not hasattr(st, 'session_state'):
    class MockState(dict):
        def __getattr__(self, key): return self.get(key)
        def __setattr__(self, key, val): self[key] = val
    st.session_state = MockState()

logger = setup_logger("TestPhase4")

def main():
    logger.info("=== TESTING PHASE 4: INTENT AGENT ===")
    
    # 1. Setup Environment
    board = Blackboard()
    agent = IntentAgent()
    
    # 2. Simulasi User Input 1
    input_text = "My coffee tastes sour and acidic."
    logger.info(f"--- Simulation 1: '{input_text}' ---")
    
    board.add_user_message(input_text)
    agent.process() # Agen bekerja
    
    print(f"Result Intent: {board.get_intent()}")
    print(f"Result Evidence: {board.get_evidence()}") # Harusnya ada 'problem_sour'

    # 3. Simulasi User Input 2
    input_text = "Recommend me a bold coffee."
    logger.info(f"--- Simulation 2: '{input_text}' ---")
    
    board.add_user_message(input_text)
    agent.process()
    
    print(f"Result Intent: {board.get_intent()}") # Harusnya 'sommelier'

if __name__ == "__main__":
    main()