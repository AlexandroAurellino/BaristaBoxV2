import json
import os
from src.utils.logger import setup_logger
from src.knowledge.bean_frame import BeanFrame
from src.knowledge.recipe_frame import RecipeFrame

logger = setup_logger("KnowledgeLoader")

class KnowledgeLoader:
    def __init__(self, beans_path, recipes_path):
        self.beans_path = beans_path
        self.recipes_path = recipes_path
        self.beans = []   # Akan berisi list of BeanFrame objects
        self.recipes = [] # Akan berisi list of RecipeFrame objects

    def load_knowledge(self):
        """
        Memuat semua data JSON dan mengonversinya menjadi Objek Frame.
        """
        logger.info("Mulai memuat basis pengetahuan...")
        
        self.beans = self._load_beans()
        self.recipes = self._load_recipes()
        
        logger.info(f"Selesai. Memuat {len(self.beans)} Beans dan {len(self.recipes)} Resep.")
        return self.beans, self.recipes

    def _load_beans(self):
        if not os.path.exists(self.beans_path):
            logger.error(f"File Beans tidak ditemukan: {self.beans_path}")
            return []
        
        try:
            with open(self.beans_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Konversi JSON dict menjadi BeanFrame object
                frames = [BeanFrame(item) for item in data]
                logger.info(f"Berhasil memuat {len(frames)} BeanFrames.")
                return frames
        except Exception as e:
            logger.error(f"Gagal memuat Beans: {e}")
            return []

    def _load_recipes(self):
        if not os.path.exists(self.recipes_path):
            logger.error(f"File Recipes tidak ditemukan: {self.recipes_path}")
            return []
        
        try:
            with open(self.recipes_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Konversi JSON dict menjadi RecipeFrame object
                frames = [RecipeFrame(item) for item in data]
                logger.info(f"Berhasil memuat {len(frames)} RecipeFrames.")
                return frames
        except Exception as e:
            logger.error(f"Gagal memuat Recipes: {e}")
            return []