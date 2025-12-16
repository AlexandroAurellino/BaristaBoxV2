# Arsitektur Sistem, Algoritma, dan Konsep Implementasi

Dokumen ini menguraikan desain arsitektur, metode representasi pengetahuan, serta algoritma kecerdasan buatan yang diterapkan dalam pengembangan sistem pakar **BaristaBox V2**. Sistem ini mengadopsi pendekatan **Hibrida (Hybrid AI)** yang secara strategis menggabungkan determinisme Sistem Berbasis Aturan (_Rule-Based_) dengan fleksibilitas _Case-Based Reasoning_ (CBR) dan kemampuan semantik dari _Large Language Models_ (LLM).

---

## 1. Arsitektur Sistem: Pola Blackboard

Untuk menangani kompleksitas interaksi antara berbagai domain pengetahuan (Diagnostik, Rekomendasi, dan Resep), sistem ini meninggalkan pendekatan prosedural linear demi arsitektur **Blackboard**.

### 1.1. Konsep Blackboard

Blackboard adalah pola desain perangkat lunak di mana sekumpulan modul spesialis independen (**Knowledge Sources/Agents**) berkolaborasi untuk memecahkan masalah dengan membaca dan menulis pada memori kerja bersama (**Blackboard**). Pola ini memutus ketergantungan langsung (_decoupling_) antar agen, memungkinkan sistem yang modular dan skalabel.

### 1.2. Komponen Arsitektur

1.  **The Blackboard (Memori Bersama):**

    - Diimplementasikan sebagai pembungkus (_wrapper_) di sekitar _session state_.
    - Menyimpan status global: _Current Intent_, _User Input_, _Context (Bean & Recipe)_, dan _Collected Evidence_.
    - Berfungsi sebagai _Single Source of Truth_ yang memungkinkan agen berbagi informasi tanpa _coupling_ langsung.
    - **Implementasi:** `src/core/blackboard.py`

2.  **The Control Shell (Orchestrator):**

    - Terletak pada `app.py`. Bertugas mengelola siklus eksekusi agen.
    - Menerapkan mekanisme **State Locking**: Jika agen Dokter sedang melakukan diagnosis aktif, Orkestrator mencegah agen lain (seperti Intent Classifier) untuk menginterupsi hingga tugas selesai.
    - Ini memecahkan masalah "Context Switching" yang kacau.

3.  **Knowledge Sources (Agents):**
    Setiap agen adalah objek otonom dengan keahlian spesifik yang memantau Blackboard dan bertindak saat kondisi yang relevan terpenuhi:
    - **IntentAgent:** Menggunakan model _Deep Learning_ (PyTorch/DistilBERT) untuk klasifikasi awal.
    - **DoctorAgent:** Spesialis diagnostik menggunakan _Rule-Based_ dan _Fuzzy Logic_.
    - **SommelierAgent:** Spesialis rekomendasi menggunakan _Weighted CBR_.
    - **BrewerAgent:** Spesialis prosedur menggunakan _Hybrid Lookup_ dan _Analogical CBR_.

---

## 2. Representasi Pengetahuan (Frame-Based Representation)

Sistem tidak menggunakan basis data relasional, melainkan mengadopsi **Frame-Based Knowledge Representation**. Pengetahuan direpresentasikan sebagai objek terstruktur ("Frames") yang memiliki atribut data dan prosedur logika.

### 2.1. Struktur Frame

Data JSON mentah dipetakan menjadi Objek Python (`BeanFrame`, `RecipeFrame`) dengan komponen berikut:

- **Frame Name:** Identitas objek (misal: ID unik biji kopi).
- **Slots (Atribut):** Data faktual (misal: `origin`, `roast_level`, `processing`).
- **Attached Procedures (Prosedur Melekat):** Metode logika yang tertanam dalam frame untuk memanipulasi data tersebut.
  - **Implementasi:** `src/knowledge/bean_frame.py` dan `src/knowledge/recipe_frame.py`
  - _Contoh Implementasi:_ Method `matches_tag(tag)` pada `BeanFrame` adalah prosedur melekat yang memungkinkan objek biji kopi "mengetahui" apakah dirinya sesuai dengan kriteria pengguna.
  - Method `to_cbr_features()` adalah prosedur yang menyiapkan data objek untuk diproses oleh mesin CBR.

**Keuntungan:**

- Logika pencarian dipindahkan dari _engine_ ke _data_ itu sendiri, menghasilkan kode yang lebih modular.

---

## 3. Metode Penalaran: AI & Heuristik (The "Soft" Logic)

Komponen ini menangani ketidakpastian, ambiguitas bahasa, dan pencarian kemiripan.

### 3.1. Case-Based Reasoning (CBR) dengan Algoritma Weighted Nearest Neighbor

CBR digunakan dalam modul **Sommelier** (untuk rekomendasi) dan **Brewer** (untuk menangani biji kopi yang tidak dikenal). Sistem memecahkan masalah baru dengan mencari kasus lama yang paling mirip dalam basis pengetahuan.

