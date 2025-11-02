from PySide6.QtCore import Qt, QUrl, Slot
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput, QVideoSink
from PySide6.QtGui import QImage, QPainter
from PySide6.QtWidgets import (QMainWindow, QWidget, QHBoxLayout,
                                QVBoxLayout, QGridLayout, QPushButton,
                                QLineEdit, QStackedWidget, QTableWidget, QSlider, QFileDialog)

class VideoWidget(QWidget):
    """Peint les frames reçues via QVideoSink — pas de surface native."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self._image = QImage()
        self.setAttribute(Qt.WA_OpaquePaintEvent)

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

    def paintEvent(self, event):
        painter = QPainter(self)
        if not self._image.isNull():
            scaled = self._image.scaled(self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            x = (self.width() - scaled.width()) // 2
            y = (self.height() - scaled.height()) // 2
            painter.drawImage(x, y, scaled)
        else:
            painter.fillRect(self.rect(), Qt.black)

class MediaPlayer(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.player = QMediaPlayer(self)
        self.audio = QAudioOutput(self)
        # connecter l'audio au player et initialiser le volume
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

        self.playToggleBtn = QPushButton("Play/Pause", self)
        self.playToggleBtn.clicked.connect(self.open_and_play)
        self.stopBtn = QPushButton("Stop", self)
        self.menuBtn = QPushButton("Menu", self)

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
        controlsLayout.addWidget(self.playToggleBtn)
        controlsLayout.addWidget(self.stopBtn)
        controlsLayout.addWidget(self.volumeSlider)
        controlsLayout.addStretch()
        controlsLayout.addWidget(self.menuBtn)

        mainLayout = QVBoxLayout(self)
        mainLayout.addWidget(self.videoWidget, stretch=1)
        mainLayout.addWidget(self.positionSlider)
        mainLayout.addLayout(controlsLayout)

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
