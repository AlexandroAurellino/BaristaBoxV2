# Architectural Decision Record: Evolusi Menuju BaristaBox V2

**Tanggal:** [Tanggal Hari Ini]
**Status:** Approved / In Progress
**Konteks:** Migrasi dari _Prototype Script_ (V1) menuju _Robust Expert System Architecture_ (V2).

---

## 1. Pendahuluan: Mengapa Memulai Ulang?

BaristaBox V1 telah berhasil membuktikan konsep (_Proof of Concept_). Kita berhasil menggabungkan model klasifikasi PyTorch dengan kemampuan generatif LLM (Gemini) dalam sebuah aplikasi Streamlit. Fungsionalitas dasar seperti Diagnosis, Rekomendasi, dan Resep sudah berjalan.

Namun, seiring berkembangnya kompleksitas logika—terutama dengan kebutuhan akan diagnosis yang peka konteks (_context-aware_) dan penanganan input yang ambigu—struktur kode prosedural/linear yang lama mulai menunjukkan keterbatasannya. Kode menjadi sulit dilacak (_trace_), sulit dikembangkan (_scale_), dan logika "pintar" tersebar di berbagai tempat tanpa struktur yang jelas.

Oleh karena itu, BaristaBox V2 dibangun dari nol (_from the ground up_) bukan untuk mengubah tujuan aplikasi, melainkan untuk merevolusi **bagaimana mesin berpikir dan bekerja di balik layar**.

---

## 2. Mengapa beralih ke Object-Oriented Programming (OOP)?

Dalam V1, kita banyak menggunakan fungsi-fungsi lepas dan _dictionary_ mentah.

- **Masalah:** Data dan logika terpisah. Sulit untuk mengetahui fungsi mana yang boleh memodifikasi data kopi, dan debugging menjadi seperti mencari jarum dalam jerami ketika variabel dilempar ke sana kemari.
- **Solusi V2:** Kita mengadopsi OOP sepenuhnya.
- **Alasan:**
  1.  **Encapsulation:** Setiap komponen (Dokter, Sommelier, Brewer) akan menjadi **Agen (Objek)** yang memiliki memori dan keahliannya sendiri.
  2.  **Modularitas:** Kita bisa memperbaiki logika "Dokter" tanpa takut merusak logika "Sommelier".
  3.  **Clean Architecture:** Memisahkan _Interface_ (Streamlit) dari _Logic_ (Brain).

---

## 3. Mengapa Mengadopsi Frame-Based Knowledge Representation?

Di V1, basis pengetahuan kita hanyalah file JSON yang dibaca sebagai _Python Dictionary_ biasa.

- **Masalah:** JSON adalah data pasif. Ia tidak punya "kecerdasan". Jika kita ingin membandingkan dua biji kopi, kita harus menulis fungsi eksternal yang rumit.
- **Solusi V2:** Menggunakan konsep **Frame**.
- **Alasan:**
  - **Representasi Kaya:** Frame bukan sekadar data; ia adalah representasi konsep. Frame `BijiKopi` tidak hanya menyimpan `origin` atau `rasa`, tetapi juga memiliki **Attached Procedures** (Prosedur Melekat).
  - **Kecerdasan Melekat:** Logika untuk menghitung "kemiripan" antara dua biji kopi atau logika untuk menentukan apakah sebuah resep cocok, sekarang **tertanam (attached)** di dalam objek itu sendiri. Ini membuat sistem lebih otonom dan rapi.

---

## 4. Mengapa Case-Based Reasoning (CBR) & Fuzzy Logic?

Di V1, kita sangat bergantung pada aturan kaku (`IF suhu < 90 THEN ...`).

- **Masalah:** Dunia nyata tidak biner (Hitam/Putih). Pengguna sering berkata "Airnya _agak_ panas" atau "Rasanya _lumayan_ asam". Aturan kaku sering gagal menangani nuansa ini atau kasus yang belum pernah didefinisikan secara eksplisit.
- **Solusi V2:**
  1.  **CBR (Case-Based Reasoning):** Sistem belajar dari pengalaman. Alih-alih hanya mengikuti aturan, sistem mencari kasus lama yang paling mirip. "Masalah ini mirip dengan kasus Ethiopia minggu lalu, mari coba solusi yang sama." Ini membuat sistem mampu menangani _unseen scenarios_ melalui analogi.
  2.  **Fuzzy Logic (Logika Samar):** Kita tidak lagi melihat suhu sebagai angka mutlak, tapi sebagai derajat keanggotaan. "92 derajat" mungkin memiliki keanggotaan 0.8 di kategori "Panas" dan 0.2 di "Sedang". Ini membuat sistem lebih toleran dan manusiawi dalam memahami input pengguna.

---

## 5. Mengapa Blackboard Architecture?

Di V1, alur kerjanya linear: Input -> Klasifikasi -> Satu Engine Bekerja -> Selesai.

