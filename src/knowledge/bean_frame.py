from src.utils.logger import setup_logger

logger = setup_logger("BeanFrame")

class BeanFrame:
    def __init__(self, data_dict):
        """
        Inisialisasi Frame Biji Kopi.
        Menerima dictionary dari JSON.
        """
        # SLOTS (Atribut Data)
        self.id = data_dict.get('id')
        self.name = data_dict.get('name')
        self.origin = data_dict.get('origin')
        self.type = data_dict.get('type', 'Arabica')
        self.roast_level = data_dict.get('roast_level')
        self.processing = data_dict.get('processing')
        self.tasting_notes = data_dict.get('tasting_notes')
        # Pastikan tags selalu berupa list, bahkan jika kosong
        self.expert_tags = data_dict.get('expert_tags', []) 
        
        # Traceability: Log saat objek dibuat (berguna untuk debug loading)
        # logger.debug(f"BeanFrame created: {self.name}") 

    # --- ATTACHED PROCEDURES (Metode Melekat) ---

    def matches_tag(self, tag_keyword):
        """Cek apakah bean ini memiliki tag tertentu (case-insensitive)."""
        tag_keyword = tag_keyword.lower()
        return any(tag_keyword in tag.lower() for tag in self.expert_tags)

    def get_description(self):
        """Mengembalikan deskripsi lengkap untuk display ke user."""
        return f"{self.name} ({self.origin}) - {self.processing}, Roast Lv {self.roast_level}"

    def __repr__(self):
        """Representasi string untuk debugging (Traceability)."""
        return f"<BeanFrame ID={self.id} Name='{self.name}'>"
    
    def to_cbr_features(self):
        """Mengubah objek menjadi dictionary fitur untuk CBR."""
        return {
            'origin': self.origin,
            'roast_level': self.roast_level,
            'processing': self.processing,
            # Kita bisa tambah logika khusus, misal 'acidity' dari tasting notes
        }