# Dashboard Sawit Indonesia — "Dari Kebun ke Devisa" (2010–2023)

Dashboard interaktif Streamlit untuk Tugas Besar 2 IF4061 Visualisasi Data.
Tema: perjalanan sawit dari provinsi (per jenis kepemilikan) hingga menjadi
ekspor & konsumsi domestik.

## Cara menjalankan (lokal)

```bash
pip install -r requirements.txt
streamlit run app.py
```
Buka http://localhost:8501 di browser.

## Struktur

```
app.py            # dashboard utama (5 KPI + 5 visualisasi + filter global)
data_loader.py    # loading & transformasi data (cached)
data/             # CSV induk + GeoJSON provinsi
data/processed/   # CSV turunan siap pakai
requirements.txt
```

## Visualisasi
1. KPI Cards — luas, produksi, produktivitas, nilai ekspor, jumlah provinsi
2. Peta Choropleth — distribusi produksi per provinsi
3. Donut — komposisi kepemilikan (PR/PBS/PBN)
4. Tren Produksi — garis historis 2010–2023
5. Bubble — efisiensi provinsi (X=luas, Y=produksi, ukuran=pangsa nasional)
6. Sankey — aliran kepemilikan → provinsi → nasional → ekspor/domestik

## Catatan data
- Produksi & kepemilikan: Outlook Kelapa Sawit (Pusdatin Kementan)
- Ekspor (CPO): Pusdatin Kementan; konsumsi domestik = produksi − ekspor
- Negara tujuan ekspor (BPS, 2012–2024): untuk lapis Sankey lanjutan (menyusul)


## Regenerasi data turunan

CSV di `data/processed/` dihasilkan dari CSV induk oleh script:

```bash
python scripts/preprocess_palm_oil.py
```

Script ini menghitung produktivitas, pangsa produksi nasional, tren YoY,
dan komposisi kepemilikan, sekaligus memvalidasi bahwa total produksi
per provinsi konsisten dengan total nasional per tahun.

## Deploy publik (Streamlit Community Cloud)
1. Push folder ini ke repo GitHub publik.
2. Buka share.streamlit.io, hubungkan repo, pilih `app.py`.
3. Dashboard akan dapat URL publik tanpa login.
