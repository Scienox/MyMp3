from PySide6.QtCore import Qt, QPoint, QPropertyAnimation, QEasingCurve, QAbstractAnimation
from PySide6.QtWidgets import (QMainWindow, QWidget, QHBoxLayout,
                                QVBoxLayout, QGridLayout, QPushButton,
                                QLineEdit, QStackedWidget, QTableWidget,
                                QComboBox, QHeaderView, QLabel, QSpacerItem,
                                QSizePolicy, QFormLayout
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

        #self.__menuBar() >> si je cree une barre de menu

    def __buildCentralWidget(self):
        self.centralWidget().setLayout(QHBoxLayout())
        self.mediaPlayer = MediaPlayer(self.centralWidget())
        self.mediaPlayer.menuBtn.clicked.connect(self.toggleMenuDrawer)

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

        self.stackedWidget.stack.widget(0).setLayout(QVBoxLayout())
        self.stackedWidget.stack.widget(0).layout().addWidget(QLabel("Contenu En ligne"))

        self.menuDrawerLayout.addWidget(self.stackedWidget)

        


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

    def myStyleSheet(self):
        open("graphics/style.qss", "r").read()
        with open("graphics/style.qss", "r") as styleFile:
            style = styleFile.read()
            self.setStyleSheet(style)

    def _on_menuDrawerAnim_finished(self):
        central = self.centralWidget()
        if self.menuDrawer.pos().x() >= central.width():
            self.menuDrawer.hide()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        central = self.centralWidget()
        self.menuDrawer.setFixedHeight(self.mediaPlayer.videoWidget.height())
        base = self.centralWidget().mapToGlobal(QPoint(0, 0))
        if self.menuDrawer.isVisible():
            self.menuDrawer.move(base + QPoint(central.width() - self.menuDrawer.width() - self.menuYAxer, self.menuYAxer))
        else:
            self.menuDrawer.move(base + QPoint(central.width() - self.menuYAxer, self.menuYAxer))
    
    # ------
    """
    def __buildCentralWidget(self):
        central = self.centralWidget()

        # layout principal : le left_widget occupe tout l'espace géré par le layout
        main_layout = QHBoxLayout()
        central.setLayout(main_layout)

        # --- Partie gauche (contenu principal) ---
        left_widget = QWidget(parent=central)
        left_layout = QVBoxLayout(left_widget)
        left_layout.addWidget(QLabel("Contenu gauche (ex: table, liste...)"))
        left_layout.addStretch()
        main_layout.addWidget(left_widget, 1)  # prend tout l'espace disponible

        # bouton pour ouvrir/fermer le volet (placé dans la partie gauche)
        self.toggle_btn = QPushButton("Ouvrir volet", parent=left_widget)
        left_layout.insertWidget(0, self.toggle_btn)

        # --- Volet droit (overlay) ---
        self.drawer_width = 320
        self.drawer = QWidget(parent=central)
        self.drawer.setFixedWidth(self.drawer_width)
        self.drawer.setStyleSheet("background: #2b2b2b; color: white;")
        drawer_layout = QVBoxLayout(self.drawer)
        drawer_layout.addWidget(QLabel("Volet de menu"))
        drawer_layout.addStretch()

        # position initiale : caché à droite (hors de la vue)
        self.drawer.move(central.width(), 0)
        self.drawer.hide()

        # animation de la position (fait "glisser" le volet)
        self.menuDrawerAnim = QPropertyAnimation(self.drawer, b"pos", self)
        self.menuDrawerAnim.setEasingCurve(QEasingCurve.OutCubic)
        self.menuDrawerAnim.setDuration(220)
        self.menuDrawerAnim.finished.connect(self._on_menuDrawerAnim_finished)

        self._drawer_open = False
        self.toggle_btn.clicked.connect(self.toggle_drawer)

    def toggle_drawer(self):
        central = self.centralWidget()
        cw = central.width()
        start = QPoint()
        end = QPoint()
        if not self._drawer_open:
            # ouvrir : de hors-écran -> visible (collé à droite)
            start = QPoint(cw, 0)
            end = QPoint(cw - self.drawer_width, 0)
            self.drawer.show()
            self.drawer.raise_()
        else:
            # fermer : de visible -> hors-écran à droite
            start = QPoint(cw - self.drawer_width, 0)
            end = QPoint(cw, 0)

        self.menuDrawerAnim.stop()
        self.menuDrawerAnim.setStartValue(start)
        self.menuDrawerAnim.setEndValue(end)
        self.menuDrawerAnim.start()
        self._drawer_open = not self._drawer_open

    def _on_menuDrawerAnim_finished(self):
        # masquer le widget quand il est complètement hors de la vue (optionnel)
        central = self.centralWidget()
        if self.drawer.pos().x() >= central.width():
            self.drawer.hide()

    def resizeEvent(self, event):
        # maintenir le drawer collé à droite lors du redimensionnement
        central = self.centralWidget()
        if self._drawer_open:
            self.drawer.move(central.width() - self.drawer_width, 0)
        else:
            self.drawer.move(central.width(), 0)
        super().resizeEvent(event)

    def myStyleSheet(self):
        try:
            with open("graphics/style.qss", "r") as styleFile:
                style = styleFile.read()
                self.setStyleSheet(style)
        except FileNotFoundError:
            pass
            """