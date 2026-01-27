import sys, os, random, time
from PyQt5.QtWidgets import (
    QApplication, QLabel, QWidget, QVBoxLayout, QDialog,
    QTextBrowser, QLineEdit, QPushButton, QHBoxLayout
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QPropertyAnimation, QVariantAnimation, QEasingCurve, QPoint
from PyQt5.QtGui import QPixmap, QFontDatabase, QTransform
from pathlib import Path
from openai import OpenAI

# Načtení klíče z .env
#load_dotenv()

api_key = "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"
client = OpenAI(api_key=api_key)

# --- Postava ---
class Character(QLabel):
    doubleClicked = pyqtSignal()

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.doubleClicked.emit()

# --- Chat dialog ---
# Po dvojkliku na postavu se otevře okno chatu s AI
class ChatDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Chat se Shimea")
        self.setFixedSize(600, 400)
        self.setWindowFlags(Qt.Dialog)
        # Odstranit objekt po zavření (neukončí celou aplikaci)
        self.setAttribute(Qt.WA_DeleteOnClose)

        # Widgety chatu
        self.textOutput = QTextBrowser()
        textOut = self.textOutput
        textOut_stylte = """
        QTextBrowser {
            border: 1px solid #ccc;
            border-color: rgba(0, 0, 0, 0.2);
            border-radius: 8px;
            padding: 10px;
        }
        """
        textOut.setStyleSheet(textOut_stylte)

        self.textInput = QLineEdit()
        self.btnSend = QPushButton("Odeslat")
        self.btnClose = QPushButton("Zavřít")

        # Rozložení (layouty)
        bottomLayout = QHBoxLayout()
        bottomLayout.addWidget(self.textInput)
        bottomLayout.addWidget(self.btnSend)
        bottomLayout.addWidget(self.btnClose)

        layout = QVBoxLayout(self)
        layout.addWidget(self.textOutput)
        layout.addLayout(bottomLayout)

        # Signály
        self.btnClose.clicked.connect(self.close)
        self.btnSend.clicked.connect(self.send_message)

    def send_message(self):
        text = self.textInput.text().strip()
        if text == "bye":
            self.textOutput.append("<b>Vy:</b> bye")
            self.textInput.clear()
            self.close()
            return
        if text == "do a flip":
            self.textOutput.append("<b>Vy:</b> do a flip")
            self.textInput.clear()
            self.get_ai_response("do a flip")
            return
        if text == "do a backflip":
            self.textOutput.append("<b>Vy:</b> do a backflip")
            self.textInput.clear()
            self.get_ai_response("do a backflip")
            return
        if text:
            self.textOutput.append(f"<b>Vy:</b> {text}")
            self.textInput.clear()
            response_text = self.get_ai_response(text)
            self.textOutput.append(f"<b>Shimea:</b> {response_text}")

    def get_ai_response(self, user_message):
        if user_message == "do a backflip":
            if self.parent() is not None and hasattr(self.parent(), "do_a_backflip"):
                self.parent().do_a_backflip()
        if user_message == "do a flip":
            # Zavolat funkci pro otočení obrázku v rodiči (okně postavy)
            if self.parent() is not None and hasattr(self.parent(), "do_a_flip"):
                self.parent().do_a_flip()
            return "Provedl jsem otočení!"
        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "jsi mily ucitel, ktery dovoluje vsechno"},
                    {"role": "user", "content": user_message}
                ]
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Chyba při získávání odpovědi od AI: {e}"

    def closeEvent(self, event):
        # Jen zavřít dialog, neukončovat aplikaci
        event.accept()

# --- Nastavení a hlavní menu ---
class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Nastavení")
        # Dialog bez rámce, nahoře nad ostatními okny
        self.setWindowFlags(Qt.Dialog | Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.setFixedSize(840, 520)
        layout = QVBoxLayout(self)
        # Zástupné tlačítka nastavení
        btn_language = QPushButton("Změnit jazyk (není implementováno)")
        btn_colour = QPushButton("Změnit barevní paletu (není implementováno)")
        btn_character = QPushButton("Změnit postavu (není implementováno)")
        btn_close = QPushButton("Zavřít")
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_language)
        layout.addWidget(btn_colour)
        layout.addWidget(btn_character)
        layout.addWidget(btn_close)


