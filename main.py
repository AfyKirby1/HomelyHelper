# main.py – Homely Helper v0.4
"""A furniture-layout planner with advanced interaction and visual features.

Changes in v0.4
────────────────
1. Mouse wheel zoom in canvas area
2. Zoom +/- buttons overlay in bottom-right corner
3. Unit-aware text display (updates with measurement changes)
4. Room border toggle for precise edge placement
5. Delete functionality (X button + Delete key)
6. Fixed settings application for font/canvas scaling
7. Floor texture system (carpet, wood, tile)
8. Enhanced visual feedback and polish
"""

from __future__ import annotations

import json
import sys
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional

from PyQt6.QtCore import Qt, QRectF, QPointF, QSettings, pyqtSignal, QTimer
from PyQt6.QtGui import QColor, QBrush, QPainter, QFont, QAction, QPalette, QWheelEvent, QKeyEvent, QPixmap, QPen, QPolygonF
from PyQt6.QtWidgets import (
    QApplication,
    QColorDialog,
    QComboBox,
    QDialog,
    QDoubleSpinBox,
    QFormLayout,
    QFrame,
    QGraphicsItem,
    QGraphicsRectItem,
    QGraphicsPolygonItem,
    QGraphicsScene,
    QGraphicsView,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMenuBar,
    QPushButton,
    QSlider,
    QSpinBox,
    QVBoxLayout,
    QWidget,
    QMessageBox,
    QCheckBox,
    QButtonGroup,
    QRadioButton,
    QMenu,
    QFileDialog,
)

# ────────────────────────────────────────────────────────────────
# Theme system
# ────────────────────────────────────────────────────────────────
class Theme:
    """Theme definitions for the application."""
    
    LIGHT = {
        'name': 'Light',
        'window_bg': '#f5f5f5',
        'panel_bg': '#ffffff',
        'canvas_bg': '#fafafa',
        'room_border': '#333333',
        'text_color': '#2c2c2c',
        'accent_color': '#0078d4',
        'button_bg': '#e1e1e1',
        'button_hover': '#d1d1d1',
        'input_bg': '#ffffff',
        'input_border': '#cccccc',
    }
    
    DARK = {
        'name': 'Dark',
        'window_bg': '#2b2b2b',
        'panel_bg': '#3c3c3c',
        'canvas_bg': '#1e1e1e',
        'room_border': '#888888',
        'text_color': '#ffffff',
        'accent_color': '#0078d4',
        'button_bg': '#4a4a4a',
        'button_hover': '#5a5a5a',
        'input_bg': '#3c3c3c',
        'input_border': '#666666',
    }
    
    MIXED = {
        'name': 'Mixed',
        'window_bg': '#e8e8e8',
        'panel_bg': '#3c3c3c',
        'canvas_bg': '#f0f0f0',
        'room_border': '#555555',
        'text_color': '#ffffff',
        'accent_color': '#ff6b35',
        'button_bg': '#4a4a4a',
        'button_hover': '#5a5a5a',
        'input_bg': '#3c3c3c',
        'input_border': '#666666',
    }

# ────────────────────────────────────────────────────────────────
# Floor textures
# ────────────────────────────────────────────────────────────────
class FloorTexture:
    """Floor texture definitions."""
    
    TEXTURES = {
        'None': {'color': '#fafafa', 'pattern': None},
        'Hardwood': {'color': '#d2b48c', 'pattern': 'wood'},
        'Carpet': {'color': '#dda0dd', 'pattern': 'carpet'},
        'Tile': {'color': '#f0f8ff', 'pattern': 'tile'},
        'Concrete': {'color': '#c0c0c0', 'pattern': 'concrete'},
    }

# ────────────────────────────────────────────────────────────────
# Utility: unit conversion
# ────────────────────────────────────────────────────────────────
_UNIT_FACTORS: Dict[str, float] = {"m": 1.0, "ft": 0.3048, "in": 0.0254}

def to_m(value: float, unit: str) -> float:
    """Convert *value* in *unit* (m/ft/in) to metres."""
    return value * _UNIT_FACTORS[unit]

def from_m(value_m: float, unit: str) -> float:
    """Convert *value_m* in metres to *unit*."""
    return value_m / _UNIT_FACTORS[unit]

def format_dimension(value_m: float, unit: str) -> str:
    """Format a dimension value for display."""
    converted = from_m(value_m, unit)
    return f"{converted:.2f} {unit}"

# ────────────────────────────────────────────────────────────────
# Data-model classes
# ────────────────────────────────────────────────────────────────
@dataclass
class Furniture:
    name: str
    width_m: float
    depth_m: float
    colour: QColor
    x_m: float = field(default=0.0)
    y_m: float = field(default=0.0)
    rotation: float = field(default=0.0)  # rotation in degrees

@dataclass
class DoorWindow:
    """Data class for doors and windows."""
    name: str
    width_m: float
    thickness_m: float
    x_m: float = field(default=0.0)
    y_m: float = field(default=0.0)
    is_door: bool = field(default=True)

class DoorItem(QGraphicsRectItem):
    """Interactive door with opening animation and rotation."""
    
    def __init__(self, door_window: DoorWindow, scale: float, parent_planner):
        super().__init__(0, 0, door_window.width_m * scale, door_window.thickness_m * scale)
        self.door_window = door_window
        self.scale = scale
        self.parent_planner = parent_planner
        self.is_open = False
        self.opening_arc = None  # For door opening visualization
        
        self.setBrush(QBrush(QColor(255, 255, 255)))  # White door
        self.setPen(QPen(QColor(100, 100, 100), 2))  # Gray border
        self.setToolTip(f"{door_window.name} - Right-click for options, Double-click to open/close")
        
        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsMovable
            | QGraphicsItem.GraphicsItemFlag.ItemIsSelectable
        )
        self.setAcceptHoverEvents(True)
    
    def mouseDoubleClickEvent(self, event):
        """Toggle door open/closed on double-click."""
        if self.door_window.is_door:  # Only doors can open/close
            self.toggle_door()
        super().mouseDoubleClickEvent(event)
    
    def toggle_door(self):
        """Toggle door between open and closed states."""
        if not self.door_window.is_door:
            return
            
        self.is_open = not self.is_open
        
        # Remove existing opening arc
        if self.opening_arc and self.opening_arc.scene():
            self.opening_arc.scene().removeItem(self.opening_arc)
            self.opening_arc = None
        
        if self.is_open:
            # Create door opening arc
            self._create_opening_arc()
            self.setBrush(QBrush(QColor(255, 255, 255, 150)))  # Semi-transparent
            self.setToolTip(f"{self.door_window.name} (Open) - Right-click for options, Double-click to close")
        else:
            # Closed door - solid white
            self.setBrush(QBrush(QColor(255, 255, 255)))
            self.setToolTip(f"{self.door_window.name} (Closed) - Right-click for options, Double-click to open")
    
    def _create_opening_arc(self):
        """Create a visual arc showing door opening path."""
        door_width = self.door_window.width_m * self.scale
        
        # Create arc polygon (90-degree arc)
        points = []
        center_x = 0
        center_y = 0
        radius = door_width
        
        # Create quarter circle
        for angle in range(0, 91, 5):  # 0 to 90 degrees, every 5 degrees
            rad = math.radians(angle)
            x = center_x + radius * math.cos(rad)
            y = center_y + radius * math.sin(rad)
            points.append(QPointF(x, y))
        
        # Add center point to close the arc
        points.append(QPointF(center_x, center_y))
        
        polygon = QPolygonF(points)
        self.opening_arc = QGraphicsPolygonItem(polygon)
        self.opening_arc.setBrush(QBrush(QColor(100, 200, 100, 50)))  # Light green, very transparent
        self.opening_arc.setPen(QPen(QColor(100, 200, 100, 100), 1, Qt.PenStyle.DashLine))
        
        # Position relative to door
        self.opening_arc.setPos(self.pos())
        self.scene().addItem(self.opening_arc)
    
    def contextMenuEvent(self, event):
        """Show right-click context menu."""
        menu = QMenu()
        
        if self.door_window.is_door:
            if self.is_open:
                close_action = menu.addAction("Close Door")
                close_action.triggered.connect(self.toggle_door)
            else:
                open_action = menu.addAction("Open Door")
                open_action.triggered.connect(self.toggle_door)
            
            menu.addSeparator()
        
        rotate_action = menu.addAction("Rotate 90°")
        rotate_action.triggered.connect(self.rotate_90)
        
        delete_action = menu.addAction("Delete")
        delete_action.triggered.connect(self.delete_self)
        
        menu.exec(event.screenPos())
    
    def rotate_90(self):
        """Rotate the door/window by 90 degrees."""
        current_rotation = self.rotation()
        self.setRotation(current_rotation + 90)
    
    def delete_self(self):
        """Delete this door/window item."""
        # Remove opening arc if it exists
        if self.opening_arc and self.opening_arc.scene():
            self.opening_arc.scene().removeItem(self.opening_arc)
        
        # Remove from parent's tracking list and scene
        if self in self.parent_planner.door_items:
            self.parent_planner.door_items.remove(self)
        
        # Remove from furniture list
        self.parent_planner._remove_door_from_list(self.door_window.name)
        
        if self.scene():
            self.scene().removeItem(self)

