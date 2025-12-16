import math
from src.utils.logger import setup_logger

logger = setup_logger("CBREngine")

class CBREngine:
    """
    Mesin untuk menangani logika Case-Based Reasoning dan Fuzzy Matching.
    """

    @staticmethod
    def calculate_similarity(case_a_features, case_b_features, weights):
        """
        Menghitung skor kemiripan antara dua kasus (case A dan case B).
        
        Args:
            case_a_features (dict): Fitur dari kasus baru (Query).
            case_b_features (dict): Fitur dari kasus lama (Database).
            weights (dict): Bobot kepentingan untuk setiap fitur.
            
        Returns:
            float: Skor kemiripan (0.0 sampai 1.0).
        """
        total_score = 0.0
        total_weight = 0.0
        
        for feature, weight in weights.items():
            val_a = case_a_features.get(feature)
            val_b = case_b_features.get(feature)
            
            # Lewati jika salah satu fitur tidak ada (tidak bisa dibandingkan)
            if val_a is None or val_b is None:
                continue
                
            similarity = 0.0
            
            # Logika Pencocokan Berdasarkan Tipe Data
            if isinstance(val_a, str) and isinstance(val_b, str):
                # String matching (Exact match = 1.0, else 0.0)
                # Di masa depan bisa diganti Levenshtein distance untuk fuzzy string
                similarity = 1.0 if val_a.lower() == val_b.lower() else 0.0
                
            elif isinstance(val_a, (int, float)) and isinstance(val_b, (int, float)):
                # Numerik: 1.0 jika sama, berkurang seiring jarak
                # Rumus sederhana: 1 / (1 + selisih)
                diff = abs(val_a - val_b)
                similarity = 1.0 / (1.0 + diff)
                
            elif isinstance(val_a, bool) and isinstance(val_b, bool):
                similarity = 1.0 if val_a == val_b else 0.0
                
            # Akumulasi Skor
            total_score += similarity * weight
            total_weight += weight
            
        if total_weight == 0:
            return 0.0
            
        return total_score / total_weight
    
    def find_similar_bean(self, target_features, all_bean_frames):
        """
        Mencari BeanFrame yang paling mirip dengan fitur target.
        target_features: dict {'origin': '...', 'roast_level': 1, 'processing': '...'}
        """
        best_match = None
        highest_score = -1
        
        # Bobot kemiripan
        weights = {
            'origin': 0.3,      # Asal negara cukup penting
            'roast_level': 0.4, # Tingkat sangrai SANGAT penting untuk resep
            'processing': 0.3   # Proses juga penting
        }
        
        for bean in all_bean_frames:
            # Kita bandingkan target dengan data bean ini
            bean_features = {
                'origin': bean.origin,
                'roast_level': bean.roast_level,
                'processing': bean.processing
            }
            
            # Khusus Origin, kita bisa bikin fuzzy (Benua sama = skor parsial)
            # Tapi untuk sekarang string match dulu via calculate_similarity dasar
            
            score = self.calculate_similarity(target_features, bean_features, weights)
            
            if score > highest_score:
                highest_score = score
                best_match = bean
                
        return best_match, highest_score

    @staticmethod
    def calculate_weighted_tag_similarity(user_preferences, bean_tags):
        """Implementasi CBR Score dengan Bobot."""
        if not user_preferences: return 0.0
        
        total_score = 0.0
        # Kita normalisasi pembagi berdasarkan total bobot positif yang diharapkan
        max_possible_score = sum(abs(v) for v in user_preferences.values())
        if max_possible_score == 0: return 0.0

        bean_tags_lower = [t.lower() for t in bean_tags]

        for pref_tag, weight in user_preferences.items():
            # Cek substring match
            matched = any(pref_tag in tag for tag in bean_tags_lower)
            
            if matched:
                # Jika tag ada, tambahkan bobot (bisa positif atau negatif)
                total_score += weight
            else:
                # Jika tag tidak ada:
                # Jika user MINTA (positif), tapi gak ada -> skor tidak nambah (0)
                # Jika user TOLAK (negatif), dan emang gak ada -> skor nambah (karena keinginan terpenuhi)
                if weight < 0:
                    total_score += abs(weight) # Bonus karena berhasil menghindari hal yg dibenci

        # Normalisasi ke 0-100
        return (total_score / max_possible_score) * 100

    @staticmethod
    def fuzzy_check_temperature(temp_c):
        """
        Logika Fuzzy untuk menilai suhu seduh kopi.
        Set: LOW (Under-extraction risk), IDEAL, HIGH (Over-extraction risk)
        """
        results = {}
        
        # 1. Fuzzy Set: LOW (< 90 is 1.0, 90-92 turun ke 0)
        if temp_c < 90:
            results['LOW'] = 1.0
        elif 90 <= temp_c < 92:
            results['LOW'] = (92 - temp_c) / 2.0
        else:
            results['LOW'] = 0.0
            
        # 2. Fuzzy Set: IDEAL (naik 90-92, rata 92-94, turun 94-96)
        if temp_c < 90 or temp_c > 96:
            results['IDEAL'] = 0.0
        elif 90 <= temp_c < 92:
            results['IDEAL'] = (temp_c - 90) / 2.0
        elif 92 <= temp_c <= 94:
            results['IDEAL'] = 1.0
        elif 94 < temp_c <= 96:
            results['IDEAL'] = (96 - temp_c) / 2.0
            
        # 3. Fuzzy Set: HIGH (> 96 is 1.0, 94-96 naik ke 1)
        if temp_c > 96:
            results['HIGH'] = 1.0
        elif 94 < temp_c <= 96:
            results['HIGH'] = (temp_c - 94) / 2.0
        else:
            results['HIGH'] = 0.0
            
        return results

    def find_nearest_neighbors(self, query_case, case_base, weights, top_k=3):
        """
        Mencari K kasus teratas yang paling mirip dari case_base.
        """
        results = []
        
        for case in case_base:
            # Asumsi 'case' adalah dictionary atau objek yang punya atribut mirip
            # Kita perlu standarisasi ini nanti. Untuk sekarang asumsi dict.
            case_features = case if isinstance(case, dict) else case.__dict__
            
            score = self.calculate_similarity(query_case, case_features, weights)
            results.append((score, case))
            
        # Urutkan dari skor tertinggi
        results.sort(key=lambda x: x[0], reverse=True)
        
        return results[:top_k]
    
    def calculate_weighted_tag_similarity(self, user_preferences, bean_tags):
        """
        Menghitung skor kemiripan berdasarkan bobot preferensi user (CF).
        
        Args:
            user_preferences: dict { 'tag_name': cf_value } 
                              Contoh: {'fruity': 1.0, 'nutty': 0.6}
            bean_tags: list ['Fruity', 'Floral', ...]
            
        Returns:
            float: Skor total
        """
        total_score = 0.0
        total_possible_score = sum(user_preferences.values())
        
        if total_possible_score == 0: return 0.0

        bean_tags_lower = [t.lower() for t in bean_tags]

        for desired_tag, cf_weight in user_preferences.items():
            # Fuzzy String Matching (Sederhana: substring)
            match = any(desired_tag in tag for tag in bean_tags_lower)
            
            if match:
                # Jika cocok, tambahkan skor sebesar keyakinan user
                total_score += 1.0 * cf_weight
            else:
                # Jika tidak cocok, penalti? Atau 0 saja.
                pass
        
        # Normalisasi skor 0-100
        return (total_score / total_possible_score) * 100