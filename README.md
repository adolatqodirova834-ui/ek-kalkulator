# EK kalkulyatori (elektrokoagulyatsiya)

Neftni qayta ishlash zavodi oqova suvlarini alyuminiy elektrodlar bilan elektrokoagulyatsiya (EK)
usulida tozalash bo'yicha laboratoriya tajribalari uchun veb-kalkulyator. Python va Streamlit'da yozilgan.

## Imkoniyatlar

- **Asosiy kalkulyator**: erigan Al massasi, koagulyant dozasi, tok zichligi, zaryad yuklamasi, energiya sarfi,
  elektrod sarfi, tozalash samaradorligi, solishtirma energiya, ekspluatatsiya xarajati, anod yemirilishi, H₂ hajmi.
- **Davriy va uzluksiz rejim**: uzluksiz rejimda vaqt o'rniga HRT = V/Q ishlatiladi.
- **Kinetika**: psevdo-birinchi va psevdo-ikkinchi tartib modellari, k, R², t½, maqsadli samaradorlik uchun
  kerakli vaqt, energiya va Al dozasi.
- **Eksport**: natijalar Excel (.xlsx) va CSV, grafiklar PNG formatida.
- **Tekshiruv**: nol va manfiy qiymatlar rad etiladi; manba chegarasi (30 V / 10 A), tok zichligi, φ va C > C₀
  bo'yicha ogohlantirishlar chiqadi.

## Eng oson yo'l: `EK_kalkulyator.html`

`EK_kalkulyator.html` faylini ikki marta bosing — kalkulyator brauzerda ochiladi. Hech narsa o'rnatish shart emas,
internet kerak emas, Python kerak emas. Eski kompyuter va brauzerlarda (masalan, Windows 7) ham ishlaydi.
Ichida asosiy kalkulyator, kinetika, grafiklar (PNG) va Excel/CSV eksport bor; hisoblar Streamlit versiyasi va
Excel prototipi bilan bir xil. Kiritilgan qiymatlar shu brauzerda saqlanib qoladi.

Alohida oynali ilova sifatida ochish (Chrome): faylni Chrome'da oching → menyu (⋮) → **Boshqa vositalar** →
**Yorliq yaratish** → **Oyna sifatida ochish** ni belgilang. Ish stolida logotipli yorliq paydo bo'ladi.

Fayl `standalone/app.html` dan `python standalone/build.py` buyrug'i bilan yig'iladi.

## Streamlit versiyasi: ikki marta bosish bilan

