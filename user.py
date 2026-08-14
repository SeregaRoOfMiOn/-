import email
import imaplib
import os
import threading
import time
import tkinter as tk
from tkinter import messagebox, scrolledtext, simpledialog
import requests

# Настройки IMAP
imap_server = "imap.mail.ru"
email_user = "boot_mass@mail.ru"
email_pass = "gJCRqYy58dwtcjjhW4OI"

body = ""

try:
  mail = imaplib.IMAP4_SSL(imap_server)
  mail.login(email_user, email_pass)
  mail.select("INBOX")

  status, messages = mail.search(None, "ALL")
  id_list = []
  if status == "OK" and messages:
    for item in messages:
      if isinstance(item, bytes):
        id_list.extend(item.split())
      elif hasattr(item, "__iter__"):
        for sub in item:
          if isinstance(sub, bytes):
            id_list.extend(sub.split())

  if id_list:
    latest_id = id_list[-1]
    res, msg_data = mail.fetch(latest_id, "(RFC822)")
    for part in msg_data:
      if isinstance(part, tuple) and len(part) > 1:
        raw_bytes = part[1]
        if isinstance(raw_bytes, bytes):
          msg = email.message_from_bytes(raw_bytes)
          if msg.is_multipart():
            for sub_part in msg.walk():
              if sub_part.get_content_type() == "text/plain":
                charset = sub_part.get_content_charset() or "utf-8"
                body = sub_part.get_payload(decode=True).decode(
                    charset, errors="ignore"
                )
                break
          else:
            charset = msg.get_content_charset() or "utf-8"
            body = msg.get_payload(decode=True).decode(charset, errors="ignore")
          break
  mail.logout()
except Exception as e:
  print(f"Ошибка почты: {e}")

server_url = body.strip()
running = True
last_printed_history = ""
name = "Аноним"


def receive_messages():
  global running, last_printed_history
  while running:
    try:
      if server_url:
        response = requests.get(server_url)
        if response.status_code == 200:
          current_history = response.text
          if current_history != last_printed_history:
            chat_area.config(state=tk.NORMAL)
            chat_area.delete("1.0", tk.END)
            chat_area.insert(tk.END, current_history)
            chat_area.config(state=tk.DISABLED)
            chat_area.see(tk.END)
            last_printed_history = current_history
    except Exception:
      pass
    time.sleep(2)


def send_message(event=None):
  message = msg_entry.get().strip()
  if not message or not server_url:
    return

  full_message = f"{name}: {message}"
  try:
    response = requests.post(server_url, data=full_message.encode("utf-8"))
    if response.status_code == 200:
      msg_entry.delete(0, tk.END)
  except Exception as e:
    messagebox.showerror("Ошибка сети", str(e))


if server_url:
  # Создаем скрытое корневое окно, чтобы поверх него показать диалог ввода имени
  root = tk.Tk()
  root.withdraw()

  # Запрашиваем имя через всплывающее окно
  user_input = simpledialog.askstring(
      "Вход", "Введите ваше имя:", parent=root
  )
  if user_input and user_input.strip():
    name = user_input.strip()

  # Возвращаем/настраиваем главное окно мессенджера
  root.deiconify()
  root.title(f"Light_gram Messenger — {name}")
  root.geometry("450x550")

  chat_area = scrolledtext.ScrolledText(root, wrap=tk.WORD, state=tk.DISABLED)
  chat_area.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

  bottom_frame = tk.Frame(root)
  bottom_frame.pack(padx=10, pady=10, fill=tk.X)

  msg_entry = tk.Entry(bottom_frame, font=("Arial", 12))
  msg_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
  msg_entry.bind("<Return>", send_message)

  send_btn = tk.Button(
      bottom_frame, text="Отправить", command=send_message, bg="#4CAF50", fg="white"
  )
  send_btn.pack(side=tk.RIGHT)

  reader_thread = threading.Thread(target=receive_messages, daemon=True)
  reader_thread.start()

  root.mainloop()
  running = False
else:
  print("[Система]: Не удалось получить URL сервера из письма.")
