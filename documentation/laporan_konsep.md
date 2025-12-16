Anda benar sekali. **Rule-Based Reasoning (RBR)** adalah tulang punggung yang mengendalikan seluruh sistem ini agar tidak "liar". Tanpa ini, sistem hanya akan menjadi chatbot biasa yang rentan halusinasi.

Sangat penting untuk menonjolkan ini secara akademis sebagai **Meta-Controller** atau **Deterministic Control Layer**.

Berikut adalah revisi lengkap **`ALGORITHMS_AND_CONCEPTS.md`**. Saya telah menambahkan Bab 4 khusus untuk **Rule-Based Reasoning** yang mencakup konsep _Finite State Automata_ dan _Forward Chaining_.

Silakan ganti seluruh isi file Anda dengan versi ini.

---

# Arsitektur Sistem, Algoritma, dan Konsep Implementasi

Dokumen ini menguraikan desain arsitektur, metode representasi pengetahuan, serta algoritma kecerdasan buatan yang diterapkan dalam pengembangan sistem pakar **BaristaBox V2**. Sistem ini mengadopsi pendekatan **Hibrida (Hybrid AI)** yang secara strategis menggabungkan determinisme Sistem Berbasis Aturan (_Rule-Based_) dengan fleksibilitas _Case-Based Reasoning_ (CBR) dan kemampuan semantik dari _Large Language Models_ (LLM).

---

## 1. Arsitektur Sistem: Pola Blackboard

Untuk menangani kompleksitas interaksi antara berbagai domain pengetahuan (Diagnostik, Rekomendasi, dan Resep), sistem ini menggunakan arsitektur **Blackboard**.

### 1.1. Konsep Blackboard

Blackboard adalah pola desain perangkat lunak di mana sekumpulan modul spesialis independen (**Knowledge Sources/Agents**) berkolaborasi memecahkan masalah dengan membaca dan menulis pada memori kerja bersama (**Blackboard**). Ini memutus ketergantungan langsung (_decoupling_) antar agen.

### 1.2. Komponen Arsitektur

1.  **The Blackboard (Memori Bersama):**
    - Menyimpan status global: _Current Intent_, _Context (Bean & Recipe)_, _Collected Evidence_, dan _Agent States_.
    - Berfungsi sebagai _Single Source of Truth_.
2.  **The Control Shell (Orchestrator):**
    - Mengelola siklus eksekusi agen.
    - Menerapkan **State Locking**: Mencegah interupsi (misal: perubahan intent) saat proses kritis (seperti diagnosis) sedang berlangsung.
3.  **Knowledge Sources (Agents):**
    - Setiap agen (`Intent`, `Doctor`, `Sommelier`, `Brewer`) adalah objek otonom yang memantau Blackboard dan bertindak saat kondisi terpenuhi.

---

## 2. Representasi Pengetahuan (Frame-Based Representation)

Sistem meninggalkan model data relasional demi representasi berbasis **Frame**.

### 2.1. Struktur Frame

Data JSON dipetakan menjadi Objek Python (`BeanFrame`, `RecipeFrame`) yang memiliki:

- **Slots (Atribut):** Data faktual (misal: `origin`, `roast_level`).
- **Attached Procedures (Prosedur Melekat):** Metode logika yang tertanam dalam objek untuk memanipulasi data dirinya sendiri.
  - _Implementasi:_ Method `to_cbr_features()` pada `BeanFrame` adalah prosedur melekat yang menyiapkan data objek untuk diproses oleh mesin CBR.

---

## 3. Metode Penalaran: AI & Heuristik (The "Soft" Logic)

Komponen ini menangani ketidakpastian, ambiguitas bahasa, dan pencarian kemiripan.

### 3.1. Case-Based Reasoning (CBR) dengan Weighted Nearest Neighbor

Digunakan untuk menangani situasi _Unknown Data_ (misal: biji kopi baru) dan memberikan rekomendasi.

**Algoritma:**
Sistem menggunakan algoritma _Weighted Nearest Neighbor_ untuk menghitung skor kemiripan ($Similarity Score$) antara kasus target ($T$) dan kasus sumber ($S$).

$$ Similarity(T, S) = \frac{\sum*{i=1}^{n} w_i \times sim(f_i^T, f_i^S)}{\sum*{i=1}^{n} w_i} $$

Dimana $w_i$ adalah bobot kepentingan fitur (misal: _Roast Level_ > _Origin_).

### 3.2. Fuzzy Logic (Logika Samar)

Digunakan untuk menangani input numerik yang tidak presisi (misal: suhu air). Variabel suhu dipetakan ke dalam himpunan fuzzy (**LOW**, **IDEAL**, **HIGH**) menggunakan fungsi keanggotaan trapesium.

- _Contoh:_ Input 91°C menghasilkan derajat keanggotaan ganda ($\mu_{LOW}=0.5, \mu_{IDEAL}=0.5$), memungkinkan diagnosis yang lebih halus.

### 3.3. Certainty Factors (CF) via Semantic Analysis

Menangani ambiguitas jawaban pengguna.

1.  **LLM Classifier:** Mengklasifikasikan input ke kategori linguistik (`STRONG_YES`, `MILD_YES`, `UNSURE`, dll).
2.  **CF Mapping:** Memetakan kategori tersebut ke nilai numerik pasti ($1.0, 0.6, 0.0$).

---

## 4. Metode Penalaran: Rule-Based Reasoning (The "Hard" Logic)

Ini adalah komponen **Sistem Pakar Klasik** yang bertindak sebagai **Meta-Controller**. Logika ini bersifat deterministik, transparan, dan berfungsi untuk menjaga agar sistem tetap berada di jalur yang benar (menghindari halusinasi AI).

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

## 5. Kesimpulan Implementasi

BaristaBox V2 mendemonstrasikan arsitektur **Hibrida Sinergis**:

1.  **Rule-Based System** menyediakan struktur, kontrol, dan _explainability_.
2.  **Blackboard** menyediakan koordinasi dan memori.
3.  **CBR & Fuzzy** menangani penalaran kompleks dan adaptasi.
4.  **LLM** menangani antarmuka bahasa alami.

Kombinasi ini menghasilkan sistem yang _robust_ (tahan banting), cerdas, namun tetap terkendali dan dapat dipercaya.