**Algoritma Perhitungan Kemiripan:**
Sistem menggunakan algoritma _Weighted Nearest Neighbor_ untuk menghitung skor kemiripan ($Similarity Score$) antara kasus target (input pengguna) dan kasus sumber (database).

Rumus yang diimplementasikan dalam `CBREngine`:

$$ Similarity(T, S) = \frac{\sum*{i=1}^{n} w_i \times sim(f_i^T, f_i^S)}{\sum*{i=1}^{n} w_i} $$

Dimana:

- $T$: Kasus Target (Kueri Pengguna).
- $S$: Kasus Sumber (Data di Database).
- $w_i$: Bobot kepentingan untuk fitur ke-$i$ (misal: fitur _Roast Level_ memiliki bobot lebih tinggi daripada _Origin_ dalam penentuan resep).
  - Contoh: `weights = {'origin': 0.3, 'roast_level': 0.4, 'processing': 0.3}`
- $sim(...)$: Fungsi kemiripan lokal:
  - Untuk data simbolik (Teks): 1 jika cocok, 0 jika tidak.
  - Untuk data numerik: $1 / (1 + |val_T - val_S|)$.

**Implementasi Code:**

- **File:** `src/core/cbr_engine.py` (Method `find_similar_bean`)
- **Proses:**
  1.  **Retrieve:** Cari bean di database dengan skor kemiripan tertinggi.
  2.  **Reuse:** Ambil resep dari bean tersebut.
  3.  **Revise:** Adaptasi resep tersebut sebagai referensi untuk bean baru pengguna.

### 3.2. Fuzzy Logic (Logika Samar)

Digunakan dalam modul **Doctor** untuk menangani ketidakpastian input numerik, khususnya pada variabel suhu air. Alih-alih menggunakan batasan tegas (_crisp logic_) seperti `jika suhu < 90`, sistem menggunakan fungsi keanggotaan (_membership function_).

**Implementasi Fungsi Keanggotaan (Suhu):**
Variabel suhu dipetakan ke dalam tiga himpunan fuzzy: **LOW**, **IDEAL**, dan **HIGH** menggunakan kurva trapesium.

- _Contoh:_ Input suhu 91°C (di area transisi) akan menghasilkan derajat keanggotaan ganda, misalnya: $\mu_{LOW}(91) = 0.5$ dan $\mu_{IDEAL}(91) = 0.5$.
- Hal ini memungkinkan sistem untuk mendeteksi nuansa "agak dingin" atau "hampir ideal" dan mengambil keputusan yang lebih halus.

**Implementasi:**

- **File:** `src/agents/doctor_agent.py`

### 3.3. Certainty Factors (CF) dengan Semantic Mapping

Sistem menangani ambiguitas jawaban pengguna (misal: "Mungkin", "Kayaknya sih") menggunakan pendekatan hibrida antara LLM dan pemetaan deterministik.

**Mekanisme:**

1.  **Semantic Classification (via LLM):** Model bahasa menganalisis sentimen dan konteks jawaban pengguna untuk mengklasifikasikannya ke dalam kategori linguistik diskrit: `STRONG_YES`, `MILD_YES`, `UNSURE`, `MILD_NO`, `STRONG_NO`.
2.  **Deterministic Mapping (via Python):** Kategori linguistik dipetakan ke nilai numerik CF yang pasti:
    - `STRONG_YES` $\rightarrow$ $CF = 1.0$
    - `MILD_YES` $\rightarrow$ $CF = 0.6$
    - `UNSURE` $\rightarrow$ $CF = 0.0$

**Penggunaan dalam Diagnosis:**

- Dalam `DoctorAgent`, diagnosis hanya dikonfirmasi jika $CF > 0.5$ (Threshold).
- Ini mencegah sistem mengambil kesimpulan prematur dari jawaban yang ragu-ragu.

**Implementasi Code:**

- **File:** `src/core/llm_service.py` (Method `interpret_certainty`)
- LLM bertindak sebagai _Fuzzifier_, mengklasifikasikan input bebas ke dalam himpunan linguistik diskrit.

---

## 4. Metode Penalaran: Rule-Based Reasoning (The "Hard" Logic)

Ini adalah komponen **Sistem Pakar Klasik** yang bertindak sebagai **Meta-Controller** atau **Deterministic Control Layer**. Logika ini bersifat deterministik, transparan, dan berfungsi untuk menjaga agar sistem tetap berada di jalur yang benar (menghindari halusinasi AI).

**Rule-Based Reasoning** adalah tulang punggung yang mengendalikan seluruh sistem ini agar tidak "liar". Tanpa ini, sistem hanya akan menjadi chatbot biasa yang rentan halusinasi.

### 4.1. Finite State Automata (Mesin State)

