<div align="center">

# WanaKit

**Python malware builder for Windows.** Encrypted payloads, real C2 panel, fake ransomware.

[![Python](https://img.shields.io/badge/python-3.12-3776ab?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![Platform](https://img.shields.io/badge/platform-windows-0078d7?style=flat-square&logo=windows&logoColor=white)](#requirements)
[![Crypto](https://img.shields.io/badge/crypto-AES--256--GCM-a371f7?style=flat-square)](#how-the-packing-works)
[![License](https://img.shields.io/badge/license-MIT-3fb950?style=flat-square)](#license)

[Website](docs/index.html) · [Quickstart](#quickstart) · [Commands](#commands) · [FAQ](#faq)

</div>

---

> Educational malware. Not a commercial RAT — no persistence in kernel, no proxy, no privilege escalation. It does what a hobby RAT needs to do and stays readable.

## What it is

WanaKit builds a Windows EXE from a Python payload and gives you a Tk control panel to drive it.

The payload source is assembled, identifiers are mangled, the bytecode is compiled with `optimize=2`, marshalled, zlib'd and AES-256-GCM encrypted. The EXE ships only a stub plus ciphertext — no `.py` files, no readable strings, no plaintext to grep.
