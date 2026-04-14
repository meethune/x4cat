---
title: "Signature Files"
layout: default
parent: "X4 Modding Reference"
nav_order: 16
---

# Signature Files

X4 uses RSA signature files for DRM/integrity verification of official content.

## Format

- Every official file has a corresponding `.sig` file
- Signature catalogs: `*_sig.cat`/`*_sig.dat` contain `.sig` entries for catalog-packed files
- Each `.sig` file is exactly **1024 bytes** (8192-bit RSA signature)
- Signed with Egosoft's private key, verified with their public key embedded in the game

## Impact on mods

- Mods **cannot and do not need to** generate signature files
- The game logs `Could not find signature file` for unsigned mod files -- this is **expected and harmless**
- The error appears once per session, then is suppressed (or use `fileio` debug filter for all)
- This does not affect mod functionality in any way

---
