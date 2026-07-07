from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Qt, QUrl, QItemSelectionModel
from PySide6.QtGui import QDesktopServices, QStandardItem, QStandardItemModel, QColor
from PySide6.QtWidgets import QAbstractItemView, QHeaderView, QHBoxLayout, QSizePolicy
from qfluentwidgets import (
    CaptionLabel, FluentIcon, MessageBoxBase,
    PrimaryToolButton, SubtitleLabel, ToolButton, ToolTipFilter,
)

from app.config.constants import AUTHOR_URL
from app.format import toReadableSize
from app.view.components.markdown_viewer import MarkdownViewer
from app.view.components.tree_view import AutoSizingTreeView

if TYPE_CHECKING:
    from app.update import Release, ReleaseAsset


class ReleaseInfoDialog(MessageBoxBase):
    def __init__(self, release: Release, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self._release = release

        self.versionLabel = SubtitleLabel(release.version, self)
        self.dateLabel = CaptionLabel(release.publishedAt[:10] if release.publishedAt else "", self)
        self.prereleaseLabel = CaptionLabel(self.tr("⚠️ 预发布版本"), self)
        self.detailButton = PrimaryToolButton(FluentIcon.LINK, self)
        self.sponsorButton = ToolButton(FluentIcon.HEART, self)
        self.descriptionEdit = MarkdownViewer(self, minimumVisibleLines=5, maximumVisibleLines=16)
        self.assetView = AutoSizingTreeView(self, minimumVisibleRows=1, maximumVisibleRows=6)
        self.assetModel = QStandardItemModel(self.assetView)
        self.titleLayout = QHBoxLayout()

        self._initWidget()
        self._initLayout()
        self._bind()

    def _initWidget(self) -> None:
        self.setShadowEffect(60, (0, 10), QColor(0, 0, 0, 50))
        self.setMaskColor(QColor(0, 0, 0, 76))
        self.widget.setMinimumWidth(min(580, self.width() - 48))
        self.yesButton.setText(self.tr("下载"))
        self.versionLabel.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.prereleaseLabel.setVisible(self._release.prerelease)
        self.detailButton.setToolTip(self.tr("打开发布页"))
        self.detailButton.installEventFilter(ToolTipFilter(self.detailButton))
        self.sponsorButton.setToolTip(self.tr("赞助作者"))
        self.sponsorButton.installEventFilter(ToolTipFilter(self.sponsorButton))

        self.descriptionEdit.setMarkdown(self._release.body or self.tr("暂无更新说明"))

        self.assetView.setRootIsDecorated(False)
        self.assetView.setUniformRowHeights(True)
        self.assetView.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.assetView.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.assetView.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)

        self.assetModel.setHorizontalHeaderLabels([self.tr("文件名"), self.tr("大小"), self.tr("下载次数")])
        self.assetView.setModel(self.assetModel)
        self.assetView.header().setStretchLastSection(True)
        self.assetView.header().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.assetView.header().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)

        from app.update import bestAsset
        best = bestAsset(self._release)
        best_row = -1

        for i, asset in enumerate(self._release.assets):
            row = [
                QStandardItem(asset.name),
                QStandardItem(toReadableSize(asset.size)),
                QStandardItem(str(asset.downloadCount)),
            ]
            row[0].setData(asset, Qt.ItemDataRole.UserRole)
            for item in row:
                item.setEditable(False)
            self.assetModel.appendRow(row)
            if best is not None and asset.name == best.name:
                best_row = i

        self.assetView.setVisible(bool(self._release.assets))
        if best_row >= 0:
            index = self.assetModel.index(best_row, 0)
            self.assetView.setCurrentIndex(index)
            sm = self.assetView.selectionModel()
            if sm is not None:
                sm.select(index, QItemSelectionModel.SelectionFlag.ClearAndSelect | QItemSelectionModel.SelectionFlag.Rows)

        if self._release.assets:
            needed = sum(self.assetView.sizeHintForColumn(i) for i in range(self.assetModel.columnCount()))
            self.widget.setMinimumWidth(max(self.widget.minimumWidth(), needed + 48 + 20))

    def _initLayout(self) -> None:
        self.titleLayout.setContentsMargins(0, 0, 0, 0)
        self.titleLayout.setSpacing(6)
        self.titleLayout.addWidget(self.versionLabel)
        self.titleLayout.addWidget(self.dateLabel)
        self.titleLayout.addWidget(self.prereleaseLabel)
        self.titleLayout.addStretch(1)
        self.titleLayout.addWidget(self.detailButton)
        self.titleLayout.addWidget(self.sponsorButton)

        self.viewLayout.addLayout(self.titleLayout)
        self.viewLayout.addSpacing(12)
        self.viewLayout.addWidget(self.descriptionEdit)
        self.viewLayout.addWidget(self.assetView)

    def _bind(self) -> None:
        self.detailButton.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(self._release.pageUrl)))
        self.sponsorButton.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(AUTHOR_URL)))

    def selectedAsset(self) -> ReleaseAsset | None:
        index = self.assetView.currentIndex()
        if not index.isValid():
            return None
        item = self.assetModel.itemFromIndex(index.siblingAtColumn(0))
        if item is None:
            return None
        return item.data(Qt.ItemDataRole.UserRole)

    def validate(self) -> bool:
        return self.selectedAsset() is not None

    def showEvent(self, e) -> None:
        from PySide6.QtWidgets import QDialog, QGraphicsOpacityEffect
        from PySide6.QtCore import QPropertyAnimation, QEasingCurve, QParallelAnimationGroup

        QDialog.showEvent(self, e)

        maskEffect = QGraphicsOpacityEffect(self.windowMask)
        self.windowMask.setGraphicsEffect(maskEffect)
        maskAni = QPropertyAnimation(maskEffect, b"opacity", self)
        maskAni.setStartValue(0)
        maskAni.setEndValue(1)
        maskAni.setDuration(200)
        maskAni.setEasingCurve(QEasingCurve.Type.OutQuad)

        widgetEffect = QGraphicsOpacityEffect(self.widget)
        self.widget.setGraphicsEffect(widgetEffect)
        widgetAni = QPropertyAnimation(widgetEffect, b"opacity", self)
        widgetAni.setStartValue(0)
        widgetAni.setEndValue(1)
        widgetAni.setDuration(200)
        widgetAni.setEasingCurve(QEasingCurve.Type.OutQuad)

        self._showGroup = QParallelAnimationGroup(self)
        self._showGroup.addAnimation(maskAni)
        self._showGroup.addAnimation(widgetAni)
        def _onShowFinished():
            self.windowMask.setGraphicsEffect(None)
            self.setShadowEffect(60, (0, 10), QColor(0, 0, 0, 50))
        self._showGroup.finished.connect(_onShowFinished)
        self._showGroup.start()

    def done(self, code: int) -> None:
        from PySide6.QtWidgets import QGraphicsOpacityEffect
        from PySide6.QtCore import QPropertyAnimation, QEasingCurve, QParallelAnimationGroup

        self.windowMask.setGraphicsEffect(None)
        self.widget.setGraphicsEffect(None)

        maskEffect = QGraphicsOpacityEffect(self.windowMask)
        self.windowMask.setGraphicsEffect(maskEffect)
        maskAni = QPropertyAnimation(maskEffect, b"opacity", self)
        maskAni.setStartValue(1)
        maskAni.setEndValue(0)
        maskAni.setDuration(120)
        maskAni.setEasingCurve(QEasingCurve.Type.InQuad)

        widgetEffect = QGraphicsOpacityEffect(self.widget)
        self.widget.setGraphicsEffect(widgetEffect)
        widgetAni = QPropertyAnimation(widgetEffect, b"opacity", self)
        widgetAni.setStartValue(1)
        widgetAni.setEndValue(0)
        widgetAni.setDuration(120)
        widgetAni.setEasingCurve(QEasingCurve.Type.InQuad)

        self._doneGroup = QParallelAnimationGroup(self)
        self._doneGroup.addAnimation(maskAni)
        self._doneGroup.addAnimation(widgetAni)
        self._doneGroup.finished.connect(lambda: self._onDone(code))
        self._doneGroup.start()
