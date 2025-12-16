import unittest
import sys
import os
import streamlit as st

# Tambahkan root folder ke path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# --- MOCKING STREAMLIT SESSION STATE (CRITICAL FIX) ---
# Tanpa ini, Blackboard tidak bisa menyimpan data saat dijalankan via 'python' command
if not hasattr(st, 'session_state'):
    class MockState(dict):
        def __getattr__(self, key): return self.get(key)
        def __setattr__(self, key, val): self[key] = val
    st.session_state = MockState()

from src.core.blackboard import Blackboard
from src.agents.intent_agent import IntentAgent
from src.agents.doctor_agent import DoctorAgent
from src.agents.brewer_agent import BrewerAgent
from src.agents.sommelier_agent import SommelierAgent

# Disable logging for cleaner test output
import logging
logging.disable(logging.CRITICAL)

class TestEndToEndFlow(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Inisialisasi semua agen sekali saja."""
        print("\n[SETUP] Initializing Agents for E2E Testing...")
        # Kita perlu memastikan environment variable atau secrets ada untuk LLM
        # Jika tidak ada, tes yang butuh LLM mungkin akan menggunakan fallback atau mock
        cls.intent_agent = IntentAgent()
        cls.doctor_agent = DoctorAgent()
        cls.brewer_agent = BrewerAgent()
        cls.sommelier_agent = SommelierAgent()

    def setUp(self):
        """Reset memori blackboard sebelum setiap test case."""
        self.board = Blackboard()
        
        # Reset manual state untuk tes
        if hasattr(self.board, 'clear_short_term_memory'):
            self.board.clear_short_term_memory()
        
        # Inject board instance yang sama ke semua agen
        self.intent_agent.blackboard = self.board
        self.doctor_agent.blackboard = self.board
        self.brewer_agent.blackboard = self.board
        self.sommelier_agent.blackboard = self.board

    def _run_orchestrator(self):
        """Simulasi logika Orchestrator (app.py) tanpa UI."""
        # 1. Cek Locking
        doc_state = self.board.get_doctor_state()
        brewer_state = self.board.get_brewer_state()
        
        is_doctor_busy = doc_state != 'INIT' and doc_state != 'DONE'
        is_brewer_busy = brewer_state != 'INIT'
        
        # 2. Intent Agent (Hanya jika tidak dikunci)
        if not is_doctor_busy and not is_brewer_busy:
            self.intent_agent.process()
            
        # 3. Specialist Agents
        self.sommelier_agent.process()
        self.brewer_agent.process()
        self.doctor_agent.process()

    def test_scenario_doctor_full_diagnosis(self):
        """Skenario 1: Diagnosis Dokter"""
        print("\n--- TEST: Doctor Full Diagnosis Flow ---")
        
        # Step 1: Input Keluhan
        self.board.add_user_message("My coffee tastes sour")
        self._run_orchestrator()
        
        # Assert Intent
        self.assertEqual(self.board.get_intent(), 'doctor')
        
        # FIX: State setelah proses pertama adalah WAIT_BEAN_RESPONSE
        # (Karena INIT -> ASK_BEAN -> WAIT_BEAN_RESPONSE terjadi dalam satu siklus)
        self.assertEqual(self.board.get_doctor_state(), 'WAIT_BEAN_RESPONSE')
        
        # Step 2: Input Bean
        self.board.add_user_message("Ethiopia Yirgacheffe")
        self._run_orchestrator()
        self.assertEqual(self.board.get_doctor_state(), 'WAIT_METHOD_RESPONSE')
        
        # Step 3: Input Method
        self.board.add_user_message("V60")
        self._run_orchestrator()
        
        # Validasi
        bean = self.board.get_context_bean()
        recipe = self.board.get_context_recipe()
        self.assertIsNotNone(bean, "Bean context harus tersimpan")
        self.assertIsNotNone(recipe, "Recipe context harus tersimpan (V60 Ethiopia)")
        self.assertEqual(self.board.get_doctor_state(), 'WAIT_DIAGNOSIS_RESPONSE')

    def test_scenario_brewer_unknown_bean_cbr(self):
        """Skenario 2: Brewer dengan Unknown Bean (CBR Analogy)"""
        print("\n--- TEST: Brewer Unknown Bean (CBR) ---")
        
        # Step 1: Input Unknown Bean
        self.board.add_user_message("I want to brew Java Frinsa")
        self._run_orchestrator()
        
        # Assert
        self.assertEqual(self.board.get_intent(), 'master_brewer')
        self.assertEqual(self.board.get_brewer_state(), 'CBR_GATHER_ATTRS')
        
        # Step 2: Input Attributes
        self.board.add_user_message("It is light roast and natural process")
        self._run_orchestrator()
        
        # Assert Recipe Found via Analogy
        recipe = self.board.get_context_recipe()
        self.assertIsNotNone(recipe, "Harusnya menemukan resep proxy via CBR")
        self.assertEqual(self.board.get_brewer_state(), 'INIT')

    def test_scenario_sommelier_weighted_cbr(self):
        """Skenario 3: Sommelier Weighted Preferences"""
        print("\n--- TEST: Sommelier Recommendation ---")
        
        # 1. Set Input User
        self.board.add_user_message("I want something fruity but not bitter")
        
        # 2. FORCE INTENT: Kita bypass classifier untuk unit test logika Sommelier
        # Tujuannya untuk memastikan agen Sommelier bekerja jika dipanggil
        self.board.set_intent('sommelier')
        
        # 3. Jalankan Sommelier Agent secara langsung
        self.sommelier_agent.process()
        
        # 4. Validasi Bean Terpilih
        best_bean = self.board.get_context_bean()
        self.assertIsNotNone(best_bean, "Sommelier harus menetapkan best bean ke context")
        
        # Ethiopia harusnya menang karena tag Fruity
        # (Pastikan di coffee_beans.json ada Ethiopia dengan tag 'Fruity')
        print(f"Winner Bean: {best_bean.name}")
        self.assertIn("Ethiopia", best_bean.name)
        
        # 5. Cek Sinergi: Sommelier harus memicu Brewer
        self.assertEqual(self.board.get_intent(), 'master_brewer')

if __name__ == '__main__':
    unittest.main()