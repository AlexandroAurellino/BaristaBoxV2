# 🧠 Technical Implementation: Algorithms & Concepts

Dokumen ini menguraikan konsep kecerdasan buatan (AI) dan Sistem Pakar yang diterapkan dalam BaristaBox V2, serta bagaimana konsep tersebut diterjemahkan ke dalam implementasi kode.

---

## 1. Frame-Based Knowledge Representation

Sistem ini meninggalkan penyimpanan data relasional atau _dictionary_ sederhana demi representasi berbasis **Frame**.

- **Konsep:** Pengetahuan direpresentasikan sebagai objek ("Frames") yang memiliki **Slots** (atribut data) dan **Attached Procedures** (metode logika yang melekat pada objek tersebut).
- **Implementasi Code:**
  - **File:** `src/knowledge/bean_frame.py`
  - **Slots:** `self.origin`, `self.roast_level`, `self.expert_tags`.
  - **Attached Procedure:** Method `matches_tag(tag)` adalah prosedur logika yang tertanam di dalam frame untuk menentukan apakah dirinya relevan dengan kueri pengguna. Ini memindahkan logika pencarian dari _engine_ ke _data_ itu sendiri.

---

## 2. Case-Based Reasoning (CBR) dengan Algoritma Nearest Neighbor

CBR digunakan sebagai metode penalaran utama untuk menangani situasi di mana data eksak tidak ditemukan (misalnya: Biji kopi yang tidak dikenal).

- **Konsep:** Menyelesaikan masalah baru dengan mengadaptasi solusi dari kasus lama yang paling mirip.
- **Algoritma (Nearest Neighbor):**
  Sistem menghitung skor kemiripan (_Similarity Score_) antara **Target Case** (Input User) dan **Source Cases** (Database) menggunakan rumus _Weighted Sum_:

  $$ Similarity(T, S) = \frac{\sum*{i=1}^{n} w_i \times sim(f_i^T, f_i^S)}{\sum*{i=1}^{n} w_i} $$

  Dimana:

  - $w_i$: Bobot kepentingan fitur (misal: Roast Level lebih penting daripada Origin).
  - $sim(...)$: Fungsi kemiripan lokal antar fitur.

- **Implementasi Code:**
  - **File:** `src/core/cbr_engine.py` (Method `find_similar_bean`)
  - **Bobot:** `weights = {'origin': 0.3, 'roast_level': 0.4, 'processing': 0.3}`
  - **Proses:**
    1.  **Retrieve:** Cari bean di database dengan skor kemiripan tertinggi.
    2.  **Reuse:** Ambil resep dari bean tersebut.
    3.  **Revise:** Adaptasi resep tersebut sebagai referensi untuk bean baru pengguna.

---

## 3. Certainty Factors (CF) & Linguistic Fuzzy Mapping

Sistem menangani ketidakpastian input bahasa alami manusia menggunakan pendekatan hibrida antara LLM dan Logika Deterministik.

- **Konsep:** Pengguna jarang menjawab dengan biner (Ya/Tidak). Mereka menjawab dengan nuansa ("Kayaknya sih", "Yakin banget"). Kita perlu memetakan variabel linguistik ini ke nilai numerik (Certainty Factor).
- **Implementasi Code:**
  - **File:** `src/core/llm_service.py` (Method `interpret_certainty`)
  - **Langkah 1 (Fuzzy Classification via LLM):** LLM bertindak sebagai _Fuzzifier_, mengklasifikasikan input bebas ke dalam himpunan linguistik diskrit: `STRONG_YES`, `MILD_YES`, `UNSURE`, `MILD_NO`, `STRONG_NO`.
  - **Langkah 2 (CF Mapping):** Kode Python memetakan himpunan tersebut ke nilai CF pasti:
    - `STRONG_YES` $\rightarrow$ $CF = 1.0$
    - `MILD_YES` $\rightarrow$ $CF = 0.6$
    - `UNSURE` $\rightarrow$ $CF = 0.0$
- **Penggunaan:** Dalam `DoctorAgent`, diagnosis hanya dikonfirmasi jika $CF > 0.5$ (Threshold). Ini mencegah sistem mengambil kesimpulan prematur dari jawaban yang ragu-ragu.

---

## 4. Blackboard Architecture (Sistem Multi-Agen)

Untuk memungkinkan kolaborasi antara modul (Dokter, Sommelier, Brewer) tanpa _tight coupling_, digunakan arsitektur Blackboard.

- **Konsep:**
  - **Knowledge Sources (Agents):** Modul independen dengan keahlian khusus.
  - **Blackboard (Shared Memory):** Repositori data sentral tempat agen membaca dan menulis status masalah.
  - **Control Shell:** Mekanisme yang menentukan agen mana yang boleh bekerja.
- **Implementasi Code:**
  - **File:** `src/core/blackboard.py`
  - **Mekanisme:** Menggunakan `st.session_state` sebagai memori persisten.
  - **State Locking:** `DoctorAgent` dapat mengunci sistem (via `set_doctor_state`) sehingga `IntentAgent` tidak menginterupsi proses diagnosis yang sedang berjalan. Ini memecahkan masalah "Context Switching" yang kacau.

---

## 5. Rule-Based Reasoning sebagai Meta-Controller

Meskipun menggunakan AI, alur kerja sistem dikendalikan secara ketat oleh aturan prosedural (Rule-Based) untuk menjamin _explainability_.

- **Konsep:** Logika `IF-THEN` digunakan untuk mengontrol transisi state (_State Machine_) dan validasi logika.
- **Implementasi Code:**
  - **File:** `src/agents/doctor_agent.py`
  - **Contoh:**
    ```python
    IF context_recipe EXISTS:
        THEN generate_comparative_question()
    ELSE:
        THEN generate_generic_question()
    ```
  - Ini memastikan bahwa AI Generatif (Gemini) tidak berhalusinasi tentang alur prosedur, melainkan hanya mengisi konten bahasa di dalam kerangka aturan yang kaku.

---

Dokumen ini menunjukkan bahwa **BaristaBox AI** bukan sekadar pembungkus API (_wrapper_), melainkan sistem rekayasa yang mengintegrasikan paradigma AI klasik dan modern untuk menghasilkan solusi yang _robust_.