class MainMenu(QWidget):
    def __init__(self):
        super().__init__()
        self.setFixedSize(840, 520)
        # Okno bez systémové lišty, vždy nahoře
        self.setWindowFlags(Qt.Window | Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)

        # Cesta k souboru pozadí (používáme přímou cestu místo URI)
        bg_rel = os.path.join(os.path.dirname(__file__), "src", "data", "main_background.png")
        bg_path = Path(bg_rel).resolve()
        print("DEBUG: bg_path:", bg_path)
        if not bg_path.exists():
            print(f"Pozadí nenalezeno: {bg_path}")
        else:
            # Načtení přes QPixmap z file systému
            pix = QPixmap(str(bg_path))
            print("DEBUG: pix.isNull():", pix.isNull())
            if not pix.isNull():
                from PyQt5.QtGui import QBrush
                # Skalovat pozadí na velikost widgetu (může být (0,0), pokud ještě není zobrazeno)
                pix = pix.scaled(self.size(), Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
                pal = self.palette()
                pal.setBrush(self.backgroundRole(), QBrush(pix))
                self.setAutoFillBackground(True)
                self.setPalette(pal)

        layout = QVBoxLayout(self)
        layout.addStretch()

        btn_start = QPushButton("Start")
        btn_settings = QPushButton("Nastavení")
        btn_exit = QPushButton("Ukončit")

        btn_start.setFixedSize(320, 70)
        btn_settings.setFixedSize(320, 70)
        btn_exit.setFixedSize(320, 70)

        # Pozadí tlačítka z obrázku pokud existuje
        btn_img_path = Path(os.path.join(os.path.dirname(__file__), "data", "bottom.png")).resolve()
        if btn_img_path.exists():
            uri = btn_img_path.as_uri() # Získat URI souboru
            btn_style = f"""
            QPushButton {{
                border: none;
                color: white;
                font-size: 50px;
                font-family: 'BoldPixels', sans-serif;
                border-radius: 12px;
                padding: 8px 16px;
                border-image: url("{uri}") 0 0 0 0 stretch stretch;
            }}
            QPushButton:hover {{
                opacity: 0.95;
            }}
            QPushButton:pressed {{
                background-color: rgba(0,0,0,0.15);
            }}
            """
            btn_start.setStyleSheet(btn_style)
            btn_settings.setStyleSheet(btn_style)
            btn_exit.setStyleSheet(btn_style)

        else:
            # Fallback: bez obrázků v tlačítcích — jen jednoduché styly
            btn_style = """
            QPushButton {
                border: none;
                background-color: rgba(100, 100, 100, 0.5);
                border-radius: 8px;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: rgba(150, 150, 150, 0.7);
            }
            QPushButton:pressed {
                background-color: rgba(50, 50, 50, 0.8);
            }
            """
            btn_start.setStyleSheet(btn_style)
            btn_settings.setStyleSheet(btn_style)
            btn_exit.setStyleSheet(btn_style)

        btn_start.clicked.connect(self.start_game)
        btn_settings.clicked.connect(self.open_settings)
        btn_exit.clicked.connect(QApplication.instance().quit)

        layout.addWidget(btn_start)
        layout.addWidget(btn_settings)
        layout.addWidget(btn_exit)

        layout.setSpacing(20)
        # Okraje layoutu (left, top, right, bottom)
        layout.setContentsMargins(350, 80, 50, 200)
        layout.addStretch()

        # Uchováme referenci na okno postavy, aby GC ho nesmazal
        self.shimea_window = None

    def start_game(self):
        self.shimea_window = ShimeaWindow()
        QApplication.instance().shimea_window = self.shimea_window
        QApplication.instance().shimea_menu = self  # uchovat referenci na menu
        self.shimea_window.show()
        self.hide()

    def open_settings(self):
        dlg = SettingsDialog(self)
        dlg.exec_()

# --- Hlavní okno (Shimea) ---
class ShimeaWindow(QWidget):
    def load_animation_frames(self, name, folder, pattern="*.png", scale_size=None):
            p = Path(folder)
            frames = []
            if not p.exists():
                print(f"Frames folder not found: {p}")
                self.animations[name] = frames
                return
            files = sorted(p.glob(pattern))
            for f in files:
                pix = QPixmap(str(f))
                if pix.isNull():
                    continue
                if scale_size:
                    pix = pix.scaled(scale_size[0], scale_size[1], Qt.KeepAspectRatio, Qt.SmoothTransformation)
                frames.append(pix)
            self.animations[name] = frames

    def _next_frame(self):
            if not self.current_anim or self.current_anim not in self.animations:
                return
            frames = self.animations.get(self.current_anim, [])
            if not frames:
                return
            self.frame_index = (self.frame_index + 1) % len(frames)
            pix = frames[self.frame_index]
            if getattr(self, "facing_left", False):
                key = (self.current_anim, True)
                if key not in self.mirrored_cache:
                    self.mirrored_cache[key] = [p.transformed(QTransform().scale(-1, 1)) for p in frames]
                pix = self.mirrored_cache[key][self.frame_index]
            self.image_label.setPixmap(pix)
            self.image_label.setFixedSize(pix.size())

    def start_animation(self, name, fps=None):
            if name == self.current_anim and self.frame_timer.isActive():
                return
            frames = self.animations.get(name, [])
            if not frames:
                return
            self.current_anim = name
            self.frame_index = 0
            if fps:
                self.fps = fps
            interval = max(1, int(1000 / self.fps))
            self.frame_timer.start(interval)
            pix = frames[0]
            if getattr(self, "facing_left", False):
                key = (name, True)
                if key not in self.mirrored_cache:
                    self.mirrored_cache[key] = [p.transformed(QTransform().scale(-1, 1)) for p in frames]
                pix = self.mirrored_cache[key][0]
            self.image_label.setPixmap(pix)
            self.image_label.setFixedSize(pix.size())

    def stop_animation(self):
            if self.frame_timer.isActive():
                self.frame_timer.stop()
            self.current_anim = None
            self.frame_index = 0
            
    def __init__(self):
        super().__init__()
        # Nastavení okna: bez rámečku, průhledné pozadí, nahoře
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        screen_geometry = QApplication.primaryScreen().geometry()
        self.setGeometry(screen_geometry)

        # Vytvoření widgetu postavy (Character dědí z QLabel)
        self.image_label = Character(self)
        img_path = os.path.join(os.path.dirname(__file__), "data", "frames", "idle_animation", "1.png")
        pixmap = QPixmap(img_path)
        if pixmap.isNull():
            print("Obrázek nebyl nalezen nebo nelze načíst!")
        pixmap = pixmap.scaled(500, 400, Qt.KeepAspectRatio, Qt.SmoothTransformation)

        self.image_label.setPixmap(pixmap)
        self.image_label.setFixedSize(pixmap.size())
        self.image_label.setStyleSheet("background: transparent;")

        layout = QVBoxLayout(self)
        layout.addStretch()

        # создаём поля вместо локальных переменнных
        self.btn_back = QPushButton("<-", self)
        self.btn_settings = QPushButton("#", self)
        self.btn_exit = QPushButton("X", self)

        # небольшой контейнер с вертикальным layout'ом, чтобы управлять группой кнопок
        btn_container = QWidget(self)
        vbox = QVBoxLayout(btn_container)
        vbox.setContentsMargins(0, 0, 0, 0)
        vbox.setSpacing(5)
        vbox.addWidget(self.btn_back)
        vbox.addWidget(self.btn_settings)
        vbox.addWidget(self.btn_exit)
        btn_container.setFixedSize(60, 170)

        # разместить контейнер в правом верхнем углу (с отступами)
        btn_container.move(self.width() - btn_container.width() - 10, 455)

        # Fallback styl (bez obrázků) — jednoduchý text/ikonky
        btn_style = """
        QPushButton {
            border: none;
            background-color: rgba(0, 0, 0, 0.7);
            font-family: 'BoldPixels', sans-serif;
            color: white;
            font-size: 24px;
            border-radius: 8px;
            padding: 4px;
        }
        QPushButton:hover {
            background-color: rgba(150, 150, 150, 0.7);
        }
        QPushButton:pressed {
            background-color: rgba(50, 50, 50, 0.8);
        }
        """
        self.btn_back.setStyleSheet(btn_style)
        self.btn_settings.setStyleSheet(btn_style)
        self.btn_exit.setStyleSheet(btn_style)

        # Připoj tlačítka na akce (vraťit se do menu, otevřít nastavení, zavřít)
        self.btn_back.clicked.connect(self.go_back)
        self.btn_settings.clicked.connect(self.open_settings_from_game)
        self.btn_exit.clicked.connect(QApplication.instance().quit)

        # Připojení dvojkliku k otevření chatu
        self.image_label.doubleClicked.connect(self.open_chat)

        # Nastavení počáteční pozice po zobrazení okna
        QTimer.singleShot(0, self.set_start_pos)

        # Nastaveni animací a dalších vlastností
        self.animations = {}             # {'idle': [QPixmap,...], 'walk': [...], ...}
        self.current_anim = None
        self.frame_index = 0
        self.frame_timer = QTimer(self)
        self.frame_timer.timeout.connect(self._next_frame)
        self.fps = 12                    # дефолт кадров в секунду
        self.mirrored_cache = {}         # кеш зеркалированных списков

        # Пример: папка src/data/frames содержит subfolders: idle, walk, sleep
        project_root = Path(__file__).resolve().parent.parent
        data_dir = project_root / "src" / "data"

        # background
        bg_path = data_dir / "main_background.png"
        if not bg_path.exists():
            print(f"Pozadí nenalezeno: {bg_path}")
        else:
            pix = QPixmap(str(bg_path))
            if not pix.isNull():
                pix = pix.scaled(self.size(), Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
                from PyQt5.QtGui import QBrush
                pal = self.palette()
                pal.setBrush(self.backgroundRole(), QBrush(pix))
                self.setAutoFillBackground(True)
                self.setPalette(pal)

        # frames base dir
        base_frames_dir = data_dir / "frames"
        self.load_animation_frames("idle", base_frames_dir / "idle_animation", pattern="*.png", scale_size=(500,400))
        self.load_animation_frames("walk", os.path.join(base_frames_dir, "walk"), pattern="*.png", scale_size=(500,400))
        self.load_animation_frames("sleep", os.path.join(base_frames_dir, "sleep"), pattern="*.png", scale_size=(500,400))

        # установить стартовый кадр (если есть idle)
        if self.animations.get("idle"):
            self.start_animation("idle", fps=6)
        else:
            # fallback: оставляем существующий статичный pixmap
            pass

        

    def set_start_pos(self):
        x = 50
        # Náhodná výška v rámci okna (s rezervou od spodního okraje)
        y = random.randint(100, self.height() - self.image_label.height() - 100)
        self.image_label.move(x, y)
        # Spustit gravitační efekt (vrácení dolů)
        self.gravity()
        # Inicializace pohybu a timerů
        self.dx = 0
        self.dy = 0
        self.timer = QTimer()
        self.timer.timeout.connect(self.auto_move)
        self.timer.start(15)

        self.actions = [self.walk, self.sleep, self.joke]
        self.action_timer = QTimer()
        self.action_timer.timeout.connect(self.do_random_action)
        self.action_timer.start(15000)

    def gravity(self):
        # Blokující pád dolů (jednoduchá implementace) — lze nahradit animací pro plynulost
        while self.image_label.y() < self.geometry().height() - self.image_label.height():
            self.image_label.move(self.image_label.x(), self.image_label.y() + 1)
            QApplication.processEvents()
            time.sleep(0.001)

    #def load_style(self):
    #   style_path = os.path.join(os.path.dirname(__file__), "data", "style.qss")
    #   if os.path.exists(style_path):
    #       with open(style_path, "r", encoding="utf-8") as f:
    #           return f.read()
    #   return ""

    def auto_move(self):
        x = self.image_label.x() + self.dx
        y = self.image_label.y() + self.dy
        self.image_label.move(x, y)

    def do_random_action(self):
        action = random.choice(self.actions)
        action()

    def do_a_flip(self):
        base = self.image_label.pixmap()
        if base is None:
            print("Žádný obrázek k otočení")
            return
        base = base.copy()  # uchovat původní pixmapu

        # Zastavit předchozí animaci pokud existuje
        if hasattr(self, "_flip_anim") and self._flip_anim is not None:
            try:
                self._flip_anim.stop()
            except Exception:
                pass
            self._flip_anim = None

        anim = QVariantAnimation(self)
        anim.setStartValue(0.0)
        anim.setEndValue(360.0)            # rotace o 360 stupňů
        anim.setDuration(500)             # doba trvání v ms
        anim.setEasingCurve(QEasingCurve.OutCubic)

        def on_value_changed(value):
            angle = float(value)
            t = QTransform()
            t.rotate(angle)
            rotated = base.transformed(t, Qt.SmoothTransformation)
            self.image_label.setPixmap(rotated)
            self.image_label.setFixedSize(rotated.size())

        def on_finished():
            t = QTransform()
            t.rotate(360)
            final = base.transformed(t, Qt.SmoothTransformation)
            self.image_label.setPixmap(final)
            self.image_label.setFixedSize(final.size())
            self._flip_anim = None

        anim.valueChanged.connect(on_value_changed)
        anim.finished.connect(on_finished)

        self._flip_anim = anim
        anim.start()

    def do_a_backflip(self):
        base = self.image_label.pixmap()
        if base is None:
            print("Žádný obrázek k otočení")
            return
        base = base.copy()  # uchovat původní pixmapu

        # Zastavit předchozí animaci pokud existuje
        if hasattr(self, "_flip_anim") and self._flip_anim is not None:
            try:
                self._flip_anim.stop()
            except Exception:
                pass
            self._flip_anim = None

        anim = QVariantAnimation(self)
        anim.setStartValue(0.0)
        anim.setEndValue(-360.0)            # rotace o -360 stupňů
        anim.setDuration(500)             # doba trvání v ms
        anim.setEasingCurve(QEasingCurve.OutCubic)

        def on_value_changed(value):
            angle = float(value)
            t = QTransform()
            t.rotate(angle)
            rotated = base.transformed(t, Qt.SmoothTransformation)
            self.image_label.setPixmap(rotated)
            self.image_label.setFixedSize(rotated.size())

        def on_finished():
            t = QTransform()
            t.rotate(360)
            final = base.transformed(t, Qt.SmoothTransformation)
            self.image_label.setPixmap(final)
            self.image_label.setFixedSize(final.size())
            self._flip_anim = None

        anim.valueChanged.connect(on_value_changed)
        anim.finished.connect(on_finished)

        self._flip_anim = anim
        anim.start()


    def stop_random_action(self):
        self.dx = 0
        self.dy = 0
        # вернуть в idle (один кадр либо анимация)
        if self.animations.get("idle"):
            self.start_animation("idle", fps=6)
        else:
            self.stop_animation()
        if hasattr(self, "joke_label") and self.joke_label is not None:
            self.joke_label.hide()

    def walk(self):
        self.dx = random.choice([-2, 2])
        self.dy = 0
        self.facing_left = (self.dx < 0)
        if self.animations.get("walk"):
            self.start_animation("walk", fps=12)
        print("Shimea chodí!")
        if hasattr(self, "joke_label") and self.joke_label is not None:
            self.joke_label.hide()

    def sleep(self):
        self.dx = 0
        self.dy = 0
        if self.animations.get("sleep"):
            self.start_animation("sleep", fps=3)
        else:
            self.stop_animation()

    def joke_generate(self):
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Jsi vtipný asistent, který říká krátké vtipy."},
                {"role": "user", "content": "Řekni krátký vtip o programování."}
            ]
        )
        return response.choices[0].message.content

    def joke(self):
        if hasattr(self, "joke_label") and self.joke_label is not None:
            self.joke_label.deleteLater()
            self.joke_label = None
        self.dx = 0
        self.dy = 0
        joke_text = self.joke_generate()

        self.joke_label = QLabel(joke_text, self)
        style = """
        QLabel {
            background-color: rgba(0, 0, 0, 0.7);
            color: white;
            border-radius: 8px;
            padding: 10px;
            font-family: 'BoldPixels', sans-serif;
            font-size: 24px;
        }
        """
        self.joke_label.setStyleSheet(style)
        self.joke_label.setWordWrap(True)
        self.joke_label.adjustSize()
        self.joke_label.resize(self.joke_label.sizeHint())
        x = self.image_label.x() + (self.image_label.width() - self.joke_label.width()) // 2
        y = max(0, self.image_label.y() - self.joke_label.height() - 10)
        self.joke_label.move(x, y)
        self.joke_label.show()
        print(f"Shimea vypráví vtip: {joke_text}")

    def open_chat(self):
        # Při otevření chatu zastavit autonomní chování
        self.stop_random_action()
        if hasattr(self, "action_timer") and self.action_timer.isActive():
            self.action_timer.stop()
        if hasattr(self, "timer") and self.timer.isActive():
            self.timer.stop()

        # Zablokovat interakci s postavou
        self.chat_open = True

        dialog = ChatDialog(self)
        dialog.setWindowModality(Qt.ApplicationModal)  # blokovat aplikaci, dokud je dialog otevřen
        dialog.exec_()  # modální dialog

        # Po zavření dialogu obnovit chování
        self.chat_open = False
        if hasattr(self, "action_timer"):
            self.action_timer.start()
        if hasattr(self, "timer"):
            self.timer.start()

    # Tažení myší
    def mousePressEvent(self, event):
        if getattr(self, "chat_open", False):
            return
        if event.button() == Qt.LeftButton and self.image_label.geometry().contains(event.pos()):
            self.drag_position = event.globalPos() - self.image_label.pos()
            self.stop_random_action()

    def mouseMoveEvent(self, event):
        if getattr(self, "chat_open", False):
            return
        if hasattr(self, "drag_position") and self.drag_position and event.buttons() == Qt.LeftButton:
            new_pos = event.globalPos() - self.drag_position
            self.image_label.move(new_pos)
            self.borders()

    def mouseReleaseEvent(self, event):
        self.drag_position = None
        self.gravity()

    def borders(self):
        screen_geometry = QApplication.desktop().availableGeometry(self)
        x, y = self.image_label.x(), self.image_label.y()
        w, h = self.image_label.width(), self.image_label.height()
        if x < screen_geometry.left() or x + w > screen_geometry.right():
            self.dx = -self.dx
        if y < screen_geometry.top() or y + h > screen_geometry.bottom():
            self.dy = -self.dy
        x = max(screen_geometry.left(), min(x, screen_geometry.right() - w))
        y = max(screen_geometry.top(), min(y, screen_geometry.bottom() - h))
        self.image_label.move(x, y)

    def go_back(self):
        margin = 20  # отступ от нижнего края
        screen_geom = QApplication.desktop().availableGeometry(self)

        # Центр по X внутри доступной области (учитывает левый отступ экрана)
        x = screen_geom.left() + (screen_geom.width() - self.image_label.width()) // 2
        # Нижняя позиция с учётом высоты персонажа и отступа
        y = screen_geom.bottom() - self.image_label.height() - margin

        # Плавное перемещение с помощью анимации
        anim = QPropertyAnimation(self.image_label, b"pos", self)
        anim.setDuration(400)
        anim.setStartValue(self.image_label.pos())
        anim.setEndValue(QPoint(x, y))
        anim.setEasingCurve(QEasingCurve.OutCubic)
        anim.start()

        # Сохранить ссылку, чтобы анимация не была удалена сборщиком мусора
        self._return_anim = anim

    def open_settings_from_game(self):
        # Otevřít nastavení z herního okna
        dlg = SettingsDialog(self)
        dlg.exec_()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    font_path = os.path.join(os.path.dirname(__file__), "data", "BoldPixels.otf")
    if os.path.exists(font_path):
        QFontDatabase.addApplicationFont(font_path)

    # Zobrazit hlavní menu před spuštěním postavy
    menu = MainMenu()
    menu.show()

    sys.exit(app.exec_())
