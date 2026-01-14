from PySide6.QtCore import Qt, QUrl, Slot, Signal, QTimer
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput, QVideoSink
from PySide6.QtGui import QImage, QPainter
from PySide6.QtWidgets import (QMainWindow, QWidget, QHBoxLayout,
                                QVBoxLayout, QGridLayout, QPushButton,
                                QLineEdit, QStackedWidget, QTableWidget, QSlider, QFileDialog)



class NodeSong:
    def __init__(self, title, artist, album):
        self.title = title
        self.artist = artist
        self.album = album
        self.next = None
        self.previous = None


class Queue:
    def __init__(self):
        self.lenght = 0
        self.origin = None
        self.head = None

    def is_empty(self):
        return self.lenght == 0
    
    def __len__(self):
        return self.lenght
    
    def add_song(self, title, artist, album):
        new_node = NodeSong(title, artist, album)
        if self.is_empty():
            self.head = new_node
            self.origin = new_node
            self.head.next = self.origin
            self.head.previous = self.origin
        else:
            self.head.next = new_node
            new_node.previous = self.head
            new_node.next = self.origin
            self.head = new_node
        self.lenght += 1

    def remove_song(self, node:NodeSong):
        if not self.is_empty():
            
            if len(self) == 1:
                self.head = None
                self.origin = None
            else:
                node.previous.next = node.next
                node.next.previous = node.previous
                if node == self.origin:
                    self.origin = node.next
                if node == self.head:
                    self.head = node.previous
            self.lenght -= 1


class VideoWidget(QWidget):
    """Peint les frames reçues via QVideoSink — pas de surface native."""
    # signal émis lors d'un double-clic sur le widget vidéo
    doubleClicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._image = QImage()
        self.setAttribute(Qt.WA_OpaquePaintEvent)
        # suivi de la souris pour cacher le curseur après une courte inactivité
        self.setMouseTracking(True)
        self._idle_timer = QTimer(self)
        self._idle_timer.setSingleShot(True)
        self._idle_timer.setInterval(1000)  # ms avant de masquer le curseur
        self._idle_timer.timeout.connect(self._on_mouse_idle_timeout)
        self._cursor_hidden = False

    def mouseDoubleClickEvent(self, event):
        # émettre le signal pour que l'appelant puisse basculer le plein écran
        try:
            self.doubleClicked.emit()
        except Exception:
            pass
        event.accept()

    def _on_mouse_idle_timeout(self):
        # masquer visuellement le curseur (il reste actif)
        try:
            self.setCursor(Qt.BlankCursor)
            self._cursor_hidden = True
        except Exception:
            pass

    def set_frame(self, frame):
        # frame est un QVideoFrame ; conversion en QImage si possible
        try:
            img = frame.toImage()
        except Exception:
            return
        if not img.isNull():
            # garder un format rapide pour QPainter
            self._image = img.convertToFormat(QImage.Format_RGB32)
            self.update()

    def mouseMoveEvent(self, event):
        # réafficher le curseur si nécessaire et relancer le timer d'inactivité
        if self._cursor_hidden:
            try:
                self.setCursor(Qt.ArrowCursor)
            except Exception:
                pass
            self._cursor_hidden = False
        self._idle_timer.start()
        super().mouseMoveEvent(event)

    def enterEvent(self, event):
        # s'assurer que le curseur est visible à l'entrée
        if self._cursor_hidden:
            try:
                self.setCursor(Qt.ArrowCursor)
            except Exception:
                pass
            self._cursor_hidden = False
        self._idle_timer.start()
        super().enterEvent(event)

    def leaveEvent(self, event):
        # arrêter le timer et réafficher le curseur si on quitte la zone
        if self._idle_timer.isActive():
            self._idle_timer.stop()
        if self._cursor_hidden:
            try:
                self.setCursor(Qt.ArrowCursor)
            except Exception:
                pass
            self._cursor_hidden = False
        super().leaveEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        if not self._image.isNull():
            scaled = self._image.scaled(self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            x = (self.width() - scaled.width()) // 2
            y = (self.height() - scaled.height()) // 2
            painter.drawImage(x, y, scaled)
        else:
            painter.fillRect(self.rect(), Qt.black)


class FullscreenVideoWindow(QWidget):
    """Fenêtre temporaire pour afficher la vidéo en plein écran sans toucher au reste de l'UI."""
    def __init__(self, video_widget):
        super().__init__(None)
        self.setWindowFlags(Qt.Window)
        self.setAttribute(Qt.WA_DeleteOnClose, True)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(video_widget)

    def keyPressEvent(self, event):
        # ESC pour quitter le plein écran vidéo
        if event.key() == Qt.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)


