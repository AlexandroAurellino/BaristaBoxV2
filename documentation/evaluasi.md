# Laporan Evaluasi dan Pengujian Sistem Pakar (BaristaBox V2)

## 1. Pendahuluan dan Strategi Pengujian

Evaluasi sistem BaristaBox V2 dilakukan untuk memvalidasi kekokohan (_robustness_) arsitektur _Blackboard_, akurasi algoritma kecerdasan buatan (CBR, Fuzzy, CF), serta fungsionalitas integrasi sistem secara keseluruhan. Strategi pengujian dibagi menjadi tiga lapisan:

1.  **Verifikasi Statis:** Pemeriksaan integritas basis pengetahuan (Knowledge Base).
2.  **Pengujian Unit (Unit Testing):** Validasi terisolasi terhadap algoritma matematika dan logika (CBR & Fuzzy).
3.  **Pengujian Integrasi (End-to-End Testing):** Validasi alur kerja sistem dalam menangani skenario pengguna yang kompleks melalui mekanisme _Blackboard_.

---

## 2. Metrik Evaluasi

Berikut adalah parameter yang digunakan untuk mengukur keberhasilan sistem:

| Komponen         | Metrik                 | Deskripsi & Target Keberhasilan                                                                                                              |
| :--------------- | :--------------------- | :------------------------------------------------------------------------------------------------------------------------------------------- |
| **CBR Engine**   | _Similarity Precision_ | Kemampuan algoritma untuk menghitung skor kemiripan yang proporsional dengan bobot input pengguna (bukan hanya _match/no-match_).            |
| **Fuzzy Logic**  | _Boundary Validity_    | Kemampuan fungsi keanggotaan untuk menangani nilai di area transisi (misal: suhu "hangat") dengan derajat keanggotaan non-biner (0.0 - 1.0). |
| **LLM Service**  | _Mapping Consistency_  | Konsistensi pemetaan bahasa alami yang ambigu menjadi nilai _Certainty Factor_ (CF) numerik yang deterministik.                              |
| **Orchestrator** | _Context Retention_    | Kemampuan sistem untuk menjaga konteks percakapan (nama biji kopi, metode seduh) tanpa kehilangan status saat berpindah antar-agen.          |
| **System**       | _Robustness_           | Kemampuan sistem menangani input yang tidak diketahui (_unknown inputs_) tanpa _crash_, menggunakan mekanisme _fallback_ atau analogi.       |

---

## 3. Hasil Pengujian Unit (Logika & Algoritma)

Pengujian ini dilakukan secara otomatis menggunakan skrip `tests/test_evaluation.py` untuk menguji komponen inti secara terisolasi.

### 3.1. Evaluasi Certainty Factors (CF) & NLP

Menguji kemampuan `LLMService` dalam menerjemahkan ambiguitas manusia.

- **Skenario A (Input Tegas):** Input "Yes absolutely".
  - _Hasil:_ Terklasifikasi `STRONG_YES` $\rightarrow$ Dipetakan ke **CF 1.0**.
- **Skenario B (Input Ragu):** Input "I don't know" atau "Maybe".
  - _Hasil:_ Terklasifikasi `UNSURE` / `MILD_YES` $\rightarrow$ Dipetakan ke **CF 0.0** / **CF 0.6**.
- **Kesimpulan:** Sistem berhasil mengubah input kualitatif menjadi kuantitatif untuk perhitungan mesin.

### 3.2. Evaluasi Fuzzy Logic (Temperatur)

Menguji fungsi `CBREngine.fuzzy_check_temperature` pada batas-batas kritis.

- **Kasus Uji:** Input Suhu **91°C** (Batas antara Dingin dan Ideal).
- **Hasil:** Sistem menghasilkan keanggotaan ganda:
  - `LOW (Dingin)`: 0.5
  - `IDEAL`: 0.5
- **Analisis:** Ini membuktikan sistem tidak menggunakan logika biner kaku (`IF < 92 THEN COLD`). Sistem mengenali nuansa bahwa 91°C berada tepat di tengah-tengah, memungkinkan pengambilan keputusan yang lebih halus.

### 3.3. Evaluasi Weighted CBR

Menguji algoritma _Weighted Nearest Neighbor_.

- **Skenario:** User menginginkan `Fruity` (Bobot 1.0) dan `Nutty` (Bobot 1.0). Database memiliki kopi yang hanya `Fruity`.
- **Hasil:** Skor kemiripan terhitung **50%** (1 dari 2 bobot terpenuhi).
- **Analisis:** Algoritma berhasil menangani pencocokan parsial, yang merupakan inti dari sistem rekomendasi yang efektif.

---

## 4. Hasil Pengujian Integrasi (Skenario End-to-End)

Pengujian ini memvalidasi perilaku agen-agen cerdas (`Doctor`, `Sommelier`, `Brewer`) saat berinteraksi melalui _Blackboard_.

### Skenario 1: The Doctor - Diagnosis Multi-Faktor & Context Aware

