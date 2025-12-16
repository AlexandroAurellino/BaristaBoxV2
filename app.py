import streamlit as st
from src.core.blackboard import Blackboard
from src.agents.intent_agent import IntentAgent
from src.agents.doctor_agent import DoctorAgent
from src.agents.sommelier_agent import SommelierAgent
from src.agents.brewer_agent import BrewerAgent
from src.utils.logger import setup_logger

# Setup Logger untuk Orchestrator
logger = setup_logger("Orchestrator")

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="BaristaBox V2 (Blackboard Arch)",
    page_icon="☕",
    layout="wide" # Gunakan wide agar bisa lihat sidebar blackboard dengan jelas
)

# --- INITIALIZATION (Hanya sekali saat app start) ---
@st.cache_resource
def load_agents():
    """
    Memuat semua agen ke memori.
    Menggunakan cache agar model PyTorch tidak di-load berulang kali.
    """
    logger.info("Initializing Agents...")
    intent_agent = IntentAgent()
    doctor_agent = DoctorAgent()
    sommelier_agent = SommelierAgent()
    brewer_agent = BrewerAgent()
    return intent_agent, doctor_agent, sommelier_agent, brewer_agent

# Load agents
intent_agent, doctor_agent, sommelier_agent, brewer_agent = load_agents()

# Initialize Blackboard (Session State wrapper)
# Blackboard otomatis menangani persistensi state via st.session_state
board = Blackboard()

# --- SIDEBAR: THE BLACKBOARD MONITOR (Traceability) ---
with st.sidebar:
    st.header("🧠 Blackboard Monitor")
    st.caption("Intip apa yang dipikirkan sistem secara real-time.")
    
    # 1. Intent Status
    current_intent = board.get_intent()
    st.info(f"**Current Intent:**\n`{current_intent if current_intent else 'Scanning...'}`")
    
    # 2. Doctor Internal State
    doc_state = board.get_doctor_state()
    st.write(f"**Doctor State:** `{doc_state}`")
    
    # 3. Collected Evidence (Fakta yang dikumpulkan)
    evidence = board.get_evidence()
    if evidence:
        st.write("**Collected Facts (Evidence):**")
        st.json(evidence)
    else:
        st.caption("*No facts collected yet.*")
        
    st.divider()
    
    # 4. Context Objects (Frame Data)
    st.write("**Context Frames:**")
    bean = board.get_context_bean()
    recipe = st.session_state.get(board.KEY_CONTEXT_RECIPE) # Akses manual jika getter belum ada di code snippet sebelumnya
    
    if bean:
        st.success(f"**Bean:** {bean.name}")
    if recipe:
        st.success(f"**Recipe:** {recipe.brew_method}")

    # Tombol Reset untuk Debugging
    if st.button("🔄 Reset Memory"):
        board.clear_short_term_memory()
        st.rerun()

# --- MAIN UI: CHATBOT INTERFACE ---

st.title("☕ BaristaBox V2")
st.caption("Expert System with Blackboard Architecture & Case-Based Reasoning")

# 1. Tampilkan History Chat
for msg in board.get_chat_history():
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 2. Handle Input User
if prompt := st.chat_input("Apa keluhan atau keinginan Anda hari ini?"):
    
    # A. Masukkan pesan user ke Blackboard
    with st.chat_message("user"):
        st.markdown(prompt)
    board.add_user_message(prompt)

    # B. THE AGENT CYCLE (Siklus Kerja Agen)
    with st.chat_message("assistant"):
        with st.spinner("The Committee is thinking..."):
            
            # --- STEP 1: INTENT AGENT (WITH SMART LOCKING) ---
            
            # Cek status Dokter
            doctor_state = board.get_doctor_state()
            is_doctor_busy = doctor_state != 'INIT' and doctor_state != 'DONE'
            
            # Cek status Brewer (BARU)
            brewer_state = board.get_brewer_state()
            is_brewer_busy = brewer_state != 'INIT'
            
            # Hanya jalankan Intent Classifier jika SEMUA agen sedang menganggur
            if not is_doctor_busy and not is_brewer_busy:
                intent_agent.process() 
            
            # --- STEP 2: SPECIALIST AGENTS ---
            
            # Sommelier (Rekomendasi)
            sommelier_agent.process()
            
            # Brewer (Resep) - Sekarang dia akan jalan jika state='WAIT_METHOD' meskipun intent berubah
            brewer_agent.process()
            
            # Doctor (Diagnosis)
            doctor_agent.process()
            
            # --- STEP 3: UPDATE UI ---
            # Karena agen menulis langsung ke history blackboard, 
            # kita perlu mengambil pesan terakhir bot untuk ditampilkan di sesi ini
            history = board.get_chat_history()
            if history and history[-1]["role"] == "assistant":
                # Tampilkan pesan terakhir yang baru saja di-generate
                # (Streamlit agak tricky di sini, biasanya kita rerun agar loop history di atas yang merender)
                st.rerun()
            else:
                # Fallback jika tidak ada agen yang merespons
                st.warning("Sistem bingung. Tidak ada agen yang mengambil tugas ini.")