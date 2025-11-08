from PySide6.QtWidgets import (QWidget, QStackedWidget, QPushButton,
                                 QHBoxLayout, QVBoxLayout, QSizePolicy, QButtonGroup)
from PySide6.QtCore import Qt


class StackedCustom(QWidget):
    """Widget composé : barre de boutons en haut (onglets) et QStackedWidget en bas.

    Usage :
      sc = StackedCustom(parent)
      sc.add_page(widget, title)
      sc.set_pages([w1, w2], ["T1", "T2"])  # optionnel
      sc.set_current(1)
    """

    def __init__(self, parent=None, page_widgets=None, titles=None, tab_height=36):
        super().__init__(parent=parent)
        self._tab_height = tab_height

        # Top: boutons
        self._top = QWidget(self)
        self._top_layout = QHBoxLayout(self._top)
        self._top_layout.setContentsMargins(0, 0, 0, 0)
        self._top_layout.setSpacing(4)

        # Group pour gérer l'état checked des boutons
        self._btn_group = QButtonGroup(self)
        self._btn_group.setExclusive(True)

        # Bottom: stacked widget
        self.stack = QStackedWidget(self)

        # Layout principal
        main = QVBoxLayout(self)
        main.setContentsMargins(0, 0, 0, 0)
        main.setSpacing(2)
        main.addWidget(self._top)
        main.addWidget(self.stack, 1)

        # tracking
        self._buttons = []

        # synchroniser l'état boutons quand la page change
        self.stack.currentChanged.connect(self._on_current_changed)

        if page_widgets:
            self.set_pages(page_widgets, titles)

    def add_page(self, widget, title=None):
        """Ajoute une page et crée le bouton correspondant. Retourne l'index."""
        idx = self.stack.addWidget(widget)
        btn_text = title or f"Page {idx + 1}"
        btn = QPushButton(btn_text, self._top)
        btn.setCheckable(True)
        btn.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        btn.setFixedHeight(self._tab_height)

        # connexion : changer la page quand le bouton est cliqué
        btn.clicked.connect(lambda checked, i=idx: self.set_current(i))

        self._top_layout.addWidget(btn)
        self._btn_group.addButton(btn, idx)
        self._buttons.append(btn)

        # si première page ajoutée, la sélectionner
        if self.stack.count() == 1:
            btn.setChecked(True)
            self.stack.setCurrentIndex(0)

        return idx

    def set_pages(self, widgets, titles=None):
        """Remplace les pages existantes par la liste fournie."""
        # vider boutons et pages
        for b in self._buttons:
            self._btn_group.removeButton(b)
            b.deleteLater()
        self._buttons = []

        while self.stack.count():
            w = self.stack.widget(0)
            self.stack.removeWidget(w)
            w.setParent(None)

        if titles is None:
            titles = [None] * len(widgets)

        for w, t in zip(widgets, titles):
            self.add_page(w, t)

    def set_current(self, index: int):
        """Sélectionne la page index et met à jour le bouton coché."""
        if 0 <= index < self.stack.count():
            self.stack.setCurrentIndex(index)
            btn = self._btn_group.button(index)
            if btn:
                btn.setChecked(True)

    def current_index(self) -> int:
        return self.stack.currentIndex()

    def _on_current_changed(self, index: int):
        # mettre à jour l'état checked du bouton
        btn = self._btn_group.button(index)
        if btn:
            btn.setChecked(True)

    # petites utilitaires
    def page_count(self) -> int:
        return self.stack.count()

    def remove_page(self, index: int):
        if 0 <= index < self.stack.count():
            btn = self._btn_group.button(index)
            if btn:
                self._btn_group.removeButton(btn)
                self._buttons[index].deleteLater()
                del self._buttons[index]
            w = self.stack.widget(index)
            self.stack.removeWidget(w)
            w.setParent(None)
            # ré-indexer button ids
            for i, b in enumerate(self._buttons):
                self._btn_group.setId(b, i)