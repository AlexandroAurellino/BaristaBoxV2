from src.core.blackboard import Blackboard
from src.core.llm_service import LLMService
from src.utils.logger import setup_logger

class BaseAgent:
    def __init__(self, name):
        self.name = name
        self.logger = setup_logger(f"Agent-{name}")
        self.blackboard = Blackboard() # Mengakses shared memory
        self.llm = LLMService()        # Mengakses kemampuan bahasa

    def process(self):
        """
        Logika utama agen. Harus di-override oleh anak kelas.
        """
        raise NotImplementedError("Setiap agen harus punya method process() sendiri.")