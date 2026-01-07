"""
Simple Image Orientation Labeler (Mac & Windows)
With PREFETCHING - loads images in background for speed!

Threading concept:
- Main thread: Shows UI, handles user input
- Background thread: Preloads upcoming images into memory
- Result: Instant image switching!
"""

import sys
import os
import json
from pathlib import Path
from threading import Thread
from queue import Queue

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFileDialog
)
from PyQt6.QtGui import QPixmap, QKeyEvent
from PyQt6.QtCore import Qt, QThread, pyqtSignal


# How many images to keep loaded ahead
PREFETCH_COUNT = 20


class ImageLoader(QThread):
    """
    Background thread that preloads images.
    
    Threading 101:
    - Runs separately from the main UI thread
    - Loads images into a cache dictionary
    - UI thread reads from cache = instant display!
    """
    image_ready = pyqtSignal(int, object)  # Signal: (index, pixmap)
    
    def __init__(self, images, folder, start_index=0):
        super().__init__()
        self.images = images
        self.folder = folder
        self.start_index = start_index
        self.running = True
        
    def run(self):
        """Load PREFETCH_COUNT images starting from start_index"""
        for i in range(self.start_index, min(self.start_index + PREFETCH_COUNT, len(self.images))):
            if not self.running:
                break
            img_name = self.images[i]
            img_path = os.path.join(self.folder, img_name)
            pixmap = QPixmap(img_path)
            if not pixmap.isNull():
                scaled = pixmap.scaled(
                    780, 430,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                self.image_ready.emit(i, scaled)
                
    def stop(self):
        self.running = False


class OrientationLabeler(QMainWindow):
    def __init__(self):
        super().__init__()
        self.images = []
        self.current_index = 0
        self.results = {}
        self.image_folder = None
        
        # Image cache - stores preloaded QPixmaps
        # Key: image index, Value: scaled QPixmap
        self.cache = {}
        
        # Track which batch we've loaded
        self.loaded_up_to = 0
        
        # Background loader thread
        self.loader = None
        
        self.setup_ui()
        
    def setup_ui(self):
        self.setWindowTitle("Image Orientation Labeler")
        self.setGeometry(100, 100, 900, 700)
        self.setStyleSheet("background-color: #1a1a2e;")
        
        main = QWidget()
        self.setCentralWidget(main)
        layout = QVBoxLayout(main)
        layout.setSpacing(15)
        
        # Title
        title = QLabel("Image Orientation Labeler")
        title.setStyleSheet("color: #e94560; font-size: 28px; font-weight: bold;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Load button
        self.load_btn = QPushButton("Load Image Folder")
        self.load_btn.setStyleSheet("""
            QPushButton {
                background-color: #0f3460;
                color: white;
                font-size: 16px;
                padding: 12px 30px;
                border-radius: 8px;
            }
            QPushButton:hover { background-color: #1a4a7a; }
        """)
        self.load_btn.clicked.connect(self.load_folder)
        layout.addWidget(self.load_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # Image display
        self.image_label = QLabel()
        self.image_label.setMinimumSize(800, 450)
        self.image_label.setStyleSheet("background-color: #16213e; border-radius: 10px;")
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.image_label)
        
        # Image name
        self.name_label = QLabel("")
        self.name_label.setStyleSheet("color: #a1a1a1; font-size: 14px;")
        self.name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.name_label)
        
        # Progress + cache status
        self.progress_label = QLabel("")
        self.progress_label.setStyleSheet("color: #e94560; font-size: 14px;")
        self.progress_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.progress_label)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(30)
        
        self.portrait_btn = QPushButton("Portrait (P)")
        self.portrait_btn.setStyleSheet("""
            QPushButton {
                background-color: #e94560;
                color: white;
                font-size: 18px;
                font-weight: bold;
                padding: 15px 50px;
                border-radius: 8px;
            }
            QPushButton:hover { background-color: #ff6b8a; }
            QPushButton:disabled { background-color: #4a4a5a; }
        """)
        self.portrait_btn.clicked.connect(lambda: self.label_image("portrait"))
        self.portrait_btn.setEnabled(False)
        btn_layout.addWidget(self.portrait_btn)
        
        self.landscape_btn = QPushButton("Landscape (L)")
        self.landscape_btn.setStyleSheet("""
            QPushButton {
                background-color: #0f3460;
                color: white;
                font-size: 18px;
                font-weight: bold;
                padding: 15px 50px;
                border-radius: 8px;
            }
            QPushButton:hover { background-color: #1a4a7a; }
            QPushButton:disabled { background-color: #4a4a5a; }
        """)
        self.landscape_btn.clicked.connect(lambda: self.label_image("landscape"))
        self.landscape_btn.setEnabled(False)
        btn_layout.addWidget(self.landscape_btn)
        
        layout.addLayout(btn_layout)
        
        # Status
        self.status_label = QLabel("Press P for Portrait, L for Landscape")
        self.status_label.setStyleSheet("color: #666; font-size: 12px;")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)
        
    def keyPressEvent(self, event: QKeyEvent):
        key = event.text().lower()
        if key == 'p':
            self.label_image("portrait")
        elif key == 'l':
            self.label_image("landscape")
            
    def load_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Image Folder")
        if not folder:
            return
            
        self.image_folder = folder
        self.images = []
        self.cache = {}
        self.loaded_up_to = 0
        
        extensions = ('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.tif')
        for f in sorted(os.listdir(folder)):
            if f.lower().endswith(extensions):
                self.images.append(f)
        
        if not self.images:
            self.name_label.setText("No images found in folder")
            return
            
        self.current_index = 0
        self.results = {}
        self.portrait_btn.setEnabled(True)
        self.landscape_btn.setEnabled(True)
        
        # Start preloading first batch
        self.start_preload(0)
        self.show_current_image()
        
    def start_preload(self, from_index):
        """
        Start background thread to preload images.
        
        This is the key technique:
        1. We tell the loader to start at from_index
        2. It loads PREFETCH_COUNT images in background
        3. Each loaded image triggers image_ready signal
        4. on_image_loaded adds it to our cache
        """
        if self.loader and self.loader.isRunning():
            self.loader.stop()
            self.loader.wait()
            
        self.loader = ImageLoader(self.images, self.image_folder, from_index)
        self.loader.image_ready.connect(self.on_image_loaded)
        self.loader.start()
        self.loaded_up_to = from_index + PREFETCH_COUNT
        
    def on_image_loaded(self, index, pixmap):
        """Called by background thread when an image is ready"""
        self.cache[index] = pixmap
        
        # If this is the current image and we're waiting, show it
        if index == self.current_index and self.image_label.pixmap() is None:
            self.image_label.setPixmap(pixmap)
            
        self.update_progress()
        
    def show_current_image(self):
        if self.current_index >= len(self.images):
            self.finish()
            return
            
        img_name = self.images[self.current_index]
        self.name_label.setText(img_name)
        self.update_progress()
        
        # Check if image is in cache (preloaded)
        if self.current_index in self.cache:
            # Instant! Image was preloaded
            self.image_label.setPixmap(self.cache[self.current_index])
        else:
            # Not in cache yet - load directly (slower)
            self.image_label.clear()
            self.status_label.setText("Loading...")
            img_path = os.path.join(self.image_folder, img_name)
            pixmap = QPixmap(img_path)
            scaled = pixmap.scaled(780, 430, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.image_label.setPixmap(scaled)
            self.status_label.setText("Press P for Portrait, L for Landscape")
            
        # Check if we need to preload more
        # When we're halfway through current batch, start loading next batch
        if self.current_index >= self.loaded_up_to - (PREFETCH_COUNT // 2):
            self.start_preload(self.loaded_up_to)
            
        # Clean up old cached images (free memory)
        self.cleanup_cache()
        
    def cleanup_cache(self):
        """Remove images we've already passed to save memory"""
        old_keys = [k for k in self.cache.keys() if k < self.current_index - 5]
        for k in old_keys:
            del self.cache[k]
            
    def update_progress(self):
        cached = len([k for k in self.cache.keys() if k >= self.current_index])
        self.progress_label.setText(
            f"{self.current_index + 1} / {len(self.images)}  •  {cached} preloaded"
        )
        
    def label_image(self, orientation):
        if not self.images or self.current_index >= len(self.images):
            return
            
        img_name = self.images[self.current_index]
        self.results[img_name] = orientation
        
        self.current_index += 1
        self.show_current_image()
        
    def finish(self):
        if self.loader:
            self.loader.stop()
            
        self.image_label.clear()
        self.name_label.setText("All done!")
        self.progress_label.setText("")
        self.portrait_btn.setEnabled(False)
        self.landscape_btn.setEnabled(False)
        
        # Save to project data directory only
        project_data_dir = Path(__file__).parent.parent.parent / "data"
        project_data_dir.mkdir(exist_ok=True)
        output_path = project_data_dir / "orientations.json"
        with open(output_path, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        self.status_label.setText(f"Saved to: {output_path}")
        
    def closeEvent(self, event):
        """Clean up when window closes"""
        if self.loader:
            self.loader.stop()
            self.loader.wait()
        event.accept()


def main():
    app = QApplication(sys.argv)
    window = OrientationLabeler()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