class FurnitureItem(QGraphicsRectItem):
    """Draggable rectangle with enhanced visual styling, delete button, and rotation."""

    def __init__(self, furn: Furniture, scale: float, parent_planner):
        super().__init__(0, 0, furn.width_m * scale, furn.depth_m * scale)
        self.furn = furn
        self.scale = scale
        self.parent_planner = parent_planner
        self.setBrush(QBrush(furn.colour))
        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsMovable
            | QGraphicsItem.GraphicsItemFlag.ItemIsSelectable
            | QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges
        )
        self.setAcceptHoverEvents(True)
        self.setToolTip(f"{furn.name}\n{furn.width_m:.2f}m × {furn.depth_m:.2f}m\nPress R to rotate, Delete to remove")
        
        # Add subtle border
        pen = self.pen()
        pen.setColor(QColor(0, 0, 0, 100))
        pen.setWidth(1)
        self.setPen(pen)
        
        # Set initial rotation
        self.setRotation(furn.rotation)
        
        # Control buttons
        self.delete_button = None
        self.rotate_button = None
        self.buttons_visible = False
        self._create_control_buttons()
        self._hide_control_buttons()  # Start hidden

    def _create_control_buttons(self):
        """Create delete and rotate button overlays."""
        button_size = 18
        
        # Delete button (X)
        self.delete_button = QPushButton("×")
        self.delete_button.setFixedSize(button_size, button_size)
        self.delete_button.setStyleSheet("""
            QPushButton {
                background-color: #ff4444;
                color: white;
                border: none;
                border-radius: 9px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #ff6666;
            }
        """)
        self.delete_button.clicked.connect(self.delete_self)
        
        # Rotate button (↻)
        self.rotate_button = QPushButton("↻")
        self.rotate_button.setFixedSize(button_size, button_size)
        self.rotate_button.setStyleSheet("""
            QPushButton {
                background-color: #4a90e2;
                color: white;
                border: none;
                border-radius: 9px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #6ba3f0;
            }
        """)
        self.rotate_button.clicked.connect(self.rotate_90)
        
        # Position buttons in scene
        self._position_control_buttons()
    
    def _position_control_buttons(self):
        """Position control buttons relative to furniture item."""
        if not self.scene():
            return
            
        button_size = 18
        margin = 2
        
        # Delete button (top-right)
        delete_proxy = None
        rotate_proxy = None
        
        # Find existing button proxies
        for item in self.scene().items():
            if hasattr(item, 'widget'):
                if item.widget() == self.delete_button:
                    delete_proxy = item
                elif item.widget() == self.rotate_button:
                    rotate_proxy = item
        
        # Create proxies if they don't exist
        if not delete_proxy:
            delete_proxy = self.scene().addWidget(self.delete_button)
        if not rotate_proxy:
            rotate_proxy = self.scene().addWidget(self.rotate_button)
        
        # Position buttons
        item_rect = self.rect()
        item_pos = self.pos()
        
        # Delete button: top-right corner
        delete_proxy.setPos(
            item_pos.x() + item_rect.width() - button_size + margin,
            item_pos.y() - margin
        )
        
        # Rotate button: top-left corner
        rotate_proxy.setPos(
            item_pos.x() - margin,
            item_pos.y() - margin
        )
        
        # Ensure buttons stay on top
        delete_proxy.setZValue(1000)
        rotate_proxy.setZValue(1000)
        
        # Update visibility
        delete_proxy.setVisible(self.buttons_visible)
        rotate_proxy.setVisible(self.buttons_visible)
    
    def _show_control_buttons(self):
        """Show control buttons."""
        self.buttons_visible = True
        # Recreate buttons to avoid artifacts
        self._create_control_buttons()
        self._position_control_buttons()
    
    def _hide_control_buttons(self):
        """Hide control buttons."""
        self.buttons_visible = False
        if self.scene():
            for item in self.scene().items():
                if hasattr(item, 'widget'):
                    widget = item.widget()
                    if widget == self.delete_button or widget == self.rotate_button:
                        item.setVisible(False)
                        # Remove from scene to prevent artifacts
                        self.scene().removeItem(item)

    def delete_self(self):
        """Remove this furniture item."""
        # Hide control buttons first
        self._hide_control_buttons()
        # Remove from parent's tracking
        self.parent_planner.remove_furniture_item(self)
    
    def rotate_90(self):
        """Rotate furniture by 90 degrees."""
        self.furn.rotation = (self.furn.rotation + 90) % 360
        self.setRotation(self.furn.rotation)
        
        # Update list display to show rotation
        self.parent_planner.update_furniture_list_item(self.furn)
        
        # Reposition buttons after rotation
        self._position_control_buttons()
    
    def copy_furniture(self):
        """Copy this furniture to clipboard."""
        self.parent_planner.copy_furniture(self.furn)
    
    def contextMenuEvent(self, event):
        """Show right-click context menu."""
        menu = QMenu()
        
        copy_action = menu.addAction("Copy")
        copy_action.triggered.connect(self.copy_furniture)
        
        rotate_action = menu.addAction("Rotate 90°")
        rotate_action.triggered.connect(self.rotate_90)
        
        menu.addSeparator()
        
        delete_action = menu.addAction("Delete")
        delete_action.triggered.connect(self.delete_self)
        
        menu.exec(event.screenPos())
    
    def hoverEnterEvent(self, event):
        """Show buttons when mouse enters."""
        self._show_control_buttons()
        super().hoverEnterEvent(event)
    
    def hoverLeaveEvent(self, event):
        """Hide buttons when mouse leaves (unless selected)."""
        if not self.isSelected():
            self._hide_control_buttons()
        super().hoverLeaveEvent(event)

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange:
            # Handle border collision if enabled
            if self.parent_planner.snap_to_borders:
                new_pos = value
                room_width_px = self.parent_planner.room_width_m * self.scale
                room_height_px = self.parent_planner.room_depth_m * self.scale
                
                # Get furniture dimensions
                furniture_width = self.rect().width()
                furniture_height = self.rect().height()
                
                # Constrain to room boundaries
                x = max(0, min(new_pos.x(), room_width_px - furniture_width))
                y = max(0, min(new_pos.y(), room_height_px - furniture_height))
                
                return QPointF(x, y)
        elif change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            pos_px: QPointF = self.pos()
            self.furn.x_m = pos_px.x() / self.scale
            self.furn.y_m = pos_px.y() / self.scale
            
            # Update control button positions
            self._position_control_buttons()
        elif change == QGraphicsItem.GraphicsItemChange.ItemSelectedHasChanged:
            # Show/hide buttons based on selection
            if self.isSelected():
                self._show_control_buttons()
            else:
                self._hide_control_buttons()
                        
        return super().itemChange(change, value)

