# EncFilex (EFX) v1.1

🔒 **EncFilex (EFX)** is a modern file encryption system with double layers:
1. Base64 Encoding
2. AES-256-GCM
3. XChaCha20-Poly1305

Designed so that **any file** (text, image, video, document) can be securely encrypted and only opened with the correct password.

---

## ✨ Features
- 🔐 **AES-256-GCM** for symmetric security
- ⚡ **XChaCha20-Poly1305** for extra security & long nonce
- 📦 Supports **large binary files** (image, video, doc, etc.)
- 🛡️ Password-based key derivation using **Argon2**
- 🎯 Usable via **Python API** or **Command Line (CLI)**

---

## 📦 Installation
Install from PyPI:

```bash
pip install encfilex
```

---

## 🚀 Usage

### 1. API (in Python)

```python
from EFX import encrypt_file, decrypt_file

# Encrypt
encrypt_file("secret.png", "secret.efx", "super-password")

# Decrypt
decrypt_file("secret.efx", "recovered.png", "super-password")
```

### 2. Command Line (CLI)
After installation, the encfilex command is available.

#### Encrypt file
```bash
efx encrypt secret.png secret.efx --password super-password
```

#### Decrypt file
```bash
efx decrypt secret.efx secret.png --password super-password
```

---

## ⚠️ Notes
- Don't forget to keep your password safe.
- If lost, files cannot be recovered (no backdoor).
- The size of the encrypted file can be about 30% larger than the original (due to metadata + Base64).
- Python 3.9+ is recommended.

---

## 📜 License
Released under the MIT license.  
Made with LOVE by Azzam Jauzi (AkzDev).