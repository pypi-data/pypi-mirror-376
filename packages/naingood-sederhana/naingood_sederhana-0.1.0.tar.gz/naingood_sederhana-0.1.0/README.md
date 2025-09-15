# Sederhana

Library Python sederhana sebagai template untuk memulai membuat package.

## Fitur

- add(a, b): penjumlahan dua angka
- factorial(n): faktorial bilangan bulat non-negatif

## Struktur Proyek

```
.
├─ pyproject.toml
├─ README.md
├─ src/
│  └─ sederhana/
│     ├─ __init__.py
│     └─ mathutils.py
└─ tests/
   └─ test_mathutils.py
```

## Pengembangan Lokal

1. Buat virtualenv (opsional tapi disarankan)
2. Instal editable:

```
pip install -e .
```

3. Jalankan test (membutuhkan `pytest`):

```
pytest -q
```

## Build Rilis

Untuk membangun wheel dan sdist (membutuhkan paket `build`):

```
pip install build
python -m build
```

Artefak akan tersedia di folder `dist/`.

## Contoh Penggunaan

```python
from sederhana import add, factorial

print(add(2, 3))       # 5
print(factorial(5))    # 120
```

## Lisensi

MIT