# ────────────────────────────────────────────────────────────────
# Custom Graphics View with zoom
# ────────────────────────────────────────────────────────────────
class ZoomableGraphicsView(QGraphicsView):
    """Graphics view with mouse wheel zoom and zoom buttons."""
    
    def __init__(self, scene, parent=None):
        super().__init__(scene, parent)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        self.zoom_factor = 1.0
        self.min_zoom = 0.1
        self.max_zoom = 5.0
        self.main_window = None  # Will be set by parent
        
        # Create zoom buttons
        self._create_zoom_buttons()
    
    def _create_zoom_buttons(self):
        """Create floating zoom +/- buttons in bottom-right corner."""
        self.zoom_in_btn = QPushButton("🔍+")
        self.zoom_out_btn = QPushButton("🔍−")
        
        for btn in [self.zoom_in_btn, self.zoom_out_btn]:
            btn.setFixedSize(35, 35)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: rgba(255, 255, 255, 200);
                    border: 2px solid #ccc;
                    border-radius: 17px;
                    font-size: 12px;
                    font-weight: bold;
                    color: #333;
                }
                QPushButton:hover {
                    background-color: rgba(255, 255, 255, 255);
                    border-color: #999;
                }
            """)
        
        self.zoom_in_btn.clicked.connect(self.zoom_in)
        self.zoom_out_btn.clicked.connect(self.zoom_out)
        
        # Position buttons (will be updated in resizeEvent)
        self._position_zoom_buttons()
    
    def _position_zoom_buttons(self):
        """Position zoom buttons in bottom-right corner."""
        margin = 20
        btn_spacing = 35
        
        self.zoom_in_btn.setParent(self)
        self.zoom_out_btn.setParent(self)
        
        self.zoom_in_btn.move(
            self.width() - margin - 30,
            self.height() - margin - 30
        )
        self.zoom_out_btn.move(
            self.width() - margin - 30,
            self.height() - margin - 30 - btn_spacing
        )
        
        # Ensure buttons stay on top
        self.zoom_in_btn.raise_()
        self.zoom_out_btn.raise_()
    
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._position_zoom_buttons()
    
    def wheelEvent(self, event: QWheelEvent):
        """Handle mouse wheel zoom."""
        if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            # Zoom with Ctrl+Wheel
            zoom_in = event.angleDelta().y() > 0
            if zoom_in:
                self.zoom_in()
            else:
                self.zoom_out()
        else:
            # Normal scroll
            super().wheelEvent(event)
    
    def zoom_in(self):
        """Zoom in by 20%."""
        if self.zoom_factor < self.max_zoom:
            self.scale(1.2, 1.2)
            self.zoom_factor *= 1.2
    
    def zoom_out(self):
        """Zoom out by 20%."""
        if self.zoom_factor > self.min_zoom:
            self.scale(0.8, 0.8)
            self.zoom_factor *= 0.8
    
    # Context menu removed to fix buggy behavior

# ────────────────────────────────────────────────────────────────
# Door/Window sizing dialog
# ────────────────────────────────────────────────────────────────
class DoorWindowDialog(QDialog):
    """Dialog for setting door/window dimensions."""
    
    def __init__(self, is_door=True, parent=None):
        super().__init__(parent)
        self.is_door = is_door
        self.setWindowTitle(f"Add {'Door' if is_door else 'Window'}")
        self.setModal(True)
        self.resize(350, 200)
        
        layout = QVBoxLayout(self)
        
        # Form for dimensions
        form_group = QGroupBox(f"{'Door' if is_door else 'Window'} Dimensions")
        form_layout = QFormLayout(form_group)
        
        # Name input
        self.name_input = QLineEdit()
        default_name = f"{'Door' if is_door else 'Window'} 1"
        self.name_input.setText(default_name)
        form_layout.addRow("Name:", self.name_input)
        
        # Width input
        self.width_spin = QDoubleSpinBox()
        self.width_spin.setRange(0.1, 10.0)
        self.width_spin.setValue(1.0 if is_door else 1.5)  # 1m door, 1.5m window
        self.width_spin.setSuffix(" m")
        self.width_spin.setDecimals(2)
        form_layout.addRow("Width:", self.width_spin)
        
        # Thickness input
        self.thickness_spin = QDoubleSpinBox()
        self.thickness_spin.setRange(0.05, 1.0)
        self.thickness_spin.setValue(0.1 if is_door else 0.2)  # 10cm door, 20cm window
        self.thickness_spin.setSuffix(" m")
        self.thickness_spin.setDecimals(2)
        form_layout.addRow("Thickness:", self.thickness_spin)
        
        layout.addWidget(form_group)
        layout.addStretch()
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        ok_btn = QPushButton("Add")
        ok_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)
    
    def get_door_window_data(self):
        """Return the door/window data."""
        return DoorWindow(
            name=self.name_input.text(),
            width_m=self.width_spin.value(),
            thickness_m=self.thickness_spin.value(),
            is_door=self.is_door
        )

# ────────────────────────────────────────────────────────────────
# Settings dialog
# ────────────────────────────────────────────────────────────────
class SettingsDialog(QDialog):
    theme_changed = pyqtSignal(dict)
    font_size_changed = pyqtSignal(int)
    scale_changed = pyqtSignal(int)
    settings_applied = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setModal(True)
        self.resize(450, 450)
        self.parent_window = parent
        
        layout = QVBoxLayout(self)
        
        # Theme selection
        theme_group = QGroupBox("Theme")
        theme_layout = QFormLayout(theme_group)
        
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Light", "Dark", "Mixed"])
        self.theme_combo.currentTextChanged.connect(self.on_theme_changed)
        theme_layout.addRow("Theme:", self.theme_combo)
        
        # Display settings
        display_group = QGroupBox("Display")
        display_layout = QFormLayout(display_group)
        
        self.font_slider = QSlider(Qt.Orientation.Horizontal)
        self.font_slider.setRange(8, 24)
        self.font_slider.setValue(11)
        self.font_slider.valueChanged.connect(self.on_font_changed)
        
        self.font_label = QLabel("11pt")
        display_layout.addRow("Font size:", self._hbox(self.font_slider, self.font_label))
        
        # Canvas scale
        self.scale_slider = QSlider(Qt.Orientation.Horizontal)
        self.scale_slider.setRange(30, 120)
        self.scale_slider.setValue(60)
        self.scale_slider.valueChanged.connect(self.on_scale_changed)
        
        self.scale_label = QLabel("60px/m")
        display_layout.addRow("Canvas scale:", self._hbox(self.scale_slider, self.scale_label))
        
        # Preview note
        preview_label = QLabel("💡 Changes apply immediately for preview")
        preview_label.setStyleSheet("color: #666; font-style: italic; padding: 5px;")
        display_layout.addRow(preview_label)
        
        layout.addWidget(theme_group)
        layout.addWidget(display_group)
        layout.addStretch()
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        # Apply button for immediate changes
        apply_btn = QPushButton("Apply")
        apply_btn.setToolTip("Apply changes immediately")
        apply_btn.clicked.connect(self.apply_settings)
        
        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(self.accept_and_apply)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        
        btn_layout.addWidget(apply_btn)
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)
    
    def _hbox(self, *widgets):
        box = QHBoxLayout()
        for w in widgets:
            box.addWidget(w)
        container = QWidget()
        container.setLayout(box)
        return container
    
    def on_theme_changed(self, theme_name):
        themes = {"Light": Theme.LIGHT, "Dark": Theme.DARK, "Mixed": Theme.MIXED}
        if self.parent_window:
            self.parent_window._apply_theme(themes[theme_name])
    
    def on_font_changed(self, size):
        self.font_label.setText(f"{size}pt")
        if self.parent_window:
            self.parent_window._set_font_size(size)
    
    def on_scale_changed(self, scale):
        self.scale_label.setText(f"{scale}px/m")
        if self.parent_window:
            self.parent_window._set_canvas_scale(scale)
    
    def apply_settings(self):
        """Apply all current settings immediately."""
        if self.parent_window:
            # Apply theme
            theme_name = self.theme_combo.currentText()
            themes = {"Light": Theme.LIGHT, "Dark": Theme.DARK, "Mixed": Theme.MIXED}
            self.parent_window._apply_theme(themes[theme_name])
            
            # Apply font size
            self.parent_window._set_font_size(self.font_slider.value())
            
            # Apply canvas scale
            self.parent_window._set_canvas_scale(self.scale_slider.value())
            
            # Save settings
            self.parent_window._save_settings()
        
        self.settings_applied.emit()
    
    def accept_and_apply(self):
        """Apply settings and close dialog."""
        self.apply_settings()
        self.accept()

# ────────────────────────────────────────────────────────────────
# Main window
# ────────────────────────────────────────────────────────────────
class RoomPlanner(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Homely Helper – Room Planner")
        self.resize(1400, 800)
        
        # Settings
        self.settings = QSettings("HomelyHelper", "RoomPlanner")
        self.current_theme = Theme.LIGHT
        self.font_size = 11
        self.pixels_per_m = 60
        self.show_room_border = True
        self.current_floor_texture = 'None'
        self.current_room_unit = 'ft'  # Default to feet for rooms
        self.current_furniture_unit = 'in'  # Default to inches for furniture
        self.clipboard_furniture = None  # For copy/paste functionality
        
        # Central widget setup
        central = QWidget()
        self.setCentralWidget(central)
        
        # Initialize room variables first
        self.room_width_m = to_m(16.0, 'ft')  # 16 feet default
        self.room_depth_m = to_m(12.0, 'ft')  # 12 feet default
        self.room_name = "My Room"  # Default room name
        self._room_rect_item: QGraphicsRectItem | None = None
        self.furniture_items = []  # Track furniture items for deletion
        self.door_items = []  # Track door items
        self.snap_to_borders = False  # Border collision toggle
        self.door_counter = 1  # Counter for door naming
        self.window_counter = 1  # Counter for window naming
        
        self._setup_ui()
        self._setup_menubar()  # Setup menu after UI so canvas exists
        self._apply_theme(self.current_theme)
        self.draw_room_border()
        
        # Load settings
        self._load_settings()
        
        # Enable keyboard focus for delete key
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
    
    def _setup_menubar(self):
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("File")
        
        new_action = QAction("New Room", self)
        new_action.setShortcut("Ctrl+N")
        new_action.triggered.connect(self.new_room)
        file_menu.addAction(new_action)
        
        file_menu.addSeparator()
        
        save_action = QAction("Save Layout...", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self.save_layout)
        file_menu.addAction(save_action)
        
        load_action = QAction("Load Layout...", self)
        load_action.setShortcut("Ctrl+O")
        load_action.triggered.connect(self.load_layout)
        file_menu.addAction(load_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # View menu
        view_menu = menubar.addMenu("View")
        
        zoom_in = QAction("Zoom In", self)
        zoom_in.setShortcut("Ctrl++")
        zoom_in.triggered.connect(self.canvas.zoom_in)
        view_menu.addAction(zoom_in)
        
        zoom_out = QAction("Zoom Out", self)
        zoom_out.setShortcut("Ctrl+-")
        zoom_out.triggered.connect(self.canvas.zoom_out)
        view_menu.addAction(zoom_out)
        
        view_menu.addSeparator()
        
        border_action = QAction("Toggle Room Border", self)
        border_action.setShortcut("Ctrl+B")
        border_action.triggered.connect(self.toggle_room_border)
        view_menu.addAction(border_action)
        
        view_menu.addSeparator()
        
        rotate_action = QAction("Rotate Selected", self)
        rotate_action.setShortcut("R")
        rotate_action.triggered.connect(self.rotate_selected_furniture)
        view_menu.addAction(rotate_action)
        
        # Edit menu
        edit_menu = menubar.addMenu("Edit")
        
        copy_action = QAction("Copy", self)
        copy_action.setShortcut("Ctrl+C")
        copy_action.triggered.connect(self.copy_selected_furniture)
        edit_menu.addAction(copy_action)
        
        paste_action = QAction("Paste", self)
        paste_action.setShortcut("Ctrl+V")
        paste_action.triggered.connect(self.paste_furniture_center)
        edit_menu.addAction(paste_action)
        
        duplicate_action = QAction("Duplicate", self)
        duplicate_action.setShortcut("Ctrl+D")
        duplicate_action.triggered.connect(self.duplicate_selected_furniture)
        edit_menu.addAction(duplicate_action)
        
        # Settings menu
        settings_menu = menubar.addMenu("Settings")
        
        prefs_action = QAction("Preferences...", self)
        prefs_action.triggered.connect(self.show_settings)
        settings_menu.addAction(prefs_action)
        
        # Help menu
        help_menu = menubar.addMenu("Help")
        
        homely_help_action = QAction("Homely Help", self)
        homely_help_action.triggered.connect(self.show_homely_help)
        help_menu.addAction(homely_help_action)
        
        help_menu.addSeparator()
        
        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def _setup_ui(self):
        central = self.centralWidget()
        
        # Scene / Canvas (center)
        self.scene = QGraphicsScene()
        self.canvas = ZoomableGraphicsView(self.scene)
        self.canvas.main_window = self  # Set reference for context menu
        
        # Right panel: furniture list with header
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(5, 5, 5, 5)
        
        # Items list header
        items_header = QLabel("Your Stuff")
        items_header.setStyleSheet("font-weight: bold; font-size: 14px; padding: 5px; color: #333;")
        right_layout.addWidget(items_header)
        
        self.list_widget = QListWidget()
        self.list_widget.setFrameShape(QFrame.Shape.StyledPanel)
        self.list_widget.setMinimumWidth(250)
        right_layout.addWidget(self.list_widget)
        
        # Left panel: controls
        self._build_control_panel()
        
        # Layout
        layout = QHBoxLayout(central)
        layout.addWidget(self.control_panel, 0)
        layout.addWidget(self.canvas, 1)
        layout.addWidget(right_panel, 0)
    
    def _build_control_panel(self):
        self.control_panel = QWidget()
        self.control_panel.setMinimumWidth(300)
        layout = QVBoxLayout(self.control_panel)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        # Room size group
        room_box = QGroupBox("Room Dimensions")
        room_layout = QFormLayout(room_box)
        
        # Room name
        self.room_name_input = QLineEdit()
        self.room_name_input.setText(self.room_name)
        self.room_name_input.setPlaceholderText("Enter room name...")
        self.room_name_input.textChanged.connect(self.on_room_name_changed)
        room_layout.addRow("Name:", self.room_name_input)
        
        self.room_w_spin = QDoubleSpinBox()
        self.room_w_spin.setRange(1, 1000)
        self.room_w_spin.setValue(16.0)  # Default room width in feet
        self.room_w_unit = QComboBox()
        self.room_w_unit.addItems(["m", "ft", "in"])
        self.room_w_unit.setCurrentText("ft")
        self.room_w_unit.currentTextChanged.connect(self._update_room_unit_display)
        room_layout.addRow("Width:", self._hbox(self.room_w_spin, self.room_w_unit))
        
        self.room_d_spin = QDoubleSpinBox()
        self.room_d_spin.setRange(1, 1000)
        self.room_d_spin.setValue(12.0)  # Default room depth in feet
        self.room_d_unit = QComboBox()
        self.room_d_unit.addItems(["m", "ft", "in"])
        self.room_d_unit.setCurrentText("ft")
        self.room_d_unit.currentTextChanged.connect(self._update_room_unit_display)
        room_layout.addRow("Depth:", self._hbox(self.room_d_spin, self.room_d_unit))
        
        room_apply = QPushButton("Apply Room Size")
        room_apply.setStyleSheet("QPushButton { font-weight: bold; padding: 8px; }")
        room_apply.clicked.connect(self.on_room_apply)
        room_layout.addRow(room_apply)
        
        # Room options
        self.border_checkbox = QCheckBox("Show room border")
        self.border_checkbox.setChecked(True)
        self.border_checkbox.toggled.connect(self.toggle_room_border)
        room_layout.addRow(self.border_checkbox)
        
        # Snap to borders option
        self.snap_checkbox = QCheckBox("Lock items to room edges")
        self.snap_checkbox.setChecked(False)
        self.snap_checkbox.toggled.connect(self.toggle_snap_to_borders)
        room_layout.addRow(self.snap_checkbox)
        
        # Floor texture
        floor_group = QGroupBox("Floor Texture")
        floor_layout = QFormLayout(floor_group)
        
        self.floor_combo = QComboBox()
        self.floor_combo.addItems(list(FloorTexture.TEXTURES.keys()))
        self.floor_combo.currentTextChanged.connect(self.on_floor_changed)
        floor_layout.addRow("Texture:", self.floor_combo)
        
        # Room Features group
        features_group = QGroupBox("Room Features")
        features_layout = QFormLayout(features_group)
        
        # Door controls
        door_button = QPushButton("Add Door")
        door_button.clicked.connect(self.add_door)
        features_layout.addRow("", door_button)
        
        # Window controls
        window_button = QPushButton("Add Window")
        window_button.clicked.connect(self.add_window)
        features_layout.addRow("", window_button)
        
        # Furniture group
        furn_box = QGroupBox("Add Furniture")
        furn_layout = QFormLayout(furn_box)
        
        self.f_name = QLineEdit()
        self.f_name.setPlaceholderText("e.g., Dining Table")
        furn_layout.addRow("Name:", self.f_name)
        
        self.f_w_spin = QDoubleSpinBox()
        self.f_w_spin.setRange(1, 1000)
        self.f_w_spin.setValue(72)  # Default table width in inches
        self.f_w_unit = QComboBox()
        self.f_w_unit.addItems(["m", "ft", "in"])
        self.f_w_unit.setCurrentText("in")
        self.f_w_unit.currentTextChanged.connect(self._update_furniture_unit_display)
        furn_layout.addRow("Width:", self._hbox(self.f_w_spin, self.f_w_unit))
        
        self.f_d_spin = QDoubleSpinBox()
        self.f_d_spin.setRange(1, 1000)
        self.f_d_spin.setValue(36)  # Default table depth in inches
        self.f_d_unit = QComboBox()
        self.f_d_unit.addItems(["m", "ft", "in"])
        self.f_d_unit.setCurrentText("in")
        self.f_d_unit.currentTextChanged.connect(self._update_furniture_unit_display)
        furn_layout.addRow("Depth:", self._hbox(self.f_d_spin, self.f_d_unit))
        
        self.f_colour = QColor("#4a90e2")
        self.colour_preview = QLabel()
        self.colour_preview.setFixedSize(50, 25)
        self.colour_preview.setFrameStyle(QFrame.Shape.StyledPanel)
        self._update_colour_preview()
        
        colour_btn = QPushButton("Choose...")
        colour_btn.clicked.connect(self.on_pick_colour)
        furn_layout.addRow("Color:", self._hbox(self.colour_preview, colour_btn))
        
        add_btn = QPushButton("Add to Room")
        add_btn.setStyleSheet("QPushButton { font-weight: bold; padding: 8px; background-color: #4a90e2; color: white; }")
        add_btn.clicked.connect(self.on_add_furniture)
        furn_layout.addRow(add_btn)
        
        # Assembly
        layout.addWidget(room_box)
        layout.addWidget(floor_group)
        layout.addWidget(features_group)
        layout.addWidget(furn_box)
        layout.addStretch(1)
    
    def _hbox(self, *widgets):
        box = QHBoxLayout()
        for w in widgets:
            box.addWidget(w)
        box.addStretch(1)
        container = QWidget()
        container.setLayout(box)
        return container
    
    def _update_room_unit_display(self):
        """Update room dimension display when unit changes."""
        w_unit = self.room_w_unit.currentText()
        d_unit = self.room_d_unit.currentText()
        
        # Convert displayed values if needed
        if hasattr(self, 'current_room_unit'):
            old_unit = self.current_room_unit
            if old_unit != w_unit:
                current_val = self.room_w_spin.value()
                # Convert from old unit to metres, then to new unit
                val_m = to_m(current_val, old_unit)
                new_val = from_m(val_m, w_unit)
                self.room_w_spin.setValue(new_val)
        
        self.current_room_unit = w_unit
    
    def _update_furniture_unit_display(self):
        """Update furniture dimension display when unit changes."""
        w_unit = self.f_w_unit.currentText()
        d_unit = self.f_d_unit.currentText()
        
        # Convert displayed values if needed
        if hasattr(self, 'current_furniture_unit'):
            old_unit = self.current_furniture_unit
            if old_unit != w_unit:
                current_val = self.f_w_spin.value()
                val_m = to_m(current_val, old_unit)
                new_val = from_m(val_m, w_unit)
                self.f_w_spin.setValue(new_val)
        
        self.current_furniture_unit = w_unit
    
    # ──────────────────────────────────────────────────────────
    # Theme system
    # ──────────────────────────────────────────────────────────
    def _apply_theme(self, theme):
        self.current_theme = theme
        
        # Main window styling
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {theme['window_bg']};
                color: {theme['text_color']};
            }}
            QGroupBox {{
                background-color: {theme['panel_bg']};
                border: 2px solid {theme['input_border']};
                border-radius: 8px;
                font-weight: bold;
                padding-top: 15px;
                margin-top: 10px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 8px 0 8px;
                color: {theme['text_color']};
            }}
            QPushButton {{
                background-color: {theme['button_bg']};
                border: 1px solid {theme['input_border']};
                border-radius: 4px;
                padding: 6px 12px;
                color: {theme['text_color']};
            }}
            QPushButton:hover {{
                background-color: {theme['button_hover']};
            }}
            QLineEdit, QDoubleSpinBox, QComboBox {{
                background-color: {theme['input_bg']};
                border: 1px solid {theme['input_border']};
                border-radius: 4px;
                padding: 4px;
                color: {theme['text_color']};
            }}
            QListWidget {{
                background-color: {theme['panel_bg']};
                border: 1px solid {theme['input_border']};
                border-radius: 4px;
                color: {theme['text_color']};
            }}
            QCheckBox {{
                color: {theme['text_color']};
            }}
        """)
        
        # Canvas background
        floor_color = FloorTexture.TEXTURES[self.current_floor_texture]['color']
        self.canvas.setBackgroundBrush(QBrush(QColor(floor_color)))
        
        # Update room border if it exists
        if self._room_rect_item and self.show_room_border:
            pen = self._room_rect_item.pen()
            pen.setColor(QColor(theme['room_border']))
            pen.setWidth(2)
            self._room_rect_item.setPen(pen)
    
    # ──────────────────────────────────────────────────────────
    # Event handlers
    # ──────────────────────────────────────────────────────────
    def keyPressEvent(self, event: QKeyEvent):
        """Handle keyboard shortcuts."""
        if event.key() == Qt.Key.Key_Delete:
            self.delete_selected_furniture()
        elif event.key() == Qt.Key.Key_R:
            self.rotate_selected_furniture()
        elif event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            if event.key() == Qt.Key.Key_C:
                self.copy_selected_furniture()
            elif event.key() == Qt.Key.Key_V:
                self.paste_furniture_center()
            elif event.key() == Qt.Key.Key_D:
                self.duplicate_selected_furniture()
            elif event.key() == Qt.Key.Key_S:
                self.save_layout()
            elif event.key() == Qt.Key.Key_O:
                self.load_layout()
            else:
                super().keyPressEvent(event)
        else:
            super().keyPressEvent(event)
    
    def rotate_selected_furniture(self):
        """Rotate currently selected furniture items."""
        selected_items = self.scene.selectedItems()
        for item in selected_items:
            if isinstance(item, FurnitureItem):
                item.rotate_90()
    
    def delete_selected_furniture(self):
        """Delete currently selected furniture items."""
        selected_items = self.scene.selectedItems()
        for item in selected_items:
            if isinstance(item, FurnitureItem):
                self.remove_furniture_item(item)
    
    def remove_furniture_item(self, furniture_item: FurnitureItem):
        """Remove a furniture item from scene and list."""
        # Remove from scene
        self.scene.removeItem(furniture_item)
        
        # Remove control button widgets if they exist
        for item in self.scene.items():
            if hasattr(item, 'widget'):
                widget = item.widget()
                if widget == furniture_item.delete_button or widget == furniture_item.rotate_button:
                    self.scene.removeItem(item)
        
        # Remove from list widget
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.data(Qt.ItemDataRole.UserRole) == furniture_item.furn:
                self.list_widget.takeItem(i)
                break
        
        # Remove from tracking list
        if furniture_item in self.furniture_items:
            self.furniture_items.remove(furniture_item)
    
    def on_room_apply(self):
        self.room_width_m = to_m(self.room_w_spin.value(), self.room_w_unit.currentText())
        self.room_depth_m = to_m(self.room_d_spin.value(), self.room_d_unit.currentText())
        self.draw_room_border()
    
    def on_pick_colour(self):
        colour = QColorDialog.getColor(self.f_colour, self, "Choose furniture color")
        if colour.isValid():
            self.f_colour = colour
            self._update_colour_preview()
    
    def _update_colour_preview(self):
        self.colour_preview.setStyleSheet(f"background-color: {self.f_colour.name()}; border: 1px solid #ccc;")
    
    def on_add_furniture(self):
        name = self.f_name.text() or f"Item {self.list_widget.count() + 1}"
        width_m = to_m(self.f_w_spin.value(), self.f_w_unit.currentText())
        depth_m = to_m(self.f_d_spin.value(), self.f_d_unit.currentText())
        
        furn = Furniture(name, width_m, depth_m, self.f_colour)
        item_rect = FurnitureItem(furn, self.pixels_per_m, self)
        self.scene.addItem(item_rect)
        self.furniture_items.append(item_rect)
        
        # Add to list (show in current display units)
        w_unit = self.f_w_unit.currentText()
        d_unit = self.f_d_unit.currentText()
        rotation_text = f" ({furn.rotation}°)" if furn.rotation != 0 else ""
        list_text = f"{name} – {format_dimension(width_m, w_unit)} × {format_dimension(depth_m, d_unit)}{rotation_text}"
        lw_item = QListWidgetItem(list_text)
        lw_item.setData(Qt.ItemDataRole.UserRole, furn)
        self.list_widget.addItem(lw_item)
        
        # Clear form
        self.f_name.clear()
    
    def copy_furniture(self, furniture: Furniture):
        """Copy furniture to clipboard."""
        self.clipboard_furniture = {
            'name': furniture.name,
            'width_m': furniture.width_m,
            'depth_m': furniture.depth_m,
            'colour': furniture.colour.name(),
            'rotation': furniture.rotation
        }
    
    def copy_selected_furniture(self):
        """Copy currently selected furniture."""
        selected_items = self.scene.selectedItems()
        for item in selected_items:
            if isinstance(item, FurnitureItem):
                self.copy_furniture(item.furn)
                break  # Copy only the first selected item
    
    def paste_furniture(self, pos=None):
        """Paste furniture from clipboard at specified position."""
        if not self.clipboard_furniture:
            return
        
        # Create new furniture from clipboard
        furn = Furniture(
            name=f"{self.clipboard_furniture['name']} (Copy)",
            width_m=self.clipboard_furniture['width_m'],
            depth_m=self.clipboard_furniture['depth_m'],
            colour=QColor(self.clipboard_furniture['colour']),
            rotation=self.clipboard_furniture['rotation']
        )
        
        # Create furniture item
        item_rect = FurnitureItem(furn, self.pixels_per_m, self)
        
        # Set position
        if pos:
            # Convert view position to scene position
            scene_pos = self.canvas.mapToScene(pos)
            item_rect.setPos(scene_pos)
            furn.x_m = scene_pos.x() / self.pixels_per_m
            furn.y_m = scene_pos.y() / self.pixels_per_m
        else:
            # Place at center
            center_x = self.room_width_m * self.pixels_per_m / 2
            center_y = self.room_depth_m * self.pixels_per_m / 2
            item_rect.setPos(center_x, center_y)
            furn.x_m = center_x / self.pixels_per_m
            furn.y_m = center_y / self.pixels_per_m
        
        self.scene.addItem(item_rect)
        self.furniture_items.append(item_rect)
        
        # Add to list
        w_unit = self.f_w_unit.currentText()
        d_unit = self.f_d_unit.currentText()
        rotation_text = f" ({furn.rotation}°)" if furn.rotation != 0 else ""
        list_text = f"{furn.name} – {format_dimension(furn.width_m, w_unit)} × {format_dimension(furn.depth_m, d_unit)}{rotation_text}"
        lw_item = QListWidgetItem(list_text)
        lw_item.setData(Qt.ItemDataRole.UserRole, furn)
        self.list_widget.addItem(lw_item)
    
    def paste_furniture_center(self):
        """Paste furniture at center of room."""
        self.paste_furniture()
    
    def duplicate_selected_furniture(self):
        """Duplicate selected furniture."""
        selected_items = self.scene.selectedItems()
        for item in selected_items:
            if isinstance(item, FurnitureItem):
                self.copy_furniture(item.furn)
                self.paste_furniture()
                break
    
    def save_layout(self):
        """Save current room layout to file."""
        filename, _ = QFileDialog.getSaveFileName(
            self, "Save Room Layout", "", "JSON Files (*.json);;All Files (*)"
        )
        if not filename:
            return
        
        # Prepare data
        layout_data = {
            'room': {
                'name': self.room_name,
                'width_m': self.room_width_m,
                'depth_m': self.room_depth_m,
                'floor_texture': self.current_floor_texture,
                'show_border': self.show_room_border
            },
            'furniture': []
        }
        
        # Add furniture data
        for item in self.furniture_items:
            furn = item.furn
            layout_data['furniture'].append({
                'name': furn.name,
                'width_m': furn.width_m,
                'depth_m': furn.depth_m,
                'colour': furn.colour.name(),
                'x_m': furn.x_m,
                'y_m': furn.y_m,
                'rotation': furn.rotation
            })
        
        # Save to file
        try:
            with open(filename, 'w') as f:
                json.dump(layout_data, f, indent=2)
            QMessageBox.information(self, "Success", f"Layout saved to {filename}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save layout:\n{str(e)}")
    
    def load_layout(self):
        """Load room layout from file."""
        filename, _ = QFileDialog.getOpenFileName(
            self, "Load Room Layout", "", "JSON Files (*.json);;All Files (*)"
        )
        if not filename:
            return
        
        try:
            with open(filename, 'r') as f:
                layout_data = json.load(f)
            
            # Clear current layout
            self.new_room()
            
            # Load room data
            room_data = layout_data.get('room', {})
            self.room_name = room_data.get('name', 'My Room')
            self.room_width_m = room_data.get('width_m', 5.0)
            self.room_depth_m = room_data.get('depth_m', 4.0)
            self.current_floor_texture = room_data.get('floor_texture', 'None')
            self.show_room_border = room_data.get('show_border', True)
            
            # Update UI
            self.room_name_input.setText(self.room_name)
            self.room_w_spin.setValue(from_m(self.room_width_m, self.room_w_unit.currentText()))
            self.room_d_spin.setValue(from_m(self.room_depth_m, self.room_d_unit.currentText()))
            self.floor_combo.setCurrentText(self.current_floor_texture)
            self.border_checkbox.setChecked(self.show_room_border)
            
            # Redraw room
            self.draw_room_border()
            self._apply_theme(self.current_theme)  # Update floor texture
            
            # Load furniture
            for furn_data in layout_data.get('furniture', []):
                furn = Furniture(
                    name=furn_data['name'],
                    width_m=furn_data['width_m'],
                    depth_m=furn_data['depth_m'],
                    colour=QColor(furn_data['colour']),
                    x_m=furn_data['x_m'],
                    y_m=furn_data['y_m'],
                    rotation=furn_data.get('rotation', 0.0)
                )
                
                # Create furniture item
                item_rect = FurnitureItem(furn, self.pixels_per_m, self)
                item_rect.setPos(furn.x_m * self.pixels_per_m, furn.y_m * self.pixels_per_m)
                self.scene.addItem(item_rect)
                self.furniture_items.append(item_rect)
                
                # Add to list
                w_unit = self.f_w_unit.currentText()
                d_unit = self.f_d_unit.currentText()
                rotation_text = f" ({furn.rotation}°)" if furn.rotation != 0 else ""
                list_text = f"{furn.name} – {format_dimension(furn.width_m, w_unit)} × {format_dimension(furn.depth_m, d_unit)}{rotation_text}"
                lw_item = QListWidgetItem(list_text)
                lw_item.setData(Qt.ItemDataRole.UserRole, furn)
                self.list_widget.addItem(lw_item)
            
            QMessageBox.information(self, "Success", f"Layout loaded from {filename}")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load layout:\n{str(e)}")
    
    def update_furniture_list_item(self, furniture: Furniture):
        """Update the list display for a furniture item (e.g., after rotation)."""
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.data(Qt.ItemDataRole.UserRole) == furniture:
                # Recreate the list text with current rotation
                w_unit = self.f_w_unit.currentText()
                d_unit = self.f_d_unit.currentText()
                rotation_text = f" ({furniture.rotation}°)" if furniture.rotation != 0 else ""
                list_text = f"{furniture.name} – {format_dimension(furniture.width_m, w_unit)} × {format_dimension(furniture.depth_m, d_unit)}{rotation_text}"
                item.setText(list_text)
                break
    
    def _add_door_to_list(self, door_window: DoorWindow):
        """Add a door/window to the furniture list."""
        w_unit = self.f_w_unit.currentText()
        d_unit = self.f_d_unit.currentText()
        display_text = f"{door_window.name} – {format_dimension(door_window.width_m, w_unit)} × {format_dimension(door_window.thickness_m, d_unit)}"
        
        list_item = QListWidgetItem(display_text)
        list_item.setData(Qt.ItemDataRole.UserRole, door_window)
        
        # Set different colors for doors vs windows
        if door_window.is_door:
            list_item.setBackground(QColor(255, 255, 255, 50))  # Light white for doors
        else:
            list_item.setBackground(QColor(173, 216, 230, 50))  # Light blue for windows
        
        self.list_widget.addItem(list_item)
    
    def _remove_door_from_list(self, door_name: str):
        """Remove a door/window from the furniture list."""
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            door_window = item.data(Qt.ItemDataRole.UserRole)
            if isinstance(door_window, DoorWindow) and door_window.name == door_name:
                self.list_widget.takeItem(i)
                break
    
    def _name_exists(self, name: str) -> bool:
        """Check if a name already exists in the furniture list."""
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            data = item.data(Qt.ItemDataRole.UserRole)
            if isinstance(data, Furniture) and data.name == name:
                return True
            elif isinstance(data, DoorWindow) and data.name == name:
                return True
        return False
    
    def on_floor_changed(self, texture_name):
        """Change floor texture."""
        self.current_floor_texture = texture_name
        floor_color = FloorTexture.TEXTURES[texture_name]['color']
        self.canvas.setBackgroundBrush(QBrush(QColor(floor_color)))
    
    def add_door(self):
        """Add a door to the room."""
        if not self._room_rect_item:
            QMessageBox.warning(self, "No Room", "Please create a room first!")
            return
        
        # Show door configuration dialog
        dialog = DoorWindowDialog(is_door=True, parent=self)
        # Find next available door name
        while self._name_exists(f"Door {self.door_counter}"):
            self.door_counter += 1
        dialog.name_input.setText(f"Door {self.door_counter}")
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            door_data = dialog.get_door_window_data()
            
            # Create interactive door
            door_item = DoorItem(door_data, self.pixels_per_m, self)
            
            # Place door on the bottom wall (y = room_depth)
            door_x = (self.room_width_m - door_data.width_m) / 2  # Center horizontally
            door_y = self.room_depth_m - door_data.thickness_m
            
            door_item.setPos(door_x * self.pixels_per_m, door_y * self.pixels_per_m)
            
            self.scene.addItem(door_item)
            self.door_items.append(door_item)
            
            # Add to furniture list
            self._add_door_to_list(door_data)
            
            # Increment counter for next door
            self.door_counter += 1
    
    def add_window(self):
        """Add a window to the room."""
        if not self._room_rect_item:
            QMessageBox.warning(self, "No Room", "Please create a room first!")
            return
        
        # Show window configuration dialog
        dialog = DoorWindowDialog(is_door=False, parent=self)
        # Find next available window name
        while self._name_exists(f"Window {self.window_counter}"):
            self.window_counter += 1
        dialog.name_input.setText(f"Window {self.window_counter}")
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            window_data = dialog.get_door_window_data()
            
            # Create window item
            window_item = DoorItem(window_data, self.pixels_per_m, self)
            
            # Style as window (light blue)
            window_item.setBrush(QBrush(QColor(173, 216, 230)))  # Light blue window
            window_item.setPen(QPen(QColor(100, 149, 237), 2))  # Cornflower blue border
            
            # Place window on the top wall (y = 0)
            window_x = (self.room_width_m - window_data.width_m) / 2  # Center horizontally
            window_y = 0
            
            window_item.setPos(window_x * self.pixels_per_m, window_y * self.pixels_per_m)
            
            self.scene.addItem(window_item)
            self.door_items.append(window_item)
            
            # Add to furniture list
            self._add_door_to_list(window_data)
            
            # Increment counter for next window
            self.window_counter += 1
    
    def on_room_name_changed(self, text):
        """Update room name when text changes."""
        self.room_name = text
    
    def toggle_snap_to_borders(self):
        """Toggle furniture snapping to room borders."""
        self.snap_to_borders = self.snap_checkbox.isChecked()
    
    def show_homely_help(self):
        """Show Homely Help dialog (placeholder)."""
        QMessageBox.information(
            self,
            "Homely Help",
            "Welcome to Homely Helper!\n\n"
            "This feature is coming soon. For now, explore the application:\n\n"
            "• Create rooms with custom dimensions\n"
            "• Add furniture and arrange it\n"
            "• Use keyboard shortcuts (R to rotate, Delete to remove)\n"
            "• Right-click items for context menu\n"
            "• Save and load your layouts\n"
            "• Try different themes in Settings!"
        )
    
    def toggle_room_border(self):
        """Toggle room border visibility."""
        self.show_room_border = not self.show_room_border
        self.border_checkbox.setChecked(self.show_room_border)
        
        if self._room_rect_item:
            if self.show_room_border:
                pen = self._room_rect_item.pen()
                pen.setColor(QColor(self.current_theme['room_border']))
                pen.setWidth(2)
                self._room_rect_item.setPen(pen)
            else:
                pen = self._room_rect_item.pen()
                pen.setColor(QColor(0, 0, 0, 0))  # Transparent
                self._room_rect_item.setPen(pen)
    
    def draw_room_border(self):
        px_w = self.room_width_m * self.pixels_per_m
        px_d = self.room_depth_m * self.pixels_per_m
        self.scene.setSceneRect(0, 0, px_w, px_d)
        
        if self._room_rect_item is None:
            self._room_rect_item = self.scene.addRect(QRectF(0, 0, px_w, px_d))
        else:
            self._room_rect_item.setRect(QRectF(0, 0, px_w, px_d))
        
        # Style the room border
        if self.show_room_border:
            pen = self._room_rect_item.pen()
            pen.setColor(QColor(self.current_theme['room_border']))
            pen.setWidth(2)
            self._room_rect_item.setPen(pen)
        else:
            pen = self._room_rect_item.pen()
            pen.setColor(QColor(0, 0, 0, 0))  # Transparent
            self._room_rect_item.setPen(pen)
            
        self._room_rect_item.setBrush(QBrush())  # No fill
    
    # ──────────────────────────────────────────────────────────
    # Menu actions
    # ──────────────────────────────────────────────────────────
    def new_room(self):
        self.scene.clear()
        self.list_widget.clear()
        self.furniture_items.clear()
        self.door_items.clear()
        self._room_rect_item = None
        # Reset counters
        self.door_counter = 1
        self.window_counter = 1
        self.draw_room_border()
    
    def show_settings(self):
        dialog = SettingsDialog(self)
        dialog.theme_combo.setCurrentText(self.current_theme['name'])
        dialog.font_slider.setValue(self.font_size)
        dialog.scale_slider.setValue(self.pixels_per_m)
        
        # Store original settings in case user cancels
        original_theme = self.current_theme
        original_font = self.font_size
        original_scale = self.pixels_per_m
        
        result = dialog.exec()
        
        # If user cancelled, restore original settings
        if result == QDialog.DialogCode.Rejected:
            self._apply_theme(original_theme)
            self._set_font_size(original_font)
            self._set_canvas_scale(original_scale)
    
    def _set_font_size(self, size):
        self.font_size = size
        font = QFont()
        font.setPointSize(size)
        QApplication.instance().setFont(font)
    
    def _set_canvas_scale(self, scale):
        """Update canvas scale and redraw everything."""
        old_scale = self.pixels_per_m
        self.pixels_per_m = scale
        
        # Redraw room
        self.draw_room_border()
        
        # Update all furniture items
        for item in self.furniture_items:
            # Update size
            new_width = item.furn.width_m * scale
            new_height = item.furn.depth_m * scale
            item.setRect(0, 0, new_width, new_height)
            
            # Update position
            item.setPos(item.furn.x_m * scale, item.furn.y_m * scale)
            item.scale = scale
            
            # Maintain rotation
            item.setRotation(item.furn.rotation)
            
            # Reposition control buttons
            item._position_control_buttons()
    
    def show_about(self):
        QMessageBox.about(self, "About Homely Helper", 
                         "Homely Helper v0.4\n\n"
                         "A modern furniture layout planner\n"
                         "with advanced interaction features.\n\n"
                         "New in v0.4:\n"
                         "• Mouse wheel zoom (Ctrl+Wheel)\n"
                         "• Floating zoom buttons\n"
                         "• Unit-aware displays\n"
                         "• Room border toggle\n"
                         "• Delete functionality (X + Del key)\n"
                         "• Floor textures\n"
                         "• Enhanced settings")
    
    def _load_settings(self):
        theme_name = self.settings.value("theme", "Light")
        themes = {"Light": Theme.LIGHT, "Dark": Theme.DARK, "Mixed": Theme.MIXED}
        if theme_name in themes:
            self._apply_theme(themes[theme_name])
        
        font_size = int(self.settings.value("font_size", 11))
        self._set_font_size(font_size)
        
        scale = int(self.settings.value("canvas_scale", 60))
        self._set_canvas_scale(scale)
        
        border = self.settings.value("show_border", True, type=bool)
        self.show_room_border = border
        self.border_checkbox.setChecked(border)
        
        floor_texture = self.settings.value("floor_texture", "None")
        if floor_texture in FloorTexture.TEXTURES:
            self.current_floor_texture = floor_texture
            self.floor_combo.setCurrentText(floor_texture)
        
        # Load cached room if it exists
        self._load_cached_room()
    
    def _save_settings(self):
        self.settings.setValue("theme", self.current_theme['name'])
        self.settings.setValue("font_size", self.font_size)
        self.settings.setValue("canvas_scale", self.pixels_per_m)
        self.settings.setValue("show_border", self.show_room_border)
        self.settings.setValue("floor_texture", self.current_floor_texture)
        
        # Cache current room layout
        self._cache_current_room()
    
    def _cache_current_room(self):
        """Cache the current room layout."""
        try:
            layout_data = {
                'room': {
                    'name': self.room_name,
                    'width_m': self.room_width_m,
                    'depth_m': self.room_depth_m,
                    'floor_texture': self.current_floor_texture,
                    'show_border': self.show_room_border
                },
                'furniture': []
            }
            
            # Add furniture data
            for item in self.furniture_items:
                furn = item.furn
                layout_data['furniture'].append({
                    'name': furn.name,
                    'width_m': furn.width_m,
                    'depth_m': furn.depth_m,
                    'colour': furn.colour.name(),
                    'x_m': furn.x_m,
                    'y_m': furn.y_m,
                    'rotation': furn.rotation
                })
            
            # Save to settings
            self.settings.setValue("cached_room", json.dumps(layout_data))
        except Exception:
            pass  # Silently fail if caching doesn't work
    
    def _load_cached_room(self):
        """Load cached room layout if it exists."""
        try:
            cached_data = self.settings.value("cached_room")
            if not cached_data:
                return
                
            layout_data = json.loads(cached_data)
            
            # Load room data
            room_data = layout_data.get('room', {})
            self.room_name = room_data.get('name', self.room_name)
            self.room_width_m = room_data.get('width_m', self.room_width_m)
            self.room_depth_m = room_data.get('depth_m', self.room_depth_m)
            self.current_floor_texture = room_data.get('floor_texture', 'None')
            self.show_room_border = room_data.get('show_border', True)
            
            # Update UI
            self.room_name_input.setText(self.room_name)
            self.room_w_spin.setValue(from_m(self.room_width_m, self.room_w_unit.currentText()))
            self.room_d_spin.setValue(from_m(self.room_depth_m, self.room_d_unit.currentText()))
            self.floor_combo.setCurrentText(self.current_floor_texture)
            self.border_checkbox.setChecked(self.show_room_border)
            
            # Redraw room
            self.draw_room_border()
            
            # Load furniture
            for furn_data in layout_data.get('furniture', []):
                furn = Furniture(
                    name=furn_data['name'],
                    width_m=furn_data['width_m'],
                    depth_m=furn_data['depth_m'],
                    colour=QColor(furn_data['colour']),
                    x_m=furn_data['x_m'],
                    y_m=furn_data['y_m'],
                    rotation=furn_data.get('rotation', 0.0)
                )
                
                # Create furniture item
                item_rect = FurnitureItem(furn, self.pixels_per_m, self)
                item_rect.setPos(furn.x_m * self.pixels_per_m, furn.y_m * self.pixels_per_m)
                self.scene.addItem(item_rect)
                self.furniture_items.append(item_rect)
                
                # Add to list
                w_unit = self.f_w_unit.currentText()
                d_unit = self.f_d_unit.currentText()
                rotation_text = f" ({furn.rotation}°)" if furn.rotation != 0 else ""
                list_text = f"{furn.name} – {format_dimension(furn.width_m, w_unit)} × {format_dimension(furn.depth_m, d_unit)}{rotation_text}"
                lw_item = QListWidgetItem(list_text)
                lw_item.setData(Qt.ItemDataRole.UserRole, furn)
                self.list_widget.addItem(lw_item)
                
        except Exception:
            pass  # Silently fail if loading doesn't work
    
    def closeEvent(self, event):
        self._save_settings()
        event.accept()

# ────────────────────────────────────────────────────────────────────
# Application entry point
# ────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("Homely Helper")
    app.setOrganizationName("HomelyHelper")
    
    window = RoomPlanner()
    window.show()
    sys.exit(app.exec()) 