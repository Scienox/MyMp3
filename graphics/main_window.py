from PySide6.QtCore import Qt, QPoint, QPropertyAnimation, QEasingCurve, QAbstractAnimation
from PySide6.QtWidgets import (QMainWindow, QWidget, QHBoxLayout,
                                QVBoxLayout, QGridLayout, QPushButton,
                                QLineEdit, QStackedWidget, QTableWidget,
                                QComboBox, QHeaderView, QLabel, QSpacerItem,
                                QSizePolicy, QFormLayout, QListWidget
                                )
from class_item.media_player import MediaPlayer
from graphics.stacked_cutom import StackedCustom


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__(parent=None)

        self.setMinimumSize(1280, 720)
        self.setWindowTitle("MyMP3")

        self.setCentralWidget(QWidget(parent=self))

        self.myStyleSheet()

        self.__buildCentralWidget()
        self.__buildQueueDrawer()

        #self.__menuBar() >> si je cree une barre de menu

    def __buildCentralWidget(self):
        self.centralWidget().setLayout(QHBoxLayout())
        self.mediaPlayer = MediaPlayer(self.centralWidget())
        self.mediaPlayer.menuBtn.clicked.connect(self.toggleMenuDrawer)
        self.mediaPlayer.queueBtn.clicked.connect(self.toggleQueueDrawer)

        self.__buildMenuDrawer()
        self.centralWidget().layout().addWidget(self.mediaPlayer)

    def __buildMenuDrawer(self):
        central = self.centralWidget()
        # drawer en tant que widget enfant du central (positionné manuellement)
        self._drawer_width = 350
        self.menuYAxer = 10
        self._anim_full_duration = 1000  # durée en ms pour un trajet complet
        self.menuDrawer = QWidget(parent=central)
        self.menuIsOpening = False
        self.menuIsMoving = False
        self.menuDrawer.setFixedWidth(self._drawer_width)
        self.menuDrawer.setFixedHeight(self.mediaPlayer.videoWidget.height())
        # position initiale (hors de la zone centrale, coordonnées locales)
        self.menuDrawer.move(central.width(), self.menuYAxer)
        self.menuDrawer.hide()
        self.menuDrawerAnim = QPropertyAnimation(self.menuDrawer, b"pos", self)
        self.menuDrawerAnim.setEasingCurve(QEasingCurve.OutCubic)
        self.menuDrawerAnim.setDuration(self._anim_full_duration)
        self.menuDrawerAnim.finished.connect(self._on_menuDrawerAnim_finished)

        self.menuDrawerLayout = QVBoxLayout(self.menuDrawer)
    
        self.stackedWidget = StackedCustom(self.menuDrawer, tab_height=30)
        self.stackedWidget.add_page(QWidget(), "En ligne")
        self.stackedWidget.add_page(QWidget(), "Bibliothèque")
        self.stackedWidget.add_page(QWidget(), "Favoris en ligne")
        self.stackedWidget._top_layout.addStretch()
        self.stackedWidget.add_page(QWidget(), "Paramètres")

        self.stackedWidget.stack.widget(0).setLayout(QVBoxLayout())
        self.stackedWidget.stack.widget(0).layout().addWidget(QLabel("Contenu En ligne"))

        self.menuDrawerLayout.addWidget(self.stackedWidget)

    def __buildQueueDrawer(self):
        central = self.centralWidget()
        # drawer en bas (overlay venant du bas vers le haut)
        self._queue_height = 240
        self.queueIsOpening = False
        self.queueIsMoving = False
        self.queueDrawer = QWidget(parent=central)
        self.queueDrawer.setFixedHeight(self._queue_height)
        # width alignée à la largeur du drawer menu par défaut
        self.queueDrawer.setFixedWidth(self._drawer_width)
        # position initiale : hors de la zone (sous le widget central), aligné à gauche
        self.queueDrawer.move(self.menuYAxer, central.height())
        self.queueDrawer.hide()

        self.queueDrawerAnim = QPropertyAnimation(self.queueDrawer, b"pos", self)
        self.queueDrawerAnim.setEasingCurve(QEasingCurve.OutCubic)
        self.queueDrawerAnim.setDuration(self._anim_full_duration)
        self.queueDrawerAnim.finished.connect(self._on_queueDrawerAnim_finished)

        # layout et contenu (ex : liste réordonnable pour le scratch)
        self.queueLayout = QVBoxLayout(self.queueDrawer)
        self.queueLayout.setContentsMargins(4, 4, 4, 4)
        self.queueList = QListWidget(self.queueDrawer)
        self.queueList.setSelectionMode(QListWidget.SingleSelection)
        self.queueList.setDragEnabled(True)
        self.queueList.setAcceptDrops(True)
        self.queueList.setDragDropMode(QListWidget.InternalMove)
        self.queueLayout.addWidget(self.queueList)

    def toggleMenuDrawer(self):
        central = self.centralWidget()
        cw = central.width()
        drawer_w = self._drawer_width

        # position actuelle (coordonnées locales du parent)
        current = self.menuDrawer.pos()

        # décider la position de départ/fin (locales)
        if not self.menuIsOpening:
            self.menuIsOpening = True
            start = QPoint(current.x() if self.menuDrawer.pos() else cw, self.menuYAxer)
            end = QPoint(cw - drawer_w - self.menuYAxer, self.menuYAxer)
            # préparer l'affichage avant l'anim
            self.menuDrawer.move(start)
            self.menuDrawer.show()
            self.menuDrawer.raise_()
        else:
            self.menuIsOpening = False
            start = current
            end = QPoint(cw, self.menuYAxer)

        self.menuIsMoving = True

        # calculer distance restante et adapter la durée
        remaining = abs(end.x() - start.x())
        full = drawer_w if drawer_w > 0 else 1
        duration = max(60, int(self._anim_full_duration * (remaining / full)))  # minimum 60ms

        # arrêter toute anim existante, appliquer nouvelle durée et lancer depuis la position courante
        if self.menuDrawerAnim.state() == QAbstractAnimation.Running:
            self.menuDrawerAnim.stop()
        self.menuDrawerAnim.setDuration(duration)
        self.menuDrawerAnim.setStartValue(start)
        self.menuDrawerAnim.setEndValue(end)
        self.menuDrawerAnim.start()

    def toggleQueueDrawer(self):
        central = self.centralWidget()
        ch = central.height()
        drawer_h = self._queue_height

        # calculer hauteur de la zone de contrôle (mediaPlayer total - video area)
        try:
            controls_h = max(0, self.mediaPlayer.height() - self.mediaPlayer.videoWidget.height())
        except Exception:
            controls_h = 0

        # position actuelle (coordonnées locales du parent)
        current = self.queueDrawer.pos()

        # décider la position de départ/fin (locales) — aligné à gauche
        if not self.queueIsOpening:
            self.queueIsOpening = True
            start = QPoint(self.menuYAxer, ch)
            end_y = max(0, ch - drawer_h - controls_h - self.menuYAxer)
            end = QPoint(self.menuYAxer, end_y)
            self.queueDrawer.move(start)
            self.queueDrawer.show()
            self.queueDrawer.raise_()
        else:
            self.queueIsOpening = False
            start = current
            end = QPoint(self.menuYAxer, ch)

        self.queueIsMoving = True

        remaining = abs(end.y() - start.y())
        full = drawer_h if drawer_h > 0 else 1
        duration = max(60, int(self._anim_full_duration * (remaining / full)))

        if self.queueDrawerAnim.state() == QAbstractAnimation.Running:
            self.queueDrawerAnim.stop()
        self.queueDrawerAnim.setDuration(duration)
        self.queueDrawerAnim.setStartValue(start)
        self.queueDrawerAnim.setEndValue(end)
        self.queueDrawerAnim.start()

    def myStyleSheet(self):
        open("graphics/style.qss", "r").read()
        with open("graphics/style.qss", "r") as styleFile:
            style = styleFile.read()
            self.setStyleSheet(style)

    def _on_menuDrawerAnim_finished(self):
        central = self.centralWidget()
        if self.menuDrawer.pos().x() >= central.width():
            self.menuDrawer.hide()
        self.menuIsMoving = False

    def _on_queueDrawerAnim_finished(self):
        central = self.centralWidget()
        # si complètement hors de la zone centrale -> cacher
        if self.queueDrawer.pos().y() >= central.height():
            self.queueDrawer.hide()
        self.queueIsMoving = False

    def resizeEvent(self, event):
        super().resizeEvent(event)
        central = self.centralWidget()
        self.menuDrawer.setFixedHeight(self.mediaPlayer.videoWidget.height())
        base = self.centralWidget().mapToGlobal(QPoint(0, 0))
        if not self.menuIsMoving:
            if self.menuDrawer.isVisible():
                self.menuDrawer.move(base + QPoint(central.width() - self.menuDrawer.width() - self.menuYAxer, self.menuYAxer))
            else:
                self.menuDrawer.move(base + QPoint(central.width() - self.menuYAxer, self.menuYAxer))
        # repositionner le queueDrawer (en coordonnées locales, aligné à gauche)
        try:
            # largeur du drawer peut évoluer
            self.queueDrawer.setFixedWidth(self._drawer_width)
            # recalculer hauteur controles
            try:
                controls_h = max(0, self.mediaPlayer.height() - self.mediaPlayer.videoWidget.height())
            except Exception:
                controls_h = 0
            if not self.queueIsMoving:
                if self.queueDrawer.isVisible():
                    self.queueDrawer.move(self.menuYAxer,
                                          central.height() - self.queueDrawer.height() - controls_h - self.menuYAxer)
                else:
                    self.queueDrawer.move(self.menuYAxer, central.height())
        except AttributeError:
            pass
