import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Tambahkan root folder ke path agar bisa import src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.cbr_engine import CBREngine
from src.knowledge.bean_frame import BeanFrame
from src.core.llm_service import LLMService

class TestBaristaBoxEvaluation(unittest.TestCase):

    def setUp(self):
        """Persiapan sebelum setiap test case."""
        self.cbr = CBREngine()
        # Mock LLM Service agar tidak memanggil API sungguhan (biaya & kecepatan)
        self.llm_service = LLMService() 
        self.llm_service.model = MagicMock() 

    # --- 1. EVALUASI CBR ENGINE (SIMILARITY) ---
    
    def test_cbr_exact_match(self):
        """Menguji apakah input yang persis sama menghasilkan skor 100%."""
        user_prefs = {'fruity': 1.0, 'bright': 1.0}
        bean_tags = ['Fruity', 'Bright', 'Floral'] # Exact match subset
        
        score = self.cbr.calculate_weighted_tag_similarity(user_prefs, bean_tags)
        
        # Total bobot = 2.0. Match = 2.0. Hasil harus 100.0
        self.assertEqual(score, 100.0, "CBR Exact Match harus bernilai 100.0")

    def test_cbr_partial_match(self):
        """Menguji apakah input parsial menghasilkan skor proporsional."""
        user_prefs = {'fruity': 1.0, 'nutty': 1.0} # Total bobot 2.0
        bean_tags = ['Fruity', 'Bright'] # Cuma ada Fruity
        
        score = self.cbr.calculate_weighted_tag_similarity(user_prefs, bean_tags)
        
        # Match 1.0 dari 2.0. Hasil harus 50.0
        self.assertEqual(score, 50.0, "CBR Partial Match harus bernilai 50.0")

    def test_cbr_no_match(self):
        """Menguji input yang tidak cocok sama sekali."""
        user_prefs = {'spicy': 1.0}
        bean_tags = ['Fruity', 'Sweet']
        
        score = self.cbr.calculate_weighted_tag_similarity(user_prefs, bean_tags)
        self.assertEqual(score, 0.0, "CBR No Match harus bernilai 0.0")

    # --- 2. EVALUASI FUZZY LOGIC (TEMPERATURE) ---

    def test_fuzzy_low_temp(self):
        """Menguji logika fuzzy untuk suhu rendah (Under-extraction risk)."""
        # Suhu 85 (Jauh di bawah 90) -> LOW harus 1.0
        result = self.cbr.fuzzy_check_temperature(85)
        self.assertEqual(result['LOW'], 1.0)
        self.assertEqual(result['IDEAL'], 0.0)

    def test_fuzzy_transition_temp(self):
        """Menguji logika fuzzy di area transisi (91 derajat)."""
        # Suhu 91 (Antara 90 dan 92). 
        # LOW = (92-91)/2 = 0.5
        # IDEAL = (91-90)/2 = 0.5
        result = self.cbr.fuzzy_check_temperature(91)
        self.assertAlmostEqual(result['LOW'], 0.5)
        self.assertAlmostEqual(result['IDEAL'], 0.5)

    def test_fuzzy_ideal_temp(self):
        """Menguji logika fuzzy untuk suhu ideal."""
        # Suhu 93 (Perfect) -> IDEAL harus 1.0
        result = self.cbr.fuzzy_check_temperature(93)
        self.assertEqual(result['IDEAL'], 1.0)
        self.assertEqual(result['LOW'], 0.0)
        self.assertEqual(result['HIGH'], 0.0)

    # --- 3. EVALUASI CERTAINTY FACTOR MAPPING ---

    def test_cf_mapping_logic(self):
        """
        Menguji apakah pemetaan kategori bahasa ke angka CF konsisten.
        Kita mock respons string dari LLM, lalu cek logika Python-nya.
        """
        # Mocking output LLM menjadi 'STRONG_YES'
        self.llm_service.generate_response = MagicMock(return_value="STRONG_YES")
        
        # Test function
        cat, cf = self.llm_service.interpret_certainty("Yes absolutely", "Context")
        
        self.assertEqual(cat, "YES")
        self.assertEqual(cf, 1.0, "STRONG_YES harus dipetakan ke CF 1.0")

    def test_cf_mapping_unsure(self):
        # Mocking output LLM menjadi 'UNSURE'
        self.llm_service.generate_response = MagicMock(return_value="UNSURE")
        
        cat, cf = self.llm_service.interpret_certainty("I dont know", "Context")
        
        self.assertEqual(cat, "UNSURE")
        self.assertEqual(cf, 0.0, "UNSURE harus dipetakan ke CF 0.0")

if __name__ == '__main__':
    unittest.main()