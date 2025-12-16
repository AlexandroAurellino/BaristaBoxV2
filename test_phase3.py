from src.core.cbr_engine import CBREngine
from src.utils.logger import setup_logger

logger = setup_logger("TestPhase3")

def main():
    logger.info("=== TESTING PHASE 3: CBR ENGINE ===")
    
    engine = CBREngine()
    
    # 1. Test Similarity Calculation
    logger.info("--- 1. Testing Similarity ---")
    
    # Kasus Baru (Query)
    query = {
        'origin': 'Ethiopia',
        'roast_level': 1, # Light
        'processing': 'Washed'
    }
    
    # Kasus Lama A (Mirip)
    case_a = {
        'id': 'bean_01',
        'origin': 'Ethiopia',
        'roast_level': 2, # Sedikit beda
        'processing': 'Washed'
    }
    
    # Kasus Lama B (Beda Jauh)
    case_b = {
        'id': 'bean_02',
        'origin': 'Indonesia',
        'roast_level': 5, # Dark
        'processing': 'Wet-Hulled'
    }
    
    weights = {'origin': 0.4, 'roast_level': 0.3, 'processing': 0.3}
    
    score_a = engine.calculate_similarity(query, case_a, weights)
    score_b = engine.calculate_similarity(query, case_b, weights)
    
    print(f"Similarity Query vs Case A (Ethiopia): {score_a:.4f}")
    print(f"Similarity Query vs Case B (Indonesia): {score_b:.4f}")
    
    # 2. Test Fuzzy Logic
    logger.info("--- 2. Testing Fuzzy Logic (Suhu) ---")
    temps = [80, 88, 96]
    for t in temps:
        print(f"Suhu {t}C -> {engine.fuzzy_match_temperature(t)}")

if __name__ == "__main__":
    main()