Kompyuterda **Python 3.11 yoki undan yangi** versiya o'rnatilgan bo'lishi kerak
(https://www.python.org/downloads/ — Windows'da o'rnatishda "Add python.exe to PATH" belgisini yoqing).

| Tizim | Fayl |
|---|---|
| Windows | `Ishga_tushirish.bat` |
| macOS | `Ishga_tushirish.command` |
| Linux | `Ishga_tushirish.sh` |

Faylni ikki marta bosing. Birinchi safar kutubxonalar avtomatik o'rnatiladi (bir necha daqiqa, internet kerak),
keyin kalkulyator brauzerda ochiladi. Keyingi safar darhol ishga tushadi va internet talab qilmaydi.
To'xtatish uchun ochilgan qora oynani yoping.

macOS birinchi safar faylni bloklasa: faylni o'ng tugma bilan bosib, **Open** ni tanlang.

Quyidagi bo'limlar qo'lda o'rnatishni xohlovchilar uchun.

## O'rnatish

Python 3.11 yoki undan yangi versiya kerak.

```bash
cd ek_kalkulyator
python -m venv .venv
```

Virtual muhitni yoqish (Linux / macOS):

```bash
source .venv/bin/activate
```

Windows:

```bash
.venv\Scripts\activate
```

Kutubxonalarni o'rnatish:

```bash
pip install -r requirements.txt
```

## Ishga tushirish

```bash
streamlit run app.py
```

Brauzerda `http://localhost:8501` manzili ochiladi.

## Foydalanish

1. Chap panelda jarayon parametrlarini kiriting: material, rejim, I, U, t (yoki Q), V, A, φ va narxlar.
2. **Asosiy kalkulyator** sahifasida C₀ va C ni kiriting. Natijalar darhol yangilanadi.
3. **Kinetika** sahifasida jadvalga vaqt va KXT qiymatlarini kiriting yoki CSV yuklang.
   - CSV'da birinchi ustun vaqt (min), ikkinchisi KXT (mg/L). Sarlavha qatori bo'lishi mumkin.
     Ajratuvchi sifatida `,` `;` yoki tabulyatsiya, o'nlik belgi sifatida nuqta yoki vergul qabul qilinadi.
   - t = 0 dagi qiymat C₀ deb olinadi. Kamida 3 ta nuqta kerak.
4. Natijalarni **Excel** yoki **CSV** tugmalari bilan yuklab oling.

### Grafiklarni PNG qilib saqlash

- Har bir grafik ostidagi **"PNG tayyorlash"** tugmasini yoqing va faylni yuklab oling (3600×2240 px,
  12 dyuym kenglikda 300 dpi). Buning uchun `kaleido` va Chrome/Chromium kerak. Chrome bo'lmasa:

  ```bash
  plotly_get_chrome
  ```

- Yoki grafikning o'ng yuqori burchagidagi kamera (📷) tugmasini bosing. Bu usul qo'shimcha dastur talab qilmaydi.

## Testlar

```bash
python -m pytest -q
```

Tekshiruv misollari (testlarda bor):

| Kirish | Kutilgan natija |
|---|---|
| I = 1 A, U = 10 V, t = 30 min, V = 1 L, φ = 1 | m ≈ 0.1678 g, doza ≈ 167.8 mg/L, E = 5.00 kWh/m³, H₂ ≈ 209.1 mL |
| t = 0…60 min, KXT = 1500, 1120, 820, 600, 450, 340, 260 mg/L | k₁ ≈ 0.02944 1/min, R² ≈ 0.9993, 80 % uchun t ≈ 54.7 min |

### Excel prototipi bilan tenglik

`EK_kalkulyator_Al.xlsx` loyiha papkasida turadi va `tests/test_excel_parity.py` uni har safar o'qiydi:

- Excel'ning o'zi saqlagan barcha natija kataklari (1-varaq B19:B29, Kinetika varag'i C4:I10 va D13:D24)
  dastur natijalari bilan 10⁻¹⁰ nisbiy aniqlikda solishtiriladi.
- Fayldagi formulalar boshqa kirish qiymatlari bilan ham qayta hisoblanib, dastur bilan taqqoslanadi.
- Ogohlantirish chegaralari Excel'dagi qizil katak qoidalari bilan bir xil ekani tekshiriladi.

Excel faylidagi formulani o'zgartirsangiz, bu test farqni darhol ko'rsatadi.

## Formulalar

F = 96 485 C/mol; Al uchun M = 26.98 g/mol, z = 3, ρ = 2.70 g/cm³.

| № | Kattalik | Formula |
|---|---|---|
| 1 | Erigan Al massasi, g | m = I·t[s]·M / (z·F) · φ |
| 2 | Koagulyant dozasi, mg/L | m·1000 / V |
| 3 | Tok zichligi, mA/cm² | I·1000 / A |
| 4 | Zaryad yuklamasi, C/L | I·t[s] / V |
| 5 | Energiya sarfi, kWh/m³ | U·I·t[soat] / V[L] |
| 6 | Elektrod sarfi, kg/m³ | m / V |
| 7 | Tozalash samaradorligi, % | (C₀ − C)/C₀·100 |
| 8 | Solishtirma energiya, kWh/kg KXT | E / ((C₀ − C)/1000) |
| 9 | Ekspluatatsiya xarajati, so'm/m³ | elektr narxi·E + Al narxi·ELC |
| 10 | Anod qalinligining kamayishi, mm | m / (ρ·A) · 10 |
| 11 | H₂ hajmi, mL (n.sh.) | I·t[s] / (2F) · 22414 |

Kinetika: ln(C₀/C) = k₁·t va 1/C − 1/C₀ = k₂·t. Qiyalik va R² erkin hadli chiziqli regressiya bilan
hisoblanadi (Excel'dagi `SLOPE` va `RSQ` kabi). t½ = ln2/k₁; maqsadli vaqt t = −ln(1 − R/100)/k₁.

Uzluksiz rejimda doza, zaryad, energiya va xarajat HRT bo'yicha, H₂ hajmi va anod yemirilishi esa
1 soatlik ish uchun hisoblanadi.

## Loyiha tuzilmasi

```
ek_kalkulyator/
├── app.py               # kirish nuqtasi, navigatsiya
├── views/               # sahifalar: kalkulyator.py, kinetika.py
├── ui/                  # sidebar.py (kirish maydonlari), charts.py (grafiklar)
├── ec_core/             # hisoblash mantiqi (Streamlit'ga bog'liq emas)
│   ├── materials.py     # materiallar lug'ati
│   ├── models.py        # Electrode, Reactor, Experiment
│   ├── kinetics.py      # kinetik tahlil
│   ├── validation.py    # tekshiruv va ogohlantirishlar
│   └── export.py        # jadvallar, Excel/CSV
├── tests/               # pytest testlari
└── EK_kalkulyator_Al.xlsx  # Excel prototipi (tenglik testi uchun)
```

## Yangi material qo'shish (masalan, Fe)

`ec_core/materials.py` faylidagi `MATERIALS` lug'atiga bitta qator qo'shing:

```python
"Fe": Material(symbol="Fe", name="Temir", M=55.845, z=2, rho=7.87),
```

Material interfeysdagi ro'yxatda avtomatik paydo bo'ladi. Fe uchun z qiymatini (2 yoki 3) o'z tajriba
sharoitingizga qarab tanlang.