class MediaPlayer(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.player = QMediaPlayer(self)
        self.audio = QAudioOutput(self)
        # connecter l'audio au player et initialiser le volume
        self.queue = Queue()
        self.player.setAudioOutput(self.audio)
        self.audio.setVolume(0.5)  # 0.0 .. 1.0
        # debug rapide pour voir erreurs / statut
        self.player.errorOccurred.connect(lambda err, msg="": print("player error:", err, msg))
        self.player.mediaStatusChanged.connect(lambda s: print("mediaStatus:", s))
        # utilisation de QVideoSink + VideoWidget (aucune surface native)
        self.videoSink = QVideoSink(self)
        self.videoWidget = VideoWidget(self)
        # connexion sink -> widget
        self.videoSink.videoFrameChanged.connect(self.videoWidget.set_frame)
        self.player.setVideoOutput(self.videoSink)

        # double-clic sur la vidéo -> basculer plein écran
        self.videoWidget.doubleClicked.connect(self._on_video_double_clicked)

        self.playToggleBtn = QPushButton("Play/Pause", self)
        self.playToggleBtn.clicked.connect(self.open_and_play)
        self.stopBtn = QPushButton("Stop", self)
        self.menuBtn = QPushButton("Menu", self)
        self.queueBtn = QPushButton("Queue", self)

        self.positionSlider = QSlider(Qt.Horizontal, self)
        self.positionSlider.setRange(0, 0)

        self.volumeSlider = QSlider(Qt.Horizontal, self)
        self.volumeSlider.setFixedWidth(100)
        self.volumeSlider.setRange(0, 100)
        self.volumeSlider.setValue(50)

        # relier le slider de volume à l'audio output
        self.volumeSlider.valueChanged.connect(lambda v: self.audio.setVolume(v / 100.0))

        controlsLayout = QHBoxLayout()
        controlsLayout.addStretch()
        controlsLayout.addWidget(self.queueBtn)
        controlsLayout.addWidget(self.playToggleBtn)
        controlsLayout.addWidget(self.stopBtn)
        controlsLayout.addWidget(self.volumeSlider)
        controlsLayout.addStretch()
        controlsLayout.addWidget(self.menuBtn)

        mainLayout = QVBoxLayout(self)
        mainLayout.addWidget(self.videoWidget, stretch=1)
        mainLayout.addWidget(self.positionSlider)
        mainLayout.addLayout(controlsLayout)

        # garder la référence du layout principal pour pouvoir retirer/réinsérer la vidéo
        self._mainLayout = mainLayout
        self._fullscreen_window = None

    @Slot()
    def open_and_play(self):
        path, _ = QFileDialog.getOpenFileName(self, "Ouvrir une vidéo",
                                              filter="Vidéo/Audio (*.mp4 *.mkv *.avi *.mp3 *.wav);;Tous fichiers (*)")
        if not path:
            return
        # charge et lance la lecture
        self.player.setSource(QUrl.fromLocalFile(path))
        print("audioAvailable:", getattr(self.player, "isAudioAvailable", lambda: None)(),
              " videoAvailable:", getattr(self.player, "isVideoAvailable", lambda: None)())
        self.player.play()

    def _on_video_double_clicked(self):
        """Basculer la vidéo en plein écran (fenêtre dédiée) ou revenir en mode normal."""
        try:
            if self._fullscreen_window is None:
                self._enter_video_fullscreen()
            else:
                self._exit_video_fullscreen()
        except Exception as e:
            print("Fullscreen toggle failed:", e)

    def _enter_video_fullscreen(self):
        """Déplace la VideoWidget dans une fenêtre autonome en plein écran."""
        try:
            # retirer du layout principal
            try:
                self._mainLayout.removeWidget(self.videoWidget)
            except Exception:
                pass
            self.videoWidget.setParent(None)

            w = FullscreenVideoWindow(self.videoWidget)
            # restaurer la vidéo dans l'UI quand la fenêtre est détruite
            w.destroyed.connect(self._on_fullscreen_closed)
            self._fullscreen_window = w
            w.showFullScreen()
        except Exception as e:
            print("enter fullscreen failed:", e)

    def _exit_video_fullscreen(self):
        """Ferme la fenêtre fullscreen si présente (provoque la restauration)."""
        try:
            if self._fullscreen_window is not None:
                self._fullscreen_window.close()
        except Exception as e:
            print("exit fullscreen failed:", e)

    def _on_fullscreen_closed(self, *args):
        """Remet la VideoWidget dans le layout principal après fermeture de la fenêtre fullscreen."""
        try:
            # remettre la video dans la layout principale
            if self.videoWidget.parent() is not self:
                self.videoWidget.setParent(self)
            # insérer en tête avec stretch=1
            try:
                self._mainLayout.insertWidget(0, self.videoWidget, stretch=1)
            except Exception:
                self._mainLayout.addWidget(self.videoWidget, stretch=1)
        except Exception as e:
            print("restore video failed:", e)
        finally:
            self._fullscreen_window = None
        