from src.agents.base_agent import BaseAgent
from src.knowledge.loader import KnowledgeLoader
from src.core.cbr_engine import CBREngine
import json

class SommelierAgent(BaseAgent):
    def __init__(self):
        super().__init__("Sommelier")
        self.loader = KnowledgeLoader('datasets/coffee_beans.json', 'datasets/brew_recipes.json')
        self.beans, _ = self.loader.load_knowledge()
        self.cbr = CBREngine()

    def process(self):
        if self.blackboard.get_intent() != 'sommelier': return

        user_input = self.blackboard.get_last_user_input()
        self.logger.info("Sommelier performing Weighted CBR Analysis...")

        # 1. Ekstraksi Bobot (LLM)
        user_prefs = self.llm.extract_weighted_preferences(user_input)
        
        if not user_prefs:
            self.blackboard.add_bot_message("Could you describe the flavor you want? (e.g., 'Fruity and sweet, not bitter')")
            return

        # 2. Kalkulasi CBR (Python)
        scored_beans = []
        for bean in self.beans:
            score = self.cbr.calculate_weighted_tag_similarity(user_prefs, bean.expert_tags)
            scored_beans.append((score, bean))

        # Sort
        scored_beans.sort(key=lambda x: x[0], reverse=True)
        
        # 3. Tampilkan "Invisible Math" (Transparansi untuk Dosen)
        top_beans = scored_beans[:3]
        
        # Debugging visual untuk user
        debug_msg = "🧮 **CBR Calculation Trace:**\n"
        debug_msg += f"**User Constraints (Weights):** `{json.dumps(user_prefs)}`\n\n"
        debug_msg += "**Scoring Results:**\n"
        
        for score, bean in top_beans:
            # Cari tag yang cocok untuk highlight
            matches = [t for t in bean.expert_tags if any(req in t.lower() for req in user_prefs)]
            debug_msg += f"- **{bean.name}**: {score:.1f}% Match (Matches: {', '.join(matches)})\n"
            
        self.blackboard.add_bot_message(debug_msg)

        # 4. Rekomendasi & Sinergi
        winner = top_beans[0][1]
        self.blackboard.set_context_bean(winner) # Set Context untuk Brewer
        
        narrative = self.llm.generate_response(
            prompt=f"Recommend {winner.name} based on user prefs {user_prefs}. Keep it professional.",
            context="Sommelier"
        )
        self.blackboard.add_bot_message(f"🏆 **Top Recommendation:**\n\n{narrative}")
        
        # Trigger Brewer untuk langsung kasih resep (Sinergi)
        self.blackboard.add_bot_message("*(Passing context to Master Brewer for recipe...)*")
        self.blackboard.set_intent('master_brewer')