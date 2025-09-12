<div align="center">
  <h1>🛡️Guardian🪽</h1>
  <h3>Vaultwarden Ciphers API Client</h3>
</div>

## Introduction

🛡️Guardian🪽 is a Vaultwarden client in Python which lets you to retrieve and decrypt
your ciphers (items in the vault).

## Usage

Install it with pip:

```bash
pip install guardian_vaultwarden
```

Inside your code do:

```python
import guardian_vaultwarden

vault = guardian_vaultwarden.Client(uri, email, password, client_id, client_secret)
# Client id and secret are available in the Vaultwarden webapp, under Settings ->
# Security -> Keys.

vault.login()
cipher = valut.cipher(cipher_id) # UUID of the cipher.

# Returns a decrypted dict with cipher information, like:
#
# {
#   "name": "MY_CIPHER",
#   "login": {
#     "username": "email@email.com",
#     "password": "mypass",
#     ...
#   },
#   ...
# }
```
