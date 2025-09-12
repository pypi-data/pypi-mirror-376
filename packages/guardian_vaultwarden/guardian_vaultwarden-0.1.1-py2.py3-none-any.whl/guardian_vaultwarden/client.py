import sys
import json
import requests

from . import crypto

class Client:

  def __init__(self, uri, email, password, client_id, client_secret):
    self.uri = uri
    self.email = email
    self.password = password
    self.client_id = client_id
    self.client_secret = client_secret


  def login(self):
    response = requests.post(
      f"{self.uri}/identity/connect/token",
      data={
        'grant_type': 'client_credentials',
        'client_id': self.client_id,
        'client_secret': self.client_secret,
        'device_identifier': 'guardian',
        'device_name': 'guardian',
        # 21 for "SDK", see https://github.com/bitwarden/server/blob/master/src/Core/Enums/DeviceType.cs
        'device_type': 21,
        'scope': 'api'
      }
    )

    if (response.status_code != 200):
      raise RuntimeError("Unable to authenticate to Vaultwarden. "\
            "Check CLIENT_ID and CLIENT_SECRET environment variables.")

    body = response.json()

    self.access_token = body['access_token']
    self.master_key = crypto.make_master_key(salt=self.email, password=self.password, iterations=600000)
    self.key = crypto.decrypt(body['Key'], self.master_key)


  def cipher(self, cipher_id: str):
    response = requests.get(
      f"{self.uri}/api/ciphers/{cipher_id}",
      headers={'Authorization': f"Bearer {self.access_token}"},
    )

    if (response.status_code != 200):
      raise RuntimeError(f"Cannot find cipher {cipher_id}.")

    body = response.json()
    decoded_body = self.decode_json(body)
    return decoded_body


  def decode_json(self, data):
    if isinstance(data, dict):
      for key, value in data.items():
        data[key] = self.decode_json(value)
      return data
    elif isinstance(data, list):
      for idx, item in enumerate(data):
        data[idx] = self.decode_json(item)
      return data
    elif isinstance(data, str):
      if data[:2] == '2.':
        return crypto.decrypt(data, self.key).decode('utf-8')
      else:
        return data
    else:
      return data
