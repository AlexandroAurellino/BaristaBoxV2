from src.agents.base_agent import BaseAgent
from src.knowledge.loader import KnowledgeLoader
from src.core.cbr_engine import CBREngine
import random

class BrewerAgent(BaseAgent):
    def __init__(self):
        super().__init__("Brewer")
        # Load Knowledge Base
        self.loader = KnowledgeLoader('datasets/coffee_beans.json', 'datasets/brew_recipes.json')
        self.beans, self.recipes = self.loader.load_knowledge()
        
        # Inisialisasi mesin CBR untuk pencarian kemiripan
        self.cbr = CBREngine()

    def process(self):
        # 1. Cek State & Intent
        state = self.blackboard.get_brewer_state()
        
        # Jika state INIT, hanya jalan jika Intent == master_brewer
        # Jika state BUKAN INIT (sedang menunggu jawaban), jalan terus apapun intent-nya (Locking)
        if state == 'INIT':
            if self.blackboard.get_intent() != 'master_brewer':
                return

        user_input = self.blackboard.get_last_user_input().lower()
        self.logger.info(f"Brewer processing in state: {state}")

        # --- STATE MACHINE ---

        if state == 'INIT':
            # Tahap 1: Identifikasi Bean dari Input
            found_bean = None
            
            # Cek string match di input user
            for bean in self.beans:
                if bean.name.lower() in user_input:
                    found_bean = bean
                    break
            
            # Jika tidak ada di input, cek apakah sudah ada context sebelumnya
            if not found_bean:
                found_bean = self.blackboard.get_context_bean()

            if found_bean:
                # KASUS A: Bean Dikenal (Ada di Database)
                self.blackboard.set_context_bean(found_bean)
                
                # Cari resep yang tersedia untuk bean ini
                available_recipes = [r for r in self.recipes if r.bean_id == found_bean.id]
                
                if not available_recipes:
                    self.blackboard.add_bot_message(f"Database confirmed: I know **{found_bean.name}**, but I have 0 recipes recorded for it yet.")
                    return

                # Cek apakah user sudah menyebutkan metode?
                found_method = self._extract_method(user_input)
                
                if found_method:
                    # User minta metode spesifik (misal: "V60 recipe for Ethiopia")
                    target_recipe = next((r for r in available_recipes if r.brew_method.lower() == found_method), None)
                    if target_recipe:
                        self._present_recipe(target_recipe, found_bean)
                    else:
                        available_methods = ", ".join([r.brew_method for r in available_recipes])
                        self.blackboard.add_bot_message(
                            f"**{found_bean.name}** found. No recipe for {found_method.title()}.\n"
                            f"Available recipes: **{available_methods}**. Pick one?"
                        )
                        self.blackboard.set_brewer_state('WAIT_METHOD_SELECTION')
                else:
                    # User TIDAK minta metode spesifik.
                    # LOGIKA PROAKTIF:
                    available_methods = [r.brew_method for r in available_recipes]
                    
                    if len(available_methods) == 1:
                        # Cuma ada 1 resep? Langsung kasih! Jangan banyak tanya.
                        self.blackboard.add_bot_message(f"Found **{found_bean.name}**. Only one expert recipe available. Here it is:")
                        self._present_recipe(available_recipes[0], found_bean)
                    else:
                        # Ada banyak? Tawarkan.
                        options_str = ", ".join(available_methods)
                        self.blackboard.add_bot_message(
                            f"**{found_bean.name}** identified. I have recipes for: **{options_str}**.\n\n"
                            "Which one do you want? (Or say 'Recommend' if unsure)."
                        )
                        self.blackboard.set_brewer_state('WAIT_METHOD_SELECTION')

            else:
                # KASUS B: Bean Tidak Dikenal -> Masuk ke Mode CBR
                self.blackboard.add_bot_message(
                    "Unknown coffee bean detected. Initializing **Case-Based Reasoning** protocol.\n\n"
                    "To generate an adapted recipe, I need attributes:\n"
                    "**What is the Roast Level (Light/Medium/Dark) and Process (Washed/Natural)?**"
                )
                self.blackboard.set_brewer_state('CBR_GATHER_ATTRS')

        elif state == 'WAIT_METHOD_SELECTION':
            # Menunggu user memilih metode dari daftar yang kita tawarkan
            found_bean = self.blackboard.get_context_bean()
            available_recipes = [r for r in self.recipes if r.bean_id == found_bean.id]
            
            found_method = self._extract_method(user_input)
            
            if found_method:
                target_recipe = next((r for r in available_recipes if r.brew_method.lower() == found_method), None)
                if target_recipe:
                    self._present_recipe(target_recipe, found_bean)
                    self.blackboard.set_brewer_state('INIT')
                    return

            # HANDLING "I DON'T KNOW" (Smart Fallback)
            # Cek certainty/keyword
            if "know" in user_input.lower() or "recommend" in user_input.lower() or "sure" in user_input.lower():
                # Pilihkan metode terbaik (Prioritas: V60 -> French Press)
                priority_order = ['v60', 'french press', 'aeropress', 'chemex']
                chosen_recipe = None
                
                for method in priority_order:
                    chosen_recipe = next((r for r in available_recipes if r.brew_method.lower() == method), None)
                    if chosen_recipe: break
                
                if not chosen_recipe:
                    chosen_recipe = available_recipes[0] # Fallback terakhir

                self.blackboard.add_bot_message(f"Auto-selection: **{chosen_recipe.brew_method}** (Best match for this bean).")
                self._present_recipe(chosen_recipe, found_bean)
                self.blackboard.set_brewer_state('INIT')
            else:
                self.blackboard.add_bot_message("Invalid selection. Please choose from the available list or ask for a recommendation.")

        elif state == 'CBR_GATHER_ATTRS':
            # Logika CBR: Mencari Bean Mirip (Nearest Neighbor)
            
            # 1. Parsing Heuristik Sederhana (Mengubah teks user jadi fitur)
            roast_level = 3 # Default Medium
            if "light" in user_input: roast_level = 1
            if "dark" in user_input: roast_level = 5
            
            process = "Washed" # Default
            if "natural" in user_input: process = "Natural"
            if "honey" in user_input: process = "Honey"
            if "wet" in user_input: process = "Wet-Hulled"

            # 2. Cari Nearest Neighbor
            target_features = {
                'origin': 'Unknown', 
                'roast_level': roast_level,
                'processing': process
            }
            
            similar_bean, score = self.cbr.find_similar_bean(target_features, self.beans)
            
            if similar_bean:
                # 3. Adaptasi Resep (Reuse)
                # Cari resep dari bean mirip itu
                proxy_recipes = [r for r in self.recipes if r.bean_id == similar_bean.id]
                
                if proxy_recipes:
                    chosen_recipe = proxy_recipes[0] # Ambil yang pertama
                    
                    self.blackboard.add_bot_message(
                        f"**CBR Analysis Result:**\n"
                        f"- Input Profile: Roast Lv {roast_level}, {process}\n"
                        f"- Nearest Neighbor Found: **{similar_bean.name}** (Similarity: {int(score*100)}%)\n"
                        f"- Adaptation: Using recipe for {similar_bean.name} as reference.\n"
                    )
                    self._present_recipe(chosen_recipe, similar_bean)
                else:
                    self.blackboard.add_bot_message("Found a similar bean profile, but it has no recipes stored.")
            else:
                self.blackboard.add_bot_message("Database insufficient. No similar beans found for analogy.")
            
            self.blackboard.set_brewer_state('INIT')

    def _extract_method(self, text):
        """Helper sederhana untuk ekstrak metode."""
        known_methods = ["v60", "aeropress", "french press", "chemex", "kalita"]
        for method in known_methods:
            if method in text:
                return method
        return None

    def _present_recipe(self, recipe, bean):
        """
        Menampilkan resep dengan format STRICT & TECHNICAL (No Yapping).
        """
        self.blackboard.set_context_recipe(recipe)
        
        # Susun data mentah
        core_data = (
            f"TARGET BEAN: {bean.name}\n"
            f"METHOD: {recipe.brew_method}\n"
            f"RATIO: {recipe.coffee_grams}g Coffee to {recipe.water_grams}ml Water\n"
            f"TEMP: {recipe.water_temp_c}°C\n"
            f"GRIND: {recipe.grind_size}\n"
            f"TECHNIQUE: {recipe.technique_notes}\n"
        )

        # Prompt Anti-Hallucination & Anti-Fluff
        prompt = f"""
        TASK: Convert the RAW DATA below into a Technical Brewing Standard Operating Procedure (SOP).
        
        CONSTRAINTS:
        1. NO conversational filler (e.g., "Here is your recipe", "Enjoy").
        2. NO introductory or concluding paragraphs. Start directly with the parameters.
        3. Use a Table or Bullet points for parameters.
        4. Steps must be numbered, imperative, and extremely concise (under 10 words per step if possible).
        5. DO NOT invent information not present in the RAW DATA.
        
        RAW DATA:
        {core_data}
        """
        
        response = self.llm.generate_response(prompt, context="You are a Technical Manual Generator.")
        self.blackboard.add_bot_message(response)