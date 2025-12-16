from src.agents.base_agent import BaseAgent
from src.knowledge.loader import KnowledgeLoader
from src.core.cbr_engine import CBREngine
import json
import re

class DoctorAgent(BaseAgent):
    def __init__(self):
        super().__init__("Doctor")
        
        # Load Knowledge Base
        self.loader = KnowledgeLoader('datasets/coffee_beans.json', 'datasets/brew_recipes.json')
        self.beans, self.recipes = self.loader.load_knowledge()
        
        with open('datasets/troubleshooting_knowledge_base.json', 'r') as f:
            self.kb_rules = json.load(f)

    def _find_ideal_recipe(self, bean_name, brew_method):
        """Helper: Mencari resep ideal berdasarkan input user."""
        if not bean_name or not brew_method:
            return None
            
        # Cari Bean ID
        found_bean_id = None
        for bean in self.beans:
            if bean.name.lower() in bean_name.lower():
                found_bean_id = bean.id
                # Update Context Bean di Blackboard
                self.blackboard.set_context_bean(bean)
                break
        
        if not found_bean_id:
            return None

        # Cari Resep
        for recipe in self.recipes:
            if recipe.bean_id == found_bean_id and recipe.brew_method.lower() in brew_method.lower():
                # Update Context Recipe di Blackboard
                self.blackboard.set_context_recipe(recipe)
                return recipe
        return None

    def process(self):
        current_intent = self.blackboard.get_intent()
        if current_intent != 'doctor':
            return 

        state = self.blackboard.get_doctor_state()
        user_input = self.blackboard.get_last_user_input()
        
        self.logger.info(f"Processing in State: {state}")

        # --- STATE MACHINE ---

        if state == 'INIT':
            evidence = self.blackboard.get_evidence()
            initial_problem = evidence.get('initial_problem_classification')
            
            if not initial_problem:
                self.blackboard.add_bot_message("I detected a brewing issue, but could you describe the taste in more detail?")
                return

            if initial_problem in self.kb_rules:
                causes = self.kb_rules[initial_problem]['causes']
                queue = list(causes.items()) 
                self.blackboard.set_diagnosis_queue(queue)
                
                # Simpan problem key untuk dipakai di sintesis
                self.blackboard.update_evidence('current_problem_key', initial_problem)
                
                self.blackboard.set_doctor_state('ASK_BEAN')
                self.process() 
            else:
                self.blackboard.add_bot_message("I'm sorry, I don't have specific data for this problem yet.")

        elif state == 'ASK_BEAN':
            self.blackboard.add_bot_message("To diagnose this accurately, I need context. Which **coffee bean** are you using?")
            self.blackboard.set_doctor_state('WAIT_BEAN_RESPONSE')

        elif state == 'WAIT_BEAN_RESPONSE':
            self.blackboard.update_evidence('user_bean_name', user_input)
            self.blackboard.add_bot_message(f"Okay, {user_input}. What **brew method** are you using? (If you aren't sure, just say 'I don't know').")
            self.blackboard.set_doctor_state('WAIT_METHOD_RESPONSE')

        elif state == 'WAIT_METHOD_RESPONSE':
            # Handle "I don't know"
            tipe_jawaban, _ = self.llm.interpret_certainty(user_input, "User is stating their brew method")
            
            final_method = user_input
            if tipe_jawaban == 'UNSURE' or "know" in user_input.lower():
                final_method = "V60 (Assumed)"
                self.blackboard.add_bot_message("No problem! Let's assume you are doing a standard **Pour Over (like V60)** for now, as that's very common.")
            
            self.blackboard.update_evidence('user_brew_method', final_method)
            
            # Cari Resep Ideal & Update Context di Blackboard
            evidence = self.blackboard.get_evidence()
            bean_name = evidence.get('user_bean_name')
            self._find_ideal_recipe(bean_name, final_method)
            
            self.blackboard.set_doctor_state('DIAGNOSING')
            self.process() 

        elif state == 'DIAGNOSING':
            # Reset current item dari iterasi sebelumnya
            self.blackboard.set_current_diagnosis_item(None)
            
            # Ambil item berikutnya dari antrian
            current_item = self.blackboard.pop_diagnosis_queue()
            
            # JIKA ANTRIAN HABIS -> Masuk tahap KESIMPULAN
            if not current_item:
                self.blackboard.set_doctor_state('SYNTHESIZE_RESULTS')
                self.process() 
                return

            # JIKA ADA PERTANYAAN -> Tanyakan
            cause_key, cause_data = current_item
            question = cause_data['question']

            # Logika Pertanyaan Kontekstual Berbasis Resep
            ideal_recipe = self.blackboard.get_context_recipe()

            if ideal_recipe:
                if cause_key == 'grind_coarse' or cause_key == 'grind_fine':
                    question = f"For this bean, the ideal grind is **{ideal_recipe.grind_size}**. \n\nDoes your grind look **significantly coarser/chunkier** than that?"
                elif 'brew_time' in cause_key:
                    time_target = "2:30 - 3:00"
                    match = re.search(r'(\d+:\d+)', ideal_recipe.technique_notes)
                    if match:
                        time_target = match.group(1)
                    
                    if 'short' in cause_key:
                        question = f"The target brew time should be around **{time_target}**. \n\nDid your water drain **much faster** than that?"
                    else:
                        question = f"The target brew time should be around **{time_target}**. \n\nDid your brew take **much longer** than that?"
                elif 'water_temp' in cause_key:
                    temp_target = ideal_recipe.water_temp_c
                    if 'low' in cause_key:
                        question = f"Recommended temp is **{temp_target}°C**. \n\nDo you think your water might have been **too cool** (e.g. waited too long after boiling)?"
                    else:
                        question = f"Recommended temp is **{temp_target}°C**. \n\nDid you use boiling water straight away?"

            self.blackboard.add_bot_message(question)
            self.blackboard.set_doctor_state('WAIT_DIAGNOSIS_RESPONSE')

        elif state == 'WAIT_DIAGNOSIS_RESPONSE':
            current_item = self.blackboard.get_current_diagnosis_item()
            cause_key, cause_data = current_item
            question_context = cause_data['question']

            # --- 1. FUZZY LOGIC CHECK (Cek Angka) ---
            tipe_jawaban = None
            cf = 0.0
            
            # Hanya jalankan Fuzzy jika pertanyaan tentang suhu
            if 'water_temp' in cause_key:
                user_temp = self.llm.extract_numerical_value(user_input, "temperature")
                
                if user_temp:
                    # Jalankan Kalkulasi Fuzzy
                    fuzzy_result = CBREngine.fuzzy_check_temperature(user_temp)
                    
                    # Tampilkan kalkulasi "di balik layar" ke Blackboard
                    msg = f"🌡️ **Fuzzy Logic Analysis (Temp: {user_temp}°C):**\n"
                    msg += f"- Low/Cold Membership: {fuzzy_result['LOW']:.2f}\n"
                    msg += f"- Ideal Membership: {fuzzy_result['IDEAL']:.2f}\n"
                    msg += f"- High/Hot Membership: {fuzzy_result['HIGH']:.2f}\n"
                    self.blackboard.add_bot_message(msg)
                    
                    # Tentukan Jawaban berdasarkan Fuzzy Score
                    if 'low' in cause_key:
                        if fuzzy_result['LOW'] > 0.5:
                            tipe_jawaban = 'YES'
                            cf = fuzzy_result['LOW']
                        else:
                            tipe_jawaban = 'NO'
                            cf = 1.0 # Sangat yakin bukan low
                            
                    elif 'high' in cause_key:
                        if fuzzy_result['HIGH'] > 0.5:
                            tipe_jawaban = 'YES'
                            cf = fuzzy_result['HIGH']
                        else:
                            tipe_jawaban = 'NO'
                            cf = 1.0

            # --- 2. STANDARD LLM CHECK (Jika Fuzzy tidak jalan/tidak ada angka) ---
            if tipe_jawaban is None:
                tipe_jawaban, cf = self.llm.interpret_certainty(user_input, question_context)
            
            self.logger.info(f"User Answer Analysis: {tipe_jawaban} (CF={cf})")

            # --- 3. SIMPAN BUKTI ---
            if tipe_jawaban == 'YES' and cf > 0.5:
                self.blackboard.update_evidence(f"confirmed_cause_{cause_key}", cf)
            else:
                self.blackboard.update_evidence(f"rejected_cause_{cause_key}", 1.0)
            
            # --- 4. LOOPING (Pindah ke Pertanyaan Berikutnya) ---
            self.blackboard.set_doctor_state('DIAGNOSING')
            self.process() 

        elif state == 'SYNTHESIZE_RESULTS':
            # Ambil semua bukti yang terkumpul
            evidence = self.blackboard.get_evidence()
            confirmed_causes = [k for k, v in evidence.items() if k.startswith('confirmed_cause_')]
            problem_key = evidence.get('current_problem_key')
            
            if not confirmed_causes:
                self.blackboard.add_bot_message("Diagnosis complete. I've checked the most common factors, but none were confirmed. This suggests the issue might be related to the coffee bean quality itself (stale/roast defect) rather than your technique.")
            
            elif len(confirmed_causes) == 1:
                # KASUS TUNGGAL
                cause_key = confirmed_causes[0].replace('confirmed_cause_', '')
                
                solution_text = "Adjust parameters."
                if problem_key and problem_key in self.kb_rules:
                    if cause_key in self.kb_rules[problem_key]['causes']:
                        solution_text = self.kb_rules[problem_key]['causes'][cause_key]['solution']

                # Format Output
                context_str = "Role: Technical Coffee Technician. Tone: Direct, Concise."
                ideal_recipe = self.blackboard.get_context_recipe()
                if ideal_recipe:
                    context_str += f" Reference Recipe: Grind {ideal_recipe.grind_size}, Temp {ideal_recipe.water_temp_c}C."

                final_response = self.llm.generate_response(
                    prompt=f"""
                    SINGLE ROOT CAUSE FOUND: {cause_key}.
                    STANDARD FIX: "{solution_text}"
                    
                    TASK: Provide specific instructions to fix this. Bullet points. Under 50 words.
                    """,
                    context=context_str
                )
                self.blackboard.add_bot_message(f"**DIAGNOSIS COMPLETE**\n\nIdentified Issue: **{cause_key.replace('_', ' ').title()}**\n\n{final_response}")
            
            else:
                # KASUS MULTI-FAKTOR
                cause_keys = [k.replace('confirmed_cause_', '') for k in confirmed_causes]
                
                solutions_context = ""
                if problem_key and problem_key in self.kb_rules:
                    for ck in cause_keys:
                        if ck in self.kb_rules[problem_key]['causes']:
                            sol = self.kb_rules[problem_key]['causes'][ck]['solution']
                            solutions_context += f"- {ck}: {sol}\n"

                final_response = self.llm.generate_response(
                    prompt=f"""
                    COMPLEX DIAGNOSIS. Multiple issues detected: {', '.join(cause_keys)}.
                    
                    Reference Solutions:
                    {solutions_context}
                    
                    TASK: Create a prioritized recovery plan.
                    1. List the detected issues.
                    2. Identify which ONE to fix FIRST (the most critical one).
                    3. Provide concise actions. No fluff.
                    """,
                    context="Role: Senior Head Barista. Tone: Analytical & Directive."
                )
                self.blackboard.add_bot_message(f"**COMPLEX DIAGNOSIS: MULTIPLE FACTORS DETECTED**\n\n{final_response}")
            
            self.blackboard.set_doctor_state('DONE')