- **Masalah:** Dalam diagnosis yang kompleks, seringkali kita butuh kolaborasi. Sommelier mungkin menyarankan biji kopi, tapi Master Brewer perlu tahu biji apa itu untuk memberi resep, dan Dokter perlu memantau parameter seduhnya. V1 membuat komunikasi antar-modul ini sulit.
- **Solusi V2:** Arsitektur Papan Tulis (_Blackboard Architecture_).
- **Alasan:**
  - Kita menciptakan **Shared Memory (Blackboard)** di mana semua agen (Dokter, Sommelier, Brewer) bisa membaca dan menulis.
  - Ini memungkinkan kolaborasi non-linear. Agen Dokter bisa melihat fakta yang ditaruh oleh Agen Brewer di papan tulis dan memberikan peringatan ("Hati-hati, resep itu butuh suhu tinggi!"). Ini meniru cara kerja tim pakar yang sedang berdiskusi.

---

## 6. Bagaimana Menangani Ketidakpastian (Certainty Factors)?

- **Strategi:** Alih-alih meminta pengguna memberikan angka ("Seberapa yakin Anda 1-10?"), kita menggunakan LLM (Gemini) sebagai ahli bahasa.
- **Mekanisme:** LLM membaca bahasa alami pengguna ("Kayaknya sih gitu...", "Yakin banget!"), dan menerjemahkannya menjadi **Certainty Factor (CF)** numerik di balik layar.
- **Tujuan:** Menjaga antarmuka tetap natural (seperti chat biasa) namun di belakang layar sistem memiliki data matematis untuk menghitung reliabilitas diagnosis.

---

**Kesimpulan:**
BaristaBox V2 bukan sekadar _update_ fitur, melainkan transformasi paradigma dari sistem berbasis skrip sederhana menjadi **Sistem Pakar Hibrida Cerdas** yang _scalable_, _robust_, dan menyerupai cara berpikir ahli manusia.

## 7. Analisis Mendalam: V1 (Meta-Rule) vs. V2 (Blackboard)

Salah satu perubahan paling fundamental dalam V2 adalah pergeseran dari **Control-Flow Driven** ke **Data-Driven Architecture**.

### A. V1: Pendekatan "Satu Otak Super" (Monolithic/Tightly Coupled)

Pada V1, logika bersifat prosedural dan terpusat.

- **Mekanisme:** `DoctorEngine` bertindak sebagai pengendali utama. Ia secara eksplisit memanggil fungsi pencarian resep, memanggil fungsi pencarian bean, dan mengatur semua logika percabangan (_if-else_).
- **Kelemahan (Tight Coupling):** Modul Dokter harus "tahu" secara detail tentang keberadaan dan cara kerja modul Resep. Jika modul Resep mengalami error, modul Dokter berpotensi ikut gagal (_crash_). Menambah fitur baru (misalnya: kalkulator harga) mengharuskan kita membedah kode Dokter yang sudah ada.

### B. V2: Pendekatan "Komite Ahli" (Decoupled/Modular)

Pada V2, tidak ada satu agen yang mengontrol segalanya. Para agen bekerja secara independen di sekitar memori bersama (_Blackboard_).

- **Mekanisme:**
  1.  **IntentAgent** menempelkan label `INTENT: DOCTOR` di papan tulis.
  2.  **SommelierAgent** (jika aktif) melihat nama kopi di input user, lalu menempelkan data `CONTEXT_BEAN: Ethiopia` di papan tulis.
  3.  **BrewerAgent** melihat data `CONTEXT_BEAN` tersebut, lalu secara proaktif menempelkan `CONTEXT_RECIPE` yang relevan di papan tulis.
  4.  **DoctorAgent** akhirnya bekerja. Ia tidak perlu memanggil Brewer. Ia cukup melihat ke papan tulis dan berkata, "Ah, sudah ada data resep di sini. Saya akan menggunakannya untuk diagnosis."
- **Keunggulan (Decoupling):**
  - **Independensi:** Dokter tidak perlu tahu siapa yang menaruh data resep di sana. Jika `BrewerAgent` mati, Dokter tetap jalan (hanya tanpa data resep).
  - **Skalabilitas:** Kita bisa menambahkan `PriceAgent` (Agen Harga) yang memantau papan tulis dan menghitung biaya setiap kali resep muncul, tanpa perlu mengubah satu baris pun kode pada agen lain.
  - **Traceability:** Kita memiliki satu titik pusat (_The Blackboard_) untuk memantau status seluruh sistem, memudahkan debugging alur logika yang kompleks.

**Kesimpulan:** V2 mengubah sistem dari sekadar kumpulan skrip pintar menjadi sebuah ekosistem agen otonom yang berkolaborasi, menciptakan fondasi yang jauh lebih _robust_ untuk pengembangan jangka panjang.

---

## 🛠️ Tantangan Pengembangan & Solusi Teknis

Selama proses pengembangan BaristaBox AI, kami menghadapi beberapa tantangan teknis mendasar terkait integrasi _Rule-Based System_ dengan _Generative AI_. Berikut adalah rincian masalah utama dan solusi arsitektural yang diterapkan.

