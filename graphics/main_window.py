from PySide6.QtCore import Qt, QPoint, QPropertyAnimation, QEasingCurve, QAbstractAnimation
from PySide6.QtWidgets import (QMainWindow, QWidget, QHBoxLayout,
                                QVBoxLayout, QGridLayout, QPushButton,
                                QLineEdit, QStackedWidget, QTableWidget,
                                QComboBox, QHeaderView, QLabel, QSpacerItem,
                                QSizePolicy, QFormLayout, QListWidget, QGraphicsOpacityEffect
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
        self._anim_full_duration = 750  # durée en ms pour un trajet complet
        self.menuDrawer = QWidget(parent=central)
        self.menuIsOpening = False
        self.menuIsMoving = False
        self.menuDrawer.setFixedWidth(self._drawer_width)
        self.menuDrawer.setFixedHeight(self.mediaPlayer.videoWidget.height())
        # position initiale (hors de la zone centrale, coordonnées locales)
        self.menuDrawer.move(central.width(), self.menuYAxer)
        self.menuDrawer.hide()
        self.menuDrawerAnim = QPropertyAnimation(self.menuDrawer, b"pos", self)
        self.menuDrawerAnim.setEasingCurve(QEasingCurve.InOutQuad)
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
        self._queue_height = 150 # Hauteur plus réaliste pour une liste
        self.queue_duration = 300 # Un peu plus lent pour être visible
        self.queueIsOpening = False
        self.queueIsMoving = False
        self.queueDrawer = QWidget(parent=central)
        self.queueDrawer.setFixedHeight(self._queue_height)
        
        # position initiale : caché à gauche
        self.queueDrawer.move(-1000, 0) # Sera repositionné par resizeEvent
        self.queueDrawer.hide()

        self.queueDrawerAnim = QPropertyAnimation(self.queueDrawer, b"pos", self)
        self.queueDrawerAnim.setEasingCurve(QEasingCurve.InOutQuad)
        self.queueDrawerAnim.setDuration(self.queue_duration)
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

        if self.menuDrawerAnim.state() == QAbstractAnimation.Running:
            self.menuDrawerAnim.stop()

        if not self.menuIsOpening:
            self.menuIsOpening = True
            # On part de la position actuelle pour éviter les sauts
            start = current
            end = QPoint(cw - drawer_w - self.menuYAxer, self.menuYAxer)
            self.menuDrawer.show()
            self.menuDrawer.raise_()
        else:
            self.menuIsOpening = False
            start = current
            end = QPoint(cw, self.menuYAxer)

        self.menuIsMoving = True

        # calculer distance restante et adapter la durée
        remaining = abs(end.x() - start.x())
        duration = max(60, int(self._anim_full_duration * (remaining / drawer_w)))

        self.menuDrawerAnim.setDuration(duration)
        self.menuDrawerAnim.setStartValue(start)
        self.menuDrawerAnim.setEndValue(end)
        self.menuDrawerAnim.start()

    def toggleQueueDrawer(self):
        central = self.centralWidget()
        
        # Calcul de la position Y cible (au dessus des contrôles si possible)
        try:
            controls_h = max(0, self.mediaPlayer.height() - self.mediaPlayer.videoWidget.height())
        except Exception:
            controls_h = 80 # fallback

        target_y = central.height() - self.queueDrawer.height() - controls_h - self.menuYAxer
        
        # position actuelle
        current = self.queueDrawer.pos()

        if self.queueDrawerAnim.state() == QAbstractAnimation.Running:
            self.queueDrawerAnim.stop()

        if not self.queueIsOpening:
            self.queueIsOpening = True
            start = current
            end = QPoint(self.menuYAxer, target_y)
            self.queueDrawer.show()
            self.queueDrawer.raise_()
        else:
            self.queueIsOpening = False
            start = current
            end = QPoint(-self.queueDrawer.width(), target_y)

        self.queueIsMoving = True

        remaining = abs(end.x() - start.x())
        full_dist = self.queueDrawer.width()
        duration = max(60, int(self.queue_duration * (remaining / full_dist)))

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
        if not self.menuIsOpening:
            self.menuDrawer.hide()
        self.menuIsMoving = False
        self.resize_queue()

    def _on_queueDrawerAnim_finished(self):
        if not self.queueIsOpening:
            self.queueDrawer.hide()
        self.queueIsMoving = False

    def resize_queue(self):
        central = self.centralWidget()
        # On calcule l'espace disponible à gauche du menu (qu'il soit visible ou en mouvement)
        menu_x = self.menuDrawer.x() if self.menuDrawer.isVisible() else central.width()
        available_w = menu_x - (self.menuYAxer * 2)
        self.queueDrawer.setFixedWidth(max(100, available_w))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        central = self.centralWidget()
        cw = central.width()
        ch = central.height()

        # Update dimensions
        self.menuDrawer.setFixedHeight(self.mediaPlayer.videoWidget.height())
        
        # Repositionner sans mapToGlobal (car drawer est enfant de central)
        if not self.menuIsMoving:
            if self.menuIsOpening:
                self.menuDrawer.move(cw - self._drawer_width - self.menuYAxer, self.menuYAxer)
            else:
                self.menuDrawer.move(cw, self.menuYAxer)
        
        self.resize_queue()
        
        if not self.queueIsMoving:
            try:
                controls_h = max(0, self.mediaPlayer.height() - self.mediaPlayer.videoWidget.height())
            except:
                controls_h = 80
            
            target_y = ch - self.queueDrawer.height() - controls_h - self.menuYAxer
            if self.queueIsOpening:
                self.queueDrawer.move(self.menuYAxer, target_y)
            else:
                self.queueDrawer.move(-self.queueDrawer.width(), target_y)
