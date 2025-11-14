import json
import datetime
import flet as ft
from flet.security import encrypt, decrypt


# NOTE: This is a demo/proof-of-concept. For production use consider stronger


def main(page: ft.Page):
    page.title = "Flet — Encrypted Topic Chat"
    page.vertical_alignment = ft.MainAxisAlignment.START

    # --- App state ---
    available_topics = ["general", "developer", "random", "Gen Z"]
    subscriptions = set()  # topics this page is subscribed to

    # --- UI controls ---
    username = ft.TextField(label="Display name", value="Anwar", width=220)

    # The user enters the passphrase as text (per your request). You may toggle masking.
    passphrase = ft.TextField(
        label="Codeword (used to encrypt/decrypt)", value="", width=360)
    mask_toggle = ft.Checkbox(label="Mask passphrase", value=False)

    def on_mask_change(e):
        # change to password field when masked
        passphrase.password = e.control.value
        page.update()

    mask_toggle.on_change = on_mask_change

    topic_dropdown = ft.Dropdown(
        label="Topic",
        width=220,
        options=[ft.dropdown.Option(t) for t in available_topics],
        value=available_topics[0],
    )

    new_topic_field = ft.TextField(label="New topic (optional)", width=220)

    subscribe_button = ft.ElevatedButton("Subscribe", disabled=False)
    unsubscribe_button = ft.ElevatedButton("Unsubscribe", disabled=False)

    messages = ft.Column(expand=True)

    message_field = ft.TextField(hint_text="Type your message...", expand=True)
    send_button = ft.ElevatedButton("Send")

    subscribed_label = ft.Text("Subscribed: —")

    # keep a reference to the topic handler so we can unsubscribe if needed
    topic_handlers = {}

    # --- Helpers ---
    def _add_message_row(topic, sender, decrypted_text, encrypted_payload=None, ok=True):
        # timestamp
        ts = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
        if ok:
            row = ft.Container(
                content=ft.Row(controls=[
                    ft.Text(f"[{ts}] ", size=9),
                    ft.Text(f"({topic}) ", size=9, weight=ft.FontWeight.BOLD),
                    ft.Text(f"{sender}: ", size=10, weight=ft.FontWeight.BOLD),
                    ft.Text(decrypted_text, size=10),
                ]),
                padding=ft.padding.only(bottom=6)
            )
        else:
            # failed decryption - show placeholder
            row = ft.Container(
                content=ft.Row(controls=[
                    ft.Text(f"[{ts}] ", size=9),
                    ft.Text(f"({topic}) ", size=9, weight=ft.FontWeight.BOLD),
                    ft.Text(f"{sender}: ", size=10, weight=ft.FontWeight.BOLD),
                    ft.Text(
                        "🔒 Encrypted message — wrong passphrase or corrupted payload", size=10, italic=True),
                    ft.Text(" [raw]", size=8, color=ft.Colors.GREY)
                ]),
                padding=ft.padding.only(bottom=6)
            )
        messages.controls.append(row)
        page.update()

    # --- PubSub handlers ---
    def make_topic_handler(sub_topic):
        # returned function signature matches Flet's subscribe_topic: (topic, message)
        def _on_message(topic, message):
            # message is whatever was sent through pubsub. We expect a dict with keys:
            # {'user': sender, 'payload': encrypted_base64_string, 'ts': '...'}
            try:
                payload = message.get("payload") if isinstance(
                    message, dict) else None
                sender = message.get("user") if isinstance(
                    message, dict) else str(message)
                if payload is None:
                    # message is not in our expected format - display raw
                    _add_message_row(topic, sender, str(message), ok=True)
                    return

                # try to decrypt using the CURRENT passphrase value provided by this user
                # (users must type the same passphrase to successfully decrypt)
                try:
                    plain = decrypt(payload, passphrase.value)
                    # decrypt returns str
                    _add_message_row(topic, sender, plain,
                                     encrypted_payload=payload, ok=True)
                except Exception:
                    # wrong passphrase — we intentionally do NOT reveal plaintext
                    _add_message_row(topic, sender, "",
                                     encrypted_payload=payload, ok=False)
            except Exception as ex:
                # unexpected errors — show minimal info
                messages.controls.append(
                    ft.Text(f"Error processing message on {sub_topic}: {ex}"))
                page.update()

        return _on_message

    # --- Subscribe / Unsubscribe logic ---
    def subscribe_to_topic(e):
        t = new_topic_field.value.strip() or topic_dropdown.value
        if not t:
            page.snack_bar = ft.SnackBar(
                ft.Text("Choose or type a topic first"))
            page.snack_bar.open = True
            page.update()
            return

        if t in subscriptions:
            page.snack_bar = ft.SnackBar(
                ft.Text(f"Already subscribed to '{t}'"))
            page.snack_bar.open = True
            page.update()
            return

        handler = make_topic_handler(t)
        page.pubsub.subscribe_topic(t, handler)
        topic_handlers[t] = handler
        subscriptions.add(t)
        subscribed_label.value = "Subscribed: " + \
            ", ".join(sorted(subscriptions))
        page.snack_bar = ft.SnackBar(ft.Text(f"Subscribed to '{t}'"))
        page.snack_bar.open = True
        page.update()

    def unsubscribe_from_topic(e):
        t = topic_dropdown.value
        if t not in subscriptions:
            page.snack_bar = ft.SnackBar(ft.Text(f"Not subscribed to '{t}'"))
            page.snack_bar.open = True
            page.update()
            return

        # unsubscribe using the simple unsubscribe_topic API
        page.pubsub.unsubscribe_topic(t)
        handler = topic_handlers.pop(t, None)
        subscriptions.discard(t)
        subscribed_label.value = "Subscribed: " + \
            (", ".join(sorted(subscriptions)) if subscriptions else "—")
        page.snack_bar = ft.SnackBar(ft.Text(f"Unsubscribed from '{t}'"))
        page.snack_bar.open = True
        page.update()

    subscribe_button.on_click = subscribe_to_topic
    unsubscribe_button.on_click = unsubscribe_from_topic

    # --- Send logic ---
    def send_message(e):
        t = new_topic_field.value.strip() or topic_dropdown.value
        if not t:
            page.snack_bar = ft.SnackBar(
                ft.Text("Choose or type a topic first"))
            page.snack_bar.open = True
            page.update()
            return

        if not message_field.value:
            return

        # encrypt the plaintext using the user's passphrase
        try:
            ciphertext = encrypt(message_field.value, passphrase.value)
        except Exception as ex:
            page.snack_bar = ft.SnackBar(ft.Text(f"Encrypt failed: {ex}"))
            page.snack_bar.open = True
            page.update()
            return

        # message object to send — can be any JSON-serializable structure
        msg = {
            "user": username.value,
            "payload": ciphertext,
            "ts": datetime.datetime.utcnow().isoformat(),
        }

        # publish to all subscribers on this topic
        page.pubsub.send_all_on_topic(t, msg)

        # also show locally (we can decrypt since we just encrypted it)
        try:
            plain = decrypt(ciphertext, passphrase.value)
            _add_message_row(t, username.value + " (you)", plain, ok=True)
        except Exception:
            _add_message_row(t, username.value + " (you)", "", ok=False)

        message_field.value = ""
        page.update()

    send_button.on_click = send_message

    # --- Cleanup when page close ---
    def client_exited(e):
        try:
            page.pubsub.unsubscribe_all()
        except Exception:
            pass

    page.on_close = client_exited

    # --- Layout ---
    controls_top = ft.Row(controls=[
        username,
        ft.Column(controls=[passphrase, mask_toggle]),
        ft.Column(controls=[topic_dropdown, new_topic_field,
                  ft.Row([subscribe_button, unsubscribe_button])]),
    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

    controls_bottom = ft.Row(
        controls=[message_field, send_button], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

    page.add(
        ft.Column(controls=[
            ft.Text("Encrypted Chat", style="headlineSmall"),
            controls_top,
            ft.Divider(),
            subscribed_label,
            ft.Container(content=messages, expand=True, padding=10,
                         border=ft.border.all(1, ft.Colors.AMBER_100)),
            controls_bottom,
        ], expand=True)
    )


if __name__ == "__main__":
    ft.app(target=main)
