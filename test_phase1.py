from src.knowledge.loader import KnowledgeLoader
from src.utils.logger import setup_logger

# Setup logger utama
logger = setup_logger("MainTest")

def main():
    logger.info("=== TESTING PHASE 1: KNOWLEDGE REPRESENTATION ===")

    # Path ke dataset (sesuaikan jika perlu)
    BEANS_PATH = 'datasets/coffee_beans.json'
    RECIPES_PATH = 'datasets/brew_recipes.json'

    # 1. Inisialisasi Loader
    loader = KnowledgeLoader(BEANS_PATH, RECIPES_PATH)

    # 2. Load Data
    all_beans, all_recipes = loader.load_knowledge()

    # 3. Test Traceability & OOP Features
    logger.info("--- Testing Bean Frames ---")
    if all_beans:
        first_bean = all_beans[0]
        # Ini akan memanggil __repr__, membuktikan objek telah dibuat
        print(f"Sample Bean Object: {first_bean}") 
        # Ini memanggil attached procedure
        print(f"Description: {first_bean.get_description()}")
        
        # Test logika sederhana
        is_fruity = first_bean.matches_tag("Fruity")
        print(f"Is Fruity? {is_fruity}")

    logger.info("--- Testing Recipe Frames ---")
    if all_recipes:
        first_recipe = all_recipes[0]
        print(f"Sample Recipe Object: {first_recipe}")
        # Test attached procedure (kalkulasi rasio)
        print(f"Calculated Ratio (1:x): 1:{first_recipe.get_ratio()}")

if __name__ == "__main__":
    main()