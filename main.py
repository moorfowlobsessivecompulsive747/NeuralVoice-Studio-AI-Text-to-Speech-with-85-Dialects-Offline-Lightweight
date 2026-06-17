import os
import asyncio
import random
import threading
import json
import shutil
from datetime import datetime
from tkinter import *
from tkinter import ttk, scrolledtext, messagebox, simpledialog
from telethon import TelegramClient
from telethon.errors import FloodWaitError, AuthKeyError, AuthKeyDuplicatedError
from telethon.tl.types import User, Chat, Channel
from telethon.tl.functions.contacts import GetContactsRequest

class TelegramSpamer:
    def __init__(self, root):
        self.root = root
        self.root.title("Telegram Рассыльщик - Стабильная версия")
        self.root.geometry("1200x1000")
        
        self.sessions_dir = "сессион"
        self.templates_dir = "шаблоны"
        self.backup_dir = "бэкапы_сессий"
        self.running = False
        self.stop_flag = False
        self.sent_chats = set()
        self.sent_contacts = set()
        self.current_client = None
        self.reconnect_attempts = 0
        self.is_reconnecting = False
        
        # Создаём папки
        for folder in [self.sessions_dir, self.templates_dir, self.backup_dir]:
            if not os.path.exists(folder):
                os.makedirs(folder)
        
        # API данные
        self.api_id = 31972424
        self.api_hash = "1da171f9f44ece6830bbb013aff34677"
        
        self.setup_ui()
        self.load_sessions_list()
        self.load_templates_list()
        self.load_api_settings()
    
    def setup_ui(self):
        # Основной контейнер с прокруткой
        main_canvas = Canvas(self.root)
        scrollbar = Scrollbar(self.root, orient="vertical", command=main_canvas.yview)
        self.scrollable_frame = Frame(main_canvas)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: main_canvas.configure(scrollregion=main_canvas.bbox("all"))
        )
        
        main_canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        main_canvas.configure(yscrollcommand=scrollbar.set)
        
        main_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        def _on_mousewheel(event):
            main_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        main_canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        main_frame = self.scrollable_frame
        
        # ===== БЛОК НАСТРОЕК API =====
        api_frame = LabelFrame(main_frame, text="🔐 API Настройки", font=("Arial", 11, "bold"), fg="red")
        api_frame.pack(fill=X, padx=10, pady=10)
        
        api_inner = Frame(api_frame)
        api_inner.pack(fill=X, padx=5, pady=5)
        
        Label(api_inner, text="API ID:").grid(row=0, column=0, padx=5, pady=2)
        self.api_id_entry = Entry(api_inner, width=15)
        self.api_id_entry.grid(row=0, column=1, padx=5, pady=2)
        self.api_id_entry.insert(0, str(self.api_id))
        
        Label(api_inner, text="API Hash:").grid(row=0, column=2, padx=5, pady=2)
        self.api_hash_entry = Entry(api_inner, width=35)
        self.api_hash_entry.grid(row=0, column=3, padx=5, pady=2)
        self.api_hash_entry.insert(0, self.api_hash)
        
        Button(api_inner, text="💾 Сохранить", command=self.save_api_settings, 
               bg="#4CAF50", fg="white").grid(row=0, column=4, padx=5, pady=2)
        
        # ===== БЛОК ШАБЛОНОВ =====
        template_frame = LabelFrame(main_frame, text="📁 Шаблоны", font=("Arial", 11, "bold"), fg="blue")
        template_frame.pack(fill=X, padx=10, pady=10)
        
        top_template_frame = Frame(template_frame)
        top_template_frame.pack(fill=X, padx=5, pady=5)
        
        Label(top_template_frame, text="Выберите шаблон:").pack(side=LEFT, padx=5)
        self.templates_combo = ttk.Combobox(top_template_frame, state="readonly", width=25)
        self.templates_combo.pack(side=LEFT, padx=5)
        self.templates_combo.bind('<<ComboboxSelected>>', self.on_template_selected)
        
        Button(top_template_frame, text="📂 Загрузить", command=self.load_template, bg="#4CAF50", fg="white").pack(side=LEFT, padx=2)
        Button(top_template_frame, text="💾 Сохранить", command=self.save_template, bg="#2196F3", fg="white").pack(side=LEFT, padx=2)
        Button(top_template_frame, text="🗑 Удалить", command=self.delete_template, bg="#f44336", fg="white").pack(side=LEFT, padx=2)
        
        # ===== Блок сессий =====
        session_frame = LabelFrame(main_frame, text="🎭 Аккаунт", font=("Arial", 11, "bold"))
        session_frame.pack(fill=X, padx=10, pady=10)
        
        session_inner = Frame(session_frame)
        session_inner.pack(fill=X, padx=5, pady=5)
        
        self.sessions_combo = ttk.Combobox(session_inner, state="readonly", width=40)
        self.sessions_combo.pack(side=LEFT, padx=5, fill=X, expand=True)
        Button(session_inner, text="🔄 Обновить", command=self.load_sessions_list).pack(side=LEFT, padx=2)
        Button(session_inner, text="➕ Новая сессия", command=self.create_new_session, bg="#4CAF50", fg="white").pack(side=LEFT, padx=2)
        
        # ===== Блок задержек =====
        delay_frame = LabelFrame(main_frame, text="⏱ Задержки", font=("Arial", 11, "bold"))
        delay_frame.pack(fill=X, padx=10, pady=10)
        
        main_delay_frame = Frame(delay_frame)
        main_delay_frame.pack(fill=X, padx=5, pady=5)
        
        Label(main_delay_frame, text="Задержка между сообщениями:").grid(row=0, column=0, sticky=W, padx=5)
        self.delay_from = Entry(main_delay_frame, width=8)
        self.delay_from.grid(row=0, column=1, padx=2)
        self.delay_from.insert(0, "60")
        Label(main_delay_frame, text="до").grid(row=0, column=2)
        self.delay_to = Entry(main_delay_frame, width=8)
        self.delay_to.grid(row=0, column=3, padx=2)
        self.delay_to.insert(0, "120")
        Label(main_delay_frame, text="сек").grid(row=0, column=4, padx=5)
        
        Label(main_delay_frame, text="Задержка перед стартом:").grid(row=1, column=0, sticky=W, padx=5, pady=5)
        self.delay_before = Entry(main_delay_frame, width=8)
        self.delay_before.grid(row=1, column=1, padx=2)
        self.delay_before.insert(0, "10")
        Label(main_delay_frame, text="сек").grid(row=1, column=2, padx=5, sticky=W)
        
        # ===== БЛОК: УДАЛЕНИЕ СООБЩЕНИЙ =====
        delete_frame = LabelFrame(main_frame, text="🗑️ Самоуничтожение", font=("Arial", 11, "bold"), fg="purple")
        delete_frame.pack(fill=X, padx=10, pady=10)
        
        self.delete_after_send = BooleanVar(value=False)
        Checkbutton(delete_frame, text="Удалять отправленные сообщения (только у себя!)",
                   variable=self.delete_after_send).pack(anchor=W, padx=5, pady=5)
        
        delete_delay_frame = Frame(delete_frame)
        delete_delay_frame.pack(anchor=W, padx=20, pady=5)
        
        Label(delete_delay_frame, text="Задержка перед удалением (сек):").pack(side=LEFT, padx=5)
        self.delete_delay = Entry(delete_delay_frame, width=8)
        self.delete_delay.pack(side=LEFT, padx=2)
        self.delete_delay.insert(0, "5")
        
        # ===== ЗАЩИТА ОТ ФЛУДА =====
        flood_frame = LabelFrame(main_frame, text="🛡️ Защита от флуда", font=("Arial", 11, "bold"), fg="red")
        flood_frame.pack(fill=X, padx=10, pady=10)
        
        flood_inner = Frame(flood_frame)
        flood_inner.pack(fill=X, padx=5, pady=5)
        
        Label(flood_inner, text="Макс сообщений в минуту:").grid(row=0, column=0, sticky=W, padx=5)
        self.max_per_minute = Entry(flood_inner, width=10)
        self.max_per_minute.grid(row=0, column=1, padx=5)
        self.max_per_minute.insert(0, "10")
        
        self.use_smart_delay = BooleanVar(value=True)
        Checkbutton(flood_inner, text="Умные задержки",
                   variable=self.use_smart_delay).grid(row=0, column=2, padx=5)
        
        Label(flood_inner, text="Лимит за сессию:").grid(row=1, column=0, sticky=W, padx=5, pady=5)
        self.max_per_session = Entry(flood_inner, width=10)
        self.max_per_session.grid(row=1, column=1, padx=5)
        self.max_per_session.insert(0, "300")
        
        # ===== Блок сообщений =====
        text_random_frame = LabelFrame(main_frame, text="📝 Сообщения", font=("Arial", 11, "bold"))
        text_random_frame.pack(fill=BOTH, expand=True, padx=10, pady=10)
        
        self.use_message_variants = BooleanVar(value=True)
        Checkbutton(text_random_frame, text="Использовать несколько вариантов",
                   variable=self.use_message_variants, command=self.toggle_message_variants).pack(anchor=W, padx=5, pady=5)
        
        self.variants_container = Frame(text_random_frame)
        self.variants_container.pack(fill=BOTH, expand=True, padx=5, pady=5)
        
        self.message_variants = []
        self.add_variant_button = Button(text_random_frame, text="+ Добавить вариант", command=self.add_message_variant)
        
        self.add_message_variant()
        self.toggle_message_variants()
        
        # ===== Предпросмотр =====
        preview_frame = LabelFrame(main_frame, text="📝 Предпросмотр", font=("Arial", 11, "bold"))
        preview_frame.pack(fill=BOTH, expand=True, padx=10, pady=10)
        
        self.preview_text = scrolledtext.ScrolledText(preview_frame, height=5, font=("Arial", 10), bg="#f0f0f0")
        self.preview_text.pack(fill=BOTH, expand=True, padx=5, pady=5)
        Button(preview_frame, text="🎲 Сгенерировать", command=self.generate_preview).pack(pady=5)
        
        # ===== Лог =====
        log_frame = LabelFrame(main_frame, text="📋 Лог", font=("Arial", 11, "bold"))
        log_frame.pack(fill=BOTH, expand=True, padx=10, pady=10)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=12, font=("Arial", 9))
        self.log_text.pack(fill=BOTH, expand=True, padx=5, pady=5)
        
        # ===== Кнопки =====
        btn_frame = Frame(main_frame)
        btn_frame.pack(fill=X, padx=10, pady=10)
        
        self.start_btn = Button(btn_frame, text="🚀 СТАРТ", bg="green", fg="white", 
                                font=("Arial", 11, "bold"), command=self.start_spam, height=2)
        self.start_btn.pack(side=LEFT, padx=5, expand=True, fill=X)
        
        self.stop_btn = Button(btn_frame, text="⏹ СТОП", bg="red", fg="white", 
                              font=("Arial", 11, "bold"), command=self.stop_spam, state=DISABLED, height=2)
        self.stop_btn.pack(side=LEFT, padx=5, expand=True, fill=X)
        
        Button(btn_frame, text="🗑 Очистить лог", command=self.clear_log, height=2).pack(side=LEFT, padx=5, expand=True, fill=X)
    
    def save_api_settings(self):
        try:
            self.api_id = int(self.api_id_entry.get())
            self.api_hash = self.api_hash_entry.get()
            config = {"api_id": self.api_id, "api_hash": self.api_hash}
            with open("api_config.json", "w") as f:
                json.dump(config, f)
            self.log("✅ API сохранены")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Неверный API ID: {e}")
    
    def load_api_settings(self):
        try:
            if os.path.exists("api_config.json"):
                with open("api_config.json", "r") as f:
                    config = json.load(f)
                    self.api_id = config.get("api_id", self.api_id)
                    self.api_hash = config.get("api_hash", self.api_hash)
                    self.api_id_entry.delete(0, END)
                    self.api_id_entry.insert(0, str(self.api_id))
                    self.api_hash_entry.delete(0, END)
                    self.api_hash_entry.insert(0, self.api_hash)
                return True
        except:
            pass
        return False
    
    def backup_session(self, session_path):
        try:
            if os.path.exists(session_path):
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_name = f"{os.path.basename(session_path)}_{timestamp}.backup"
                backup_path = os.path.join(self.backup_dir, backup_name)
                shutil.copy2(session_path, backup_path)
                return backup_path
        except:
            pass
        return None
    
    def create_new_session(self):
        try:
            self.save_api_settings()
            phone = simpledialog.askstring("Новая сессия", "Введите номер телефона (+7...):")
            if not phone:
                return
            
            session_name = simpledialog.askstring("Новая сессия", "Имя для сессии:")
            if not session_name:
                return
            
            session_path = os.path.join(self.sessions_dir, session_name)
            self.log(f"🔄 Создание сессии {session_name}...")
            
            client = TelegramClient(session_path, self.api_id, self.api_hash)
            
            async def create_session():
                await client.start(phone=phone)
                me = await client.get_me()
                self.log(f"✅ Сессия создана: {me.first_name}")
                await client.disconnect()
                self.load_sessions_list()
                messagebox.showinfo("Успех", f"Сессия {session_name} создана!")
            
            def run_async():
                asyncio.run(create_session())
            
            threading.Thread(target=run_async, daemon=True).start()
        except Exception as e:
            self.log(f"❌ Ошибка: {e}")
    
    def on_template_selected(self, event):
        self.load_template()
    
    def toggle_message_variants(self):
        if self.use_message_variants.get():
            self.add_variant_button.pack(pady=5)
            for frame, _, _ in self.message_variants:
                frame.pack(fill=X, pady=2)
        else:
            self.add_variant_button.pack_forget()
            for i, (frame, _, _) in enumerate(self.message_variants):
                if i == 0:
                    frame.pack(fill=X, pady=2)
                else:
                    frame.pack_forget()
    
    def add_message_variant(self):
        variant_num = len(self.message_variants) + 1
        frame = Frame(self.variants_container)
        
        Label(frame, text=f"Вариант {variant_num}:").pack(side=LEFT, padx=5)
        text_widget = scrolledtext.ScrolledText(frame, height=3, width=80, font=("Arial", 9))
        text_widget.pack(side=LEFT, fill=BOTH, expand=True, padx=5)
        
        if variant_num == 1:
            text_widget.insert(1.0, "Привет, {name}!")
        
        remove_btn = Button(frame, text="✖", command=lambda: self.remove_message_variant(frame))
        remove_btn.pack(side=LEFT, padx=2)
        
        self.message_variants.append((frame, text_widget, remove_btn))
        
        if not self.use_message_variants.get() and variant_num > 1:
            frame.pack_forget()
        else:
            frame.pack(fill=X, pady=2)
    
    def remove_message_variant(self, frame):
        if len(self.message_variants) <= 1:
            messagebox.showwarning("Внимание", "Должен быть хотя бы один вариант")
            return
        
        for i, (f, t, btn) in enumerate(self.message_variants):
            if f == frame:
                self.message_variants.pop(i)
                frame.destroy()
                for j, (f2, t2, btn2) in enumerate(self.message_variants, 1):
                    for child in f2.winfo_children():
                        if isinstance(child, Label) and "Вариант" in child.cget("text"):
                            child.config(text=f"Вариант {j}:")
                break
    
    def clear_all_variants(self):
        for frame, _, _ in self.message_variants:
            frame.destroy()
        self.message_variants.clear()
    
    def get_random_message(self, user):
        variants = []
        for _, text_widget, _ in self.message_variants:
            msg = text_widget.get(1.0, END).strip()
            if msg:
                variants.append(msg)
        
        if not variants:
            return ""
        
        if not self.use_message_variants.get():
            message = variants[0]
        else:
            message = random.choice(variants)
        
        try:
            first_name = user.first_name or ""
            last_name = user.last_name or ""
            name = f"{first_name} {last_name}".strip() or user.username or str(user.id)
            
            message = message.replace("{name}", name)
            message = message.replace("{first_name}", first_name)
            message = message.replace("{last_name}", last_name)
            return message
        except:
            return message
    
    def generate_preview(self):
        class FakeUser:
            def __init__(self):
                self.first_name = "Иван"
                self.last_name = "Петров"
                self.username = "ivan"
                self.id = 123
        
        message = self.get_random_message(FakeUser())
        self.preview_text.delete(1.0, END)
        self.preview_text.insert(1.0, message)
    
    def log(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(END, f"[{timestamp}] {message}\n")
        self.log_text.see(END)
        self.root.update()
    
    def clear_log(self):
        self.log_text.delete(1.0, END)
    
    def load_sessions_list(self):
        sessions = []
        if os.path.exists(self.sessions_dir):
            for file in os.listdir(self.sessions_dir):
                if file.endswith(".session") and not file.endswith(".broken"):
                    sessions.append(file.replace(".session", ""))
        
        if sessions:
            self.sessions_combo['values'] = sessions
            if sessions:
                self.sessions_combo.current(0)
            self.log(f"📂 Найдено сессий: {len(sessions)}")
        else:
            self.sessions_combo['values'] = []
            self.log("⚠️ Нет .session файлов")
    
    def load_templates_list(self):
        templates = []
        if os.path.exists(self.templates_dir):
            for file in os.listdir(self.templates_dir):
                if file.endswith(".json"):
                    templates.append(file.replace(".json", ""))
        
        current = self.templates_combo.get()
        self.templates_combo['values'] = templates
        
        if templates:
            if current in templates:
                self.templates_combo.set(current)
            else:
                self.templates_combo.set('')
            self.log(f"📁 Найдено шаблонов: {len(templates)}")
    
    def save_template(self):
        name = simpledialog.askstring("Сохранить шаблон", "Введите имя шаблона:")
        if not name:
            return
        
        messages = []
        for _, text_widget, _ in self.message_variants:
            msg = text_widget.get(1.0, END).strip()
            if msg:
                messages.append(msg)
        
        if not messages:
            messagebox.showerror("Ошибка", "Нет текста для сохранения")
            return
        
        template_data = {
            "messages": messages,
            "use_message_variants": self.use_message_variants.get(),
            "delay_from": self.delay_from.get(),
            "delay_to": self.delay_to.get(),
            "delay_before": self.delay_before.get(),
            "max_per_minute": self.max_per_minute.get(),
            "max_per_session": self.max_per_session.get(),
            "use_smart_delay": self.use_smart_delay.get(),
            "delete_after_send": self.delete_after_send.get(),
            "delete_delay": self.delete_delay.get()
        }
        
        file_path = os.path.join(self.templates_dir, f"{name}.json")
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(template_data, f, ensure_ascii=False, indent=2)
        
        self.log(f"✅ Шаблон '{name}' сохранён!")
        self.load_templates_list()
        self.templates_combo.set(name)
    
    def load_template(self):
        name = self.templates_combo.get()
        if not name:
            messagebox.showwarning("Внимание", "Выберите шаблон")
            return
        
        file_path = os.path.join(self.templates_dir, f"{name}.json")
        if not os.path.exists(file_path):
            messagebox.showerror("Ошибка", f"Файл не найден")
            return
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.delay_from.delete(0, END)
            self.delay_from.insert(0, data.get("delay_from", "60"))
            self.delay_to.delete(0, END)
            self.delay_to.insert(0, data.get("delay_to", "120"))
            self.delay_before.delete(0, END)
            self.delay_before.insert(0, data.get("delay_before", "10"))
            
            self.max_per_minute.delete(0, END)
            self.max_per_minute.insert(0, data.get("max_per_minute", "10"))
            self.max_per_session.delete(0, END)
            self.max_per_session.insert(0, data.get("max_per_session", "300"))
            self.use_smart_delay.set(data.get("use_smart_delay", True))
            
            self.delete_after_send.set(data.get("delete_after_send", False))
            self.delete_delay.delete(0, END)
            self.delete_delay.insert(0, data.get("delete_delay", "5"))
            
            self.clear_all_variants()
            messages = data.get("messages", ["Привет, {name}!"])
            
            for i, msg in enumerate(messages):
                self.add_message_variant()
                self.message_variants[i][1].delete(1.0, END)
                self.message_variants[i][1].insert(1.0, msg)
            
            use_variants = data.get("use_message_variants", len(messages) > 1)
            self.use_message_variants.set(use_variants)
            
            if use_variants:
                for frame, _, _ in self.message_variants:
                    frame.pack(fill=X, pady=2)
                self.add_variant_button.pack(pady=5)
            else:
                for i, (frame, _, _) in enumerate(self.message_variants):
                    if i == 0:
                        frame.pack(fill=X, pady=2)
                    else:
                        frame.pack_forget()
                self.add_variant_button.pack_forget()
            
            self.log(f"📂 Загружен шаблон '{name}'")
            self.generate_preview()
            
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))
    
    def delete_template(self):
        name = self.templates_combo.get()
        if not name:
            messagebox.showwarning("Внимание", "Выберите шаблон")
            return
        
        if messagebox.askyesno("Подтверждение", f"Удалить шаблон '{name}'?"):
            file_path = os.path.join(self.templates_dir, f"{name}.json")
            if os.path.exists(file_path):
                os.remove(file_path)
                self.log(f"🗑 Шаблон '{name}' удалён")
                self.load_templates_list()
    
    def calculate_smart_delay(self):
        try:
            max_per_min = int(self.max_per_minute.get())
            if max_per_min <= 0:
                return 60
            base_delay = 60 / max_per_min
            variation = random.uniform(0.8, 1.2)
            return base_delay * variation
        except:
            return 60
    
    async def keep_alive(self, client):
        """Поддержание соединения"""
        while self.running and not self.stop_flag:
            await asyncio.sleep(240)
            try:
                if client and client.is_connected():
                    await client.get_me()
                else:
                    if client and not self.is_reconnecting:
                        self.is_reconnecting = True
                        try:
                            await client.disconnect()
                            await asyncio.sleep(2)
                            await client.connect()
                            self.reconnect_attempts = 0
                        except Exception as e:
                            self.reconnect_attempts += 1
                            if self.reconnect_attempts >= 3:
                                self.stop_spam()
                        finally:
                            self.is_reconnecting = False
            except:
                pass
    
    async def send_message_safe(self, client, recipient, message, max_retries=3):
        """Безопасная отправка с обработкой дисконнекта"""
        for attempt in range(max_retries):
            try:
                if not client or not client.is_connected():
                    await client.connect()
                    await asyncio.sleep(3)
                
                sent = await client.send_message(recipient, message)
                
                if self.delete_after_send.get():
                    try:
                        delay = float(self.delete_delay.get())
                        if delay > 0:
                            await asyncio.sleep(delay)
                        await client.delete_messages(recipient, [sent.id], revoke=False)
                    except:
                        pass
                
                return True
                
            except Exception as e:
                error_msg = str(e).lower()
                if "disconnected" in error_msg or "connection" in error_msg:
                    if attempt < max_retries - 1:
                        await asyncio.sleep(5)
                        continue
                return False
        return False
    
    def start_spam(self):
        if not self.sessions_combo.get():
            messagebox.showerror("Ошибка", "Выберите сессию")
            return
        
        self.load_api_settings()
        
        has_message = False
        for _, text_widget, _ in self.message_variants:
            if text_widget.get(1.0, END).strip():
                has_message = True
                break
        
        if not has_message:
            messagebox.showerror("Ошибка", "Введите сообщение")
            return
        
        self.running = True
        self.stop_flag = False
        self.sent_chats.clear()
        self.sent_contacts.clear()
        self.reconnect_attempts = 0
        self.start_btn.config(state=DISABLED)
        self.stop_btn.config(state=NORMAL)
        
        thread = threading.Thread(target=self.run_async_spam, daemon=True)
        thread.start()
    
    def stop_spam(self):
        self.stop_flag = True
        self.log("⚠️ Остановка...")
    
    def run_async_spam(self):
        asyncio.run(self.spam_process())
    
    async def spam_process(self):
        session_name = self.sessions_combo.get()
        session_path = os.path.join(self.sessions_dir, session_name)
        
        self.log(f"✅ Запуск: {session_name}")
        
        self.backup_session(session_path)
        
        client = TelegramClient(
            session_path, 
            self.api_id, 
            self.api_hash,
            connection_retries=5,
            retry_delay=3,
            auto_reconnect=True,
            flood_sleep_threshold=120,
            request_retries=5
        )
        
        self.current_client = client
        
        try:
            await client.start()
            me = await client.get_me()
            my_id = me.id
            self.log(f"👤 Аккаунт: {me.first_name} (ID: {my_id})")
            
            if self.delete_after_send.get():
                self.log(f"🗑️ Самоуничтожение: ВКЛЮЧЕНО")
            
            keep_alive_task = asyncio.create_task(self.keep_alive(client))
            
            try:
                before_delay = float(self.delay_before.get())
            except:
                before_delay = 10
            self.log(f"⏳ Старт через {before_delay} сек...")
            await asyncio.sleep(before_delay)
            
            # Получаем диалоги
            self.log("📂 Получение диалогов...")
            dialogs = await client.get_dialogs()
            
            personal_dialogs = []
            skipped_count = 0
            
            for dialog in dialogs:
                entity = dialog.entity
                
                # Пропускаем каналы и чаты
                if isinstance(entity, (Chat, Channel)):
                    skipped_count += 1
                    continue
                
                # Пропускаем ботов
                if hasattr(entity, 'bot') and entity.bot:
                    skipped_count += 1
                    continue
                
                # Пропускаем пользователей
                if isinstance(entity, User) and not entity.bot:
                    # === ВАЖНО: ИСКЛЮЧАЕМ "ИЗБРАННОЕ" (Saved Messages) ===
                    # Избранное - это диалог с самим собой (entity.id == my_id)
                    if entity.id == my_id:
                        self.log("⏭️ Пропущено: Избранное (Saved Messages)")
                        skipped_count += 1
                        continue
                    
                    # === ИСКЛЮЧАЕМ АККАУНТ TELEGRAM ===
                    # Официальный аккаунт Telegram имеет username "telegram"
                    if hasattr(entity, 'username') and entity.username and entity.username.lower() == "telegram":
                        self.log("⏭️ Пропущено: Telegram аккаунт")
                        skipped_count += 1
                        continue
                    
                    # Также проверяем по имени
                    if hasattr(entity, 'first_name') and entity.first_name:
                        if entity.first_name.lower() == "telegram":
                            self.log("⏭️ Пропущено: Telegram")
                            skipped_count += 1
                            continue
                    
                    personal_dialogs.append(dialog)
            
            self.log(f"📊 Диалогов для рассылки: {len(personal_dialogs)}")
            self.log(f"⏭️ Пропущено (боты/каналы/избранное/telegram): {skipped_count}")
            
            try:
                max_session = int(self.max_per_session.get())
            except:
                max_session = 300
            
            messages_sent = 0
            minute_start = asyncio.get_event_loop().time()
            session_total = 0
            
            # Рассылка по диалогам
            if personal_dialogs:
                self.log("=" * 50)
                self.log("💬 РАССЫЛКА ПО ДИАЛОГАМ")
                self.log("=" * 50)
                
                for i, dialog in enumerate(personal_dialogs, 1):
                    if self.stop_flag or session_total >= max_session:
                        break
                    
                    user = dialog.entity
                    user_name = f"{user.first_name or ''} {user.last_name or ''}".strip() or user.username or str(user.id)
                    
                    message = self.get_random_message(user)
                    
                    self.log(f"[{i}/{len(personal_dialogs)}] → {user_name}")
                    
                    success = await self.send_message_safe(client, user, message)
                    
                    if success:
                        self.sent_chats.add(user.id)
                        messages_sent += 1
                        session_total += 1
                    
                    # Лимит в минуту
                    if self.use_smart_delay.get():
                        current_time = asyncio.get_event_loop().time()
                        if current_time - minute_start >= 60:
                            messages_sent = 1
                            minute_start = current_time
                        elif messages_sent >= int(self.max_per_minute.get()):
                            wait = 60 - (current_time - minute_start) + random.uniform(3, 6)
                            self.log(f"⚠️ Лимит {self.max_per_minute.get()}/мин, пауза {wait:.0f} сек")
                            await asyncio.sleep(wait)
                            messages_sent = 0
                            minute_start = asyncio.get_event_loop().time()
                    
                    # Задержка между сообщениями
                    if self.use_smart_delay.get():
                        delay = self.calculate_smart_delay()
                    else:
                        try:
                            delay = random.uniform(float(self.delay_from.get()), float(self.delay_to.get()))
                        except:
                            delay = random.uniform(60, 120)
                    
                    if i < len(personal_dialogs) and not self.stop_flag and session_total < max_session:
                        self.log(f"⏳ Пауза {delay:.0f} сек")
                        await asyncio.sleep(delay)
            
            # Контакты
            if not self.stop_flag and session_total < max_session:
                self.log("=" * 50)
                self.log("👥 РАССЫЛКА ПО КОНТАКТАМ")
                self.log("=" * 50)
                
                try:
                    contacts_result = await client(GetContactsRequest(hash=0))
                    
                    # Исключаем себя и Telegram из контактов
                    filtered_contacts = []
                    for c in contacts_result.users:
                        if c.bot:
                            continue
                        if c.id == my_id:
                            continue
                        if hasattr(c, 'username') and c.username and c.username.lower() == "telegram":
                            continue
                        if c.id not in self.sent_chats:
                            filtered_contacts.append(c)
                    
                    self.log(f"📊 Контактов для рассылки: {len(filtered_contacts)}")
                    
                    messages_sent = 0
                    minute_start = asyncio.get_event_loop().time()
                    
                    for i, contact in enumerate(filtered_contacts, 1):
                        if self.stop_flag or session_total >= max_session:
                            break
                        
                        name = f"{contact.first_name or ''} {contact.last_name or ''}".strip() or contact.username or str(contact.id)
                        message = self.get_random_message(contact)
                        
                        self.log(f"[{i}/{len(filtered_contacts)}] → {name}")
                        
                        success = await self.send_message_safe(client, contact, message)
                        
                        if success:
                            self.sent_contacts.add(contact.id)
                            messages_sent += 1
                            session_total += 1
                        
                        if self.use_smart_delay.get():
                            current_time = asyncio.get_event_loop().time()
                            if current_time - minute_start >= 60:
                                messages_sent = 1
                                minute_start = current_time
                            elif messages_sent >= int(self.max_per_minute.get()):
                                wait = 60 - (current_time - minute_start) + random.uniform(3, 6)
                                self.log(f"⚠️ Лимит, пауза {wait:.0f} сек")
                                await asyncio.sleep(wait)
                                messages_sent = 0
                                minute_start = current_time
                        
                        if self.use_smart_delay.get():
                            delay = self.calculate_smart_delay()
                        else:
                            try:
                                delay = random.uniform(float(self.delay_from.get()), float(self.delay_to.get()))
                            except:
                                delay = random.uniform(60, 120)
                        
                        if i < len(filtered_contacts) and not self.stop_flag and session_total < max_session:
                            await asyncio.sleep(delay)
                            
                except Exception as e:
                    self.log(f"❌ Ошибка контактов: {e}")
            
            keep_alive_task.cancel()
            
        except AuthKeyError:
            self.log("❌ Ошибка авторизации! Сессия повреждена.")
            if os.path.exists(session_path):
                os.rename(session_path, session_path + ".broken")
        except Exception as e:
            self.log(f"❌ Ошибка: {str(e)[:100]}")
        finally:
            try:
                await client.disconnect()
            except:
                pass
            self.current_client = None
        
        self.log("=" * 50)
        if self.stop_flag:
            self.log("❌ ОСТАНОВЛЕНО")
        else:
            self.log("✅ ЗАВЕРШЕНО!")
            self.log(f"📊 Отправлено: {len(self.sent_chats) + len(self.sent_contacts)}")
        
        self.running = False
        self.start_btn.config(state=NORMAL)
        self.stop_btn.config(state=DISABLED)


if __name__ == "__main__":
    root = Tk()
    app = TelegramSpamer(root)
    
    messagebox.showinfo("Готово", 
        "✅ Стабильная версия\n\n"
        "Исправлено:\n"
        "• Исключено 'Избранное' (Saved Messages)\n"
        "• Исключен официальный аккаунт Telegram\n"
        "• Убрана рандомизация раскладки\n"
        "• Автоматическое переподключение\n\n"
        "Рекомендуемые настройки:\n"
        "• Задержка: 60-120 сек\n"
        "• 10 сообщений в минуту\n"
        "• Лимит сессии: 300 сообщений")
    
    root.mainloop()