### 1. Masalah "Black Box Logic" & Halusinasi

**Masalah:**
Pada iterasi awal (V1), sistem terlalu bergantung pada LLM (Gemini) untuk membuat keputusan diagnostik. Akibatnya, alur logika menjadi sulit dilacak (_untraceable_) dan rentan terhadap halusinasi (memberikan saran yang tidak ada di basis pengetahuan). Dosen/Reviewer menilai sistem "Terlalu AI" dan kurang memiliki karakteristik Sistem Pakar yang deterministik.

**Solusi:**
Kami melakukan refactoring total menuju **Arsitektur Hibrida (Rule-Based Controller + LLM Interface)**.

- **Logika Deterministik:** Kendali alur diagnosis (`IF-THEN`) dipindahkan sepenuhnya ke kode Python. Sistem secara eksplisit menguji aturan satu per satu dari _Knowledge Base_.
- **Peran Terbatas LLM:** Peran Gemini dibatasi hanya sebagai "Penerjemah Bahasa" (memformat pertanyaan/jawaban) dan bukan sebagai pengambil keputusan logika. Ini menjamin _explainability_.

### 2. Masalah "Intent Flipping" (Hilangnya Konteks Percakapan)

**Masalah:**
Saat sistem sedang dalam tengah proses diagnosis dan bertanya _"Metode seduh apa yang Anda gunakan?"_, pengguna menjawab _"V60"_.
_Classifier_ sistem salah mengartikan jawaban "V60" sebagai permintaan resep baru, sehingga sistem tiba-tiba berpindah dari mode `Doctor` ke `MasterBrewer`, memutus alur diagnosis yang sedang berjalan.

**Solusi:**
Implementasi mekanisme **State Locking** pada **Blackboard Architecture**.

- Kami menambahkan _internal state_ pada setiap agen (misal: `WAIT_METHOD_RESPONSE`).
- **Logika Orkestrator Cerdas:** Jika seorang agen sedang dalam status "Sibuk" (menunggu jawaban), Orkestrator akan **mengunci** intent classifier dan memaksa input pengguna untuk diarahkan langsung ke agen yang sedang aktif tersebut, mencegah interupsi alur.

### 3. Ambiguitas Input Bahasa Alami vs Logika Biner

**Masalah:**
Sistem pakar membutuhkan input fakta yang pasti (Ya/Tidak) untuk memicu aturan. Namun, pengguna sering menjawab dengan bahasa alami yang ambigu, seperti _"Sepertinya iya"_ atau _"Saya beli 3 bulan lalu"_ (saat ditanya apakah kopi tua). Logika pencocokan _keyword_ sederhana gagal menangani nuansa ini.

**Solusi:**
Penerapan **LLM sebagai Interpreter Logika**.

- Kami menggunakan LLM untuk menganalisis semantik jawaban pengguna dalam konteks pertanyaan.
- Kami memetakan hasil analisis tersebut ke dalam **Certainty Factors (CF)** yang terukur.
  - _"3 bulan lalu"_ $\rightarrow$ LLM: `STRONG_YES` $\rightarrow$ Python: `CF = 1.0` $\rightarrow$ Aturan `Old Beans` terpicu.

### 4. Masalah Data Tidak Dikenal (_Cold Start_)

**Masalah:**
Jika pengguna meminta resep untuk biji kopi yang tidak ada dalam database (misal: _"Java Frinsa"_), sistem berbasis aturan standar akan gagal total atau memberikan pesan error.

**Solusi:**
Implementasi **Case-Based Reasoning (CBR)** dengan Analogi.

- Sistem tidak menyerah, melainkan mengumpulkan atribut fitur dari biji kopi baru tersebut (misal: _Light Roast, Natural Process_).
- Algoritma _Nearest Neighbor_ menghitung jarak kemiripan dengan semua kasus (biji kopi) yang ada di database.
- Sistem mengadaptasi resep dari "tetangga terdekat" (misal: _Ethiopia Natural_) dan menyajikannya sebagai solusi referensi.

### 5. Masalah "Yapping" (Output yang Bertele-tele)

**Masalah:**
LLM cenderung memberikan jawaban yang terlalu sopan, panjang lebar, dan puitis, yang mengubur informasi teknis (suhu, gramasi) yang dibutuhkan pengguna.

**Solusi:**
Penerapan **Strict Prompt Engineering** dan **SOP Formatting**.

- Kami mengubah instruksi sistem (_System Prompt_) menjadi sangat ketat: _"No conversational filler. Use bullet points. Be technical and direct."_
- Data resep disusun terlebih dahulu dalam format terstruktur oleh Python sebelum dikirim ke LLM untuk diformat, memastikan tidak ada data yang hilang atau ditambah-tambahkan.

---

Bagian ini akan sangat memperkuat laporan Anda karena menunjukkan bahwa Anda tidak hanya "coding sampai jadi", tetapi benar-benar melakukan rekayasa perangkat lunak untuk mengatasi masalah fundamental dalam pengembangan AI.
