from src.utils.logger import setup_logger

logger = setup_logger("RecipeFrame")

class RecipeFrame:
    def __init__(self, data_dict):
        """
        Inisialisasi Frame Resep.
        """
        # SLOTS
        self.recipe_id = data_dict.get('recipe_id')
        self.bean_id = data_dict.get('bean_id')
        self.brew_method = data_dict.get('brew_method')
        self.grind_size = data_dict.get('grind_size')
        self.coffee_grams = data_dict.get('coffee_grams')
        self.water_grams = data_dict.get('water_grams')
        self.water_temp_c = data_dict.get('water_temp_c')
        self.technique_notes = data_dict.get('technique_notes')

    # --- ATTACHED PROCEDURES ---

    def matches_bean(self, bean_id_to_check):
        """Cek apakah resep ini cocok untuk bean ID tertentu."""
        return self.bean_id == bean_id_to_check

    def get_ratio(self):
        """Hitung rasio air:kopi secara dinamis."""
        if self.coffee_grams and self.coffee_grams > 0:
            return round(self.water_grams / self.coffee_grams, 1)
        return 0

    def __repr__(self):
        """Untuk Debugging."""
        return f"<RecipeFrame ID={self.recipe_id} Method='{self.brew_method}' for BeanID='{self.bean_id}'>"