Setiap agen (`Doctor`, `Brewer`) diimplementasikan sebagai **State Machine**. Perilaku agen ditentukan secara kaku oleh _state_ saat ini.

- **Struktur Logika:**
  ```python
  IF state == 'INIT': Lakukan inisialisasi & cek database
  ELIF state == 'ASK_CONTEXT': Ajukan pertanyaan wajib
  ELIF state == 'DIAGNOSING': Jalankan loop inferensi
  ```
- **Tujuan:** Menjamin urutan prosedur yang baku (SOP) yang tidak bisa dilanggar oleh LLM.

### 4.2. Forward Chaining (Rantai Maju)

Digunakan dalam modul **Doctor** untuk proses diagnosis.

- **Mekanisme:** Sistem memulai dengan sekumpulan fakta (gejala awal) dan bergerak maju melalui serangkaian aturan (`IF cause_X THEN ask_question_X`) untuk mengumpulkan bukti baru (`evidence`), hingga mencapai kesimpulan (`diagnosis`).
- **Implementasi:** Loop `while` yang memproses antrian aturan (_rule queue_) satu per satu, memverifikasi fakta dengan pengguna, dan menyimpan hasil konfirmasi.
- **File:** `src/agents/doctor_agent.py`

### 4.3. Heuristic Override (Aturan Prioritas)

Digunakan dalam modul **Intent** untuk meningkatkan akurasi.

- **Logika:**
  ```python
  IF input_user CONTAINS known_bean_name:
      THEN force_intent = 'master_brewer' (Rule Base)
  ELSE:
      THEN use_neural_network_prediction() (Machine Learning)
  ```
- **Tujuan:** Memastikan fakta yang sudah diketahui (nama biji kopi di database) selalu mengalahkan prediksi probabilistik model AI.

---

## 5. Implementasi Logika Agen

Setiap agen menerapkan strategi penalaran yang berbeda sesuai dengan tugasnya.

### 5.1. Doctor Agent (Diagnostic & Troubleshooting)

- **Strategi:** _Context-Aware Rule-Based Reasoning_.
- **Alur Kerja:**
  1.  **Pengumpulan Konteks:** Mengidentifikasi Biji Kopi dan Metode Seduh.
  2.  **Pencarian Resep Referensi:** Mencari resep ideal di database sebagai standar perbandingan.
  3.  **Loop Pengumpulan Bukti:** Menggunakan _Forward Chaining_ untuk menguji hipotesis penyebab masalah satu per satu. Pertanyaan disesuaikan secara dinamis berdasarkan Resep Referensi (misal: membandingkan suhu pengguna dengan suhu resep).
  4.  **Sintesis:** Mengumpulkan semua bukti yang terkonfirmasi ($CF > threshold$) dan memberikan diagnosis (tunggal atau multi-faktor).

**Implementasi:**

- **File:** `src/agents/doctor_agent.py`

### 5.2. Sommelier Agent (Recommendation)

- **Strategi:** _Weighted Case-Based Reasoning_.
- **Alur Kerja:**
  1.  **Ekstraksi Preferensi:** Menggunakan LLM untuk memecah kalimat pengguna menjadi pasangan fitur dan bobot (misal: `{"fruity": 1.0, "bitter": -1.0}`).
  2.  **Scoring:** Menghitung skor kemiripan setiap biji kopi dalam database terhadap preferensi berbobot tersebut.
  3.  **Ranking:** Mengurutkan hasil dan merekomendasikan biji kopi dengan skor tertinggi (_Top-N_).

**Implementasi:**

- **File:** `src/agents/sommelier_agent.py`

### 5.3. Brewer Agent (Recipe Generation)

- **Strategi:** _Hybrid Rule-Based & Analogical Reasoning_.
- **Alur Kerja:**
  - **Jika Biji Kopi Dikenal:** Menggunakan _Rule-Based Lookup_ untuk mengambil resep eksak.
  - **Jika Biji Kopi Tidak Dikenal:** Beralih ke mode **CBR**. Sistem meminta atribut fisik biji kopi (Tingkat Sangrai, Proses), mencari biji kopi lain yang paling mirip di database (_Nearest Neighbor_), dan mengadaptasi resep dari biji kopi tersebut sebagai solusi (_Adaptation Strategy_).

**Implementasi:**

- **File:** `src/agents/brewer_agent.py`

---

## 6. Kesimpulan Implementasi

BaristaBox V2 mendemonstrasikan arsitektur **Hibrida Sinergis**:

1.  **Rule-Based System** menyediakan struktur, kontrol, dan _explainability_.
2.  **Blackboard** menyediakan koordinasi dan memori.
3.  **CBR & Fuzzy** menangani penalaran kompleks dan adaptasi.
4.  **LLM** menangani antarmuka bahasa alami.

Kombinasi ini menghasilkan sistem yang _robust_ (tahan banting), cerdas, namun tetap terkendali dan dapat dipercaya.
