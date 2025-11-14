# Encrypted Topic Chat — README

> A compact, step‑by‑step guide for the Flet-based encrypted topic chat demo.

---

## What this is

A small proof‑of‑concept chat app built with **Flet** that demonstrates topic-based publish/subscribe messaging with **end-to-end style encryption**. Users type a _codeword_ (passphrase) to encrypt outgoing messages and must use the same passphrase to decrypt incoming messages. The app intentionally keeps encryption simple for demonstration.

## Example of sending a message.

![alt text](<images/Screenshot 2025-11-14 181922_Anwar.png>)

## Example of correct decryption and successful message display because John and Anwar have same codeword

![alt text](<images/Screenshot 2025-11-14 182026_John.png>)

## Example of decryption failure (wrong passphrase) because Smith is using different codeword.

![alt text](<images/Screenshot 2025-11-14 182126_Smith.png>)

---

## Requirements

- Python 3.9+
- `flet` package (tested with recent Flet releases)

Install dependencies:

```bash
python -m pip install --upgrade pip
pip install flet
```

---

## Quick start — run locally (step by step)

1. **Open a terminal** in the project folder (the folder that contains the script).

2. **Create a virtual environment** (recommended):

   ```bash
   python -m venv .venv
   source .venv/bin/activate    # macOS / Linux
   .venv\Scripts\activate      # Windows
   ```

3. **Install dependencies**:

   ```bash
   pip install flet
   ```

4. **Run the app**:

   ```bash
   flet run Flet_Encrypted_Chat.py --web
   ```

   Flet will start a local web UI (usually printed as `http://127.0.0.1:####`). Open that URL in your browser.

5. **Use the UI** (step‑by‑step):

   1. Enter a **Display name** (for example `Anwar`).
   2. Type a **Codeword** (passphrase). Everybody who wants to read your messages must use the _same_ codeword. You can toggle **Mask passphrase** to hide the passphrase input.
   3. Pick an existing **Topic** from the dropdown (e.g. `developer`) or type a **New topic**.
   4. Click **Subscribe** to start receiving messages for that topic. Subscriptions appear in the `Subscribed:` label.
   5. Type a message into `Type your message...` and click **Send**. The message is encrypted with the current codeword and published to all subscribers on the topic.
   6. If other subscribers are using the same passphrase they will see the decrypted text. If their passphrase is wrong, they will see a locked placeholder message (🔒). See the screenshots for examples.

---

## UX / Behavior notes

- Messages are published as JSON objects: `{ "user": "<display-name>", "payload": "<encrypted-string>", "ts": "<iso-timestamp>" }`.
- If a subscriber receives a message but cannot decrypt it with their current passphrase, the app intentionally does **not** reveal plaintext — it shows a locked placeholder and a small `[raw]` hint.
- The local page shows your sent message immediately by decrypting the ciphertext you just created (local echo).

---

## Troubleshooting

- **App doesn’t open in browser**: Confirm the local address printed by Flet and try the exact URL. Check firewall settings and that the chosen port is free.
- **Decrypt failures**: If you see `🔒 Encrypted message — wrong passphrase or corrupted payload` (see `Smith.png`), verify that every party typed the same codeword (and there are no stray spaces). If the message sender used a different passphrase you will not be able to decrypt.
- **Encrypt failed**: If encryption raises an exception, the app displays a snack bar with the error. Typical causes: invalid passphrase type (should be string) or library issues.
