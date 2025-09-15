
# Maskify

`maskify` is a Python module designed to efficiently mask sensitive columns in large CSV / DAT files using character-level substitution. It leverages **Polars** for high-performance data manipulation and provides a memory-efficient way to process large files in chunks.

## 🚀 Features

- Process large CSV / DAT files in chunks without consuming excessive memory.
- Mask specified columns by substituting lowercase letters, uppercase letters, and digits with customizable cipher mappings.
- Skip masking for NULL, "NA" (case-insensitive), or empty values.
- Simple API for flexible integration into data pipelines.

## ✅ Installation

Install `maskify` from PyPI:

```bash
pip install maskify
```

## 🛠️ Usage

### 1️⃣ Generate Cipher Maps

Use `create_cipher_maps_letters_digits()` to generate random mappings for lowercase letters, uppercase letters, and digits.

```python
from maskify import create_cipher_maps_letters_digits

cipher_maps = create_cipher_maps_letters_digits()
letters_lower_map, letters_upper_map, digits_map = cipher_maps
```

### 2️⃣ Process and Mask Data

Use `process_maskify()` to mask specified columns in a CSV / DAT file and save the masked output.

```python
from maskify import process_maskify

output_file = process_maskify(
    input_file='data/input.csv',
    separator=',',
    columns_to_mask=['name', 'id'],
    enCipher=(letters_lower_map, letters_upper_map, digits_map),
    output_file='data/output_masked.csv'
)

print(f"Masked file saved at: {output_file}")
```


## ⚠️ License

Copyright 2025 Vikas Bhaskar Vooradi

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

<br>

<div align="center">

## 💖 **Support This Project!**


**Maskify** is **completely free** for everyone! 🎉  <br>
If you find it useful and want to support its development, you can buy me a coffee ☕. <br> Your contributions help keep the project updated and maintained.

### **Click the link below to contribute:**
[![Buy Me a Coffee](https://img.shields.io/badge/☕-Buy%20Me%20a%20Coffee-FFDD00?style=for-the-badge&logo=buy-me-a-coffee&logoColor=black)](https://www.buymeacoffee.com/vikasvooradi)

**Thank you for supporting open-source!** 🎉  
Every coffee helps keep the project alive and growing!  
Built with ❤️ using Python and Polars
</div>  