- **Input:** _"My V60 coffee tastes sour."_ $\rightarrow$ _"Ethiopia"_ $\rightarrow$ _"V60"_ $\rightarrow$ _"Grind is chunky"_ (User: Yes) $\rightarrow$ _"Temp is 85C"_ (User: Input Angka).
- **Hasil Observasi:**
  1.  **Context Gathering:** Sistem berhasil menyimpan "Ethiopia" dan "V60" di Blackboard.
  2.  **Recipe Lookup:** Sistem menemukan resep ideal dan menggunakannya untuk memodifikasi pertanyaan (misal: _"Resep idealnya 96C, apakah punya Anda lebih rendah?"_).
  3.  **Fuzzy Logic Trigger:** Saat user memasukkan "85C", logika Fuzzy aktif, menghitung skor `LOW`, dan otomatis memvonis masalah suhu tanpa perlu konfirmasi manual user.
  4.  **Full Evidence:** Sistem tidak berhenti pada masalah gilingan, tapi terus mendeteksi masalah suhu.
- **Status:** **PASS**. Menunjukkan kemampuan diagnosis yang setara dengan pakar manusia (holistik).

### Skenario 2: The Brewer - True CBR (Analogy Reasoning)

- **Input:** _"I want to brew Java Frinsa"_ (Biji kopi tidak ada di database).
- **Input Atribut:** _"It is light roast and natural process."_
- **Hasil Observasi:**
  1.  **Handling Unknown:** Sistem tidak error, melainkan masuk state `CBR_GATHER_ATTRS`.
  2.  **Nearest Neighbor:** Sistem menghitung jarak dan menemukan tetangga terdekat, misalnya "Ethiopia Sidamo Guji" (Similarity: 70%).
  3.  **Adaptasi:** Sistem menyajikan resep Ethiopia tersebut sebagai referensi adaptasi untuk Java Frinsa.
- **Status:** **PASS**. Membuktikan sistem memiliki _Robustness_ tinggi melalui penalaran analogi.

### Skenario 3: The Brewer - Smart Fallback

- **Input:** _"Costa Rica Tarrazu"_ $\rightarrow$ _"I don't know"_ (saat ditanya metode).
- **Hasil Observasi:**
  1.  **Detection:** Sistem mendeteksi ketidaktahuan pengguna.
  2.  **Action:** Sistem secara proaktif memilihkan metode yang paling sesuai (misal: French Press) dan langsung memberikan resepnya, disertai penjelasan edukatif.
- **Status:** **PASS**. Meningkatkan _User Experience_ (UX) secara signifikan bagi pemula.

---

## 5. Analisis Komparatif (V1 vs. V2)

Tabel berikut merangkum peningkatan teknis dari prototipe awal (V1) ke versi final (V2).

| Aspek                   | BaristaBox V1 (Awal)                        | BaristaBox V2 (Final)                 | Analisis Peningkatan                                                                                                                                      |
| :---------------------- | :------------------------------------------ | :------------------------------------ | :-------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Arsitektur**          | Prosedural / Monolitik                      | **Blackboard Architecture**           | V2 memisahkan logika agen dari memori. Memungkinkan kolaborasi kompleks (Sinergi Sommelier $\rightarrow$ Brewer) dan _state management_ yang persisten.   |
| **Logika Diagnosis**    | _First-Found_ (Berhenti di masalah pertama) | **Evidence Gathering** (Multi-Faktor) | V2 jauh lebih akurat karena mengumpulkan seluruh bukti sebelum menyimpulkan, mencerminkan diagnosis dunia nyata yang seringkali kompleks.                 |
| **Fleksibilitas Input** | _Exact Matching_ (Kaku)                     | **Fuzzy & Semantic**                  | V1 gagal jika user tidak menjawab "Yes/No". V2 menggunakan LLM dan Fuzzy Logic untuk memahami angka ("85 derajat") dan nuansa bahasa ("Mungkin").         |
| **Penanganan Data**     | Statis (Gagal jika data tidak ada)          | **CBR Analogy**                       | V1 menyerah pada biji kopi baru. V2 menggunakan CBR untuk mencari analogi terdekat, membuat sistem tetap berguna meskipun data tidak lengkap.             |
| **Kualitas Output**     | _Unstructured_ (LLM Hallucination)          | **Strict SOP**                        | V2 menggunakan prompt yang ketat dan data terstruktur untuk menghasilkan panduan teknis yang bersih, menghilangkan jawaban yang bertele-tele (_yapping_). |

## 6. Kesimpulan Evaluasi

Berdasarkan hasil pengujian di atas, BaristaBox V2 dinyatakan telah memenuhi standar **Sistem Pakar Hibrida**. Sistem ini berhasil mengatasi keterbatasan sistem pakar tradisional (kekakuan aturan) dengan integrasi AI modern (Fuzzy, NLP), sekaligus menghindari kelemahan AI generatif murni (halusinasi) dengan kontrol logika berbasis aturan yang ketat.
