import sys
import subprocess
import platform
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *


class FloatClipboardWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # 窗口置顶 + 有标题栏
        self.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint
        )
        self.setMinimumSize(200, 500)
        self.setWindowTitle("剪贴板")

        # 主界面
        central = QWidget()
        self.setCentralWidget(central)
        self.main_layout = QVBoxLayout(central)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        self.main_layout.setSpacing(8)

        # 检测按钮和自动检测复选框
        check_layout = QHBoxLayout()
        self.btn_check = QPushButton("🔍 检查剪贴板")
        self.btn_check.clicked.connect(self.on_clip_change)
        check_layout.addWidget(self.btn_check)
        
        self.auto_check = QCheckBox("自动检测")
        self.auto_check.stateChanged.connect(self.toggle_auto_check)
        check_layout.addWidget(self.auto_check)
        
        self.main_layout.addLayout(check_layout)

        # 图片列表容器
        self.images_container = QWidget()
        self.images_layout = QVBoxLayout(self.images_container)
        self.images_layout.setSpacing(10)
        self.main_layout.addWidget(self.images_container)
        
        # 自动粘贴功能
        paste_layout = QHBoxLayout()
        self.btn_auto_paste = QPushButton("📋 自动粘贴")
        self.btn_auto_paste.clicked.connect(self.auto_paste)
        paste_layout.addWidget(self.btn_auto_paste)
        
        self.label_delay = QLabel("延迟(秒):")
        paste_layout.addWidget(self.label_delay)
        
        self.spin_delay = QSpinBox()
        self.spin_delay.setMinimum(1)
        self.spin_delay.setMaximum(10)
        self.spin_delay.setValue(1)
        paste_layout.addWidget(self.spin_delay)
        
        self.main_layout.addLayout(paste_layout)
        

        


        # 剪贴板
        self.clipboard = QApplication.clipboard()
        self.current_images = []  # 存储图片和按钮的列表

        # 拖动窗口用
        self.mouse_pos = None
        
        # 设置窗口位置到屏幕最左边
        screen = QApplication.primaryScreen()
        screen_geometry = screen.geometry()
        self.move(0, screen_geometry.top())

    # --------------- 窗口拖动 ---------------
    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self.mouse_pos = e.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, e):
        if self.mouse_pos and e.buttons() & Qt.MouseButton.LeftButton:
            self.move(e.globalPosition().toPoint() - self.mouse_pos)

    # --------------- 剪贴板变化 ---------------
    def on_clip_change(self):
        mime = self.clipboard.mimeData()
        
        # 清除现有图片
        self.clear_images()
        
        # 检查是否有图片
        if mime.hasImage():
            img = mime.imageData()
            if isinstance(img, QImage) and not img.isNull():
                pixmap = QPixmap.fromImage(img)
                self.add_image(pixmap)
                return
        
        # 检查是否有文件路径
        if mime.hasUrls():
            for url in mime.urls():
                path = url.toLocalFile()
                if path.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
                    pixmap = QPixmap(path)
                    if not pixmap.isNull():
                        self.add_image(pixmap)
            if self.current_images:
                return
        
        # 检查是否有文本路径
        if mime.hasText():
            text = mime.text().strip()
            lines = text.split('\n')
            for line in lines:
                line = line.strip()
                if line.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
                    pixmap = QPixmap(line)
                    if not pixmap.isNull():
                        self.add_image(pixmap)
            if self.current_images:
                return
        
    def clear_images(self):
        """清除所有图片和按钮"""
        for widget in self.current_images:
            widget.deleteLater()
        self.current_images.clear()
    
    def add_image(self, pixmap):
        """添加一张图片到列表"""
        # 创建水平布局
        image_layout = QHBoxLayout()
        image_layout.setSpacing(10)
        
        # 图片标签
        image_label = QLabel()
        scaled = pixmap.scaled(
            100, 100, Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        image_label.setPixmap(scaled)
        image_label.setStyleSheet("""
            QLabel {
                background-color: #1d1d1d;
                border-radius: 4px;
                padding: 5px;
            }
        """)
        image_layout.addWidget(image_label)
        
        # 重新复制按钮
        copy_button = QPushButton("🔁 重新复制")
        copy_button.clicked.connect(lambda _, p=pixmap: self.copy_to_clipboard(p))
        image_layout.addWidget(copy_button)
        
        # 创建容器并添加到主布局
        image_widget = QWidget()
        image_widget.setLayout(image_layout)
        self.images_layout.addWidget(image_widget)
        self.current_images.append(image_widget)



    # --------------- 核心功能 ---------------
    def copy_to_clipboard(self, pixmap):
        """把指定图片复制回剪贴板"""
        if pixmap:
            self.clipboard.setPixmap(pixmap)
            QToolTip.showText(QCursor.pos(), "已复制")
    
    def toggle_auto_check(self, state):
        """切换自动检测功能"""
        if state == Qt.CheckState.Checked.value:
            # 连接剪贴板信号
            self.clipboard.dataChanged.connect(self.on_clip_change)
        else:
            # 断开剪贴板信号
            self.clipboard.dataChanged.disconnect(self.on_clip_change)
    

    
    def auto_paste(self):
        print("自动粘贴所有图片")
        """自动粘贴所有图片"""
        import platform
        import ctypes
        
        delay = self.spin_delay.value() * 1000  # 转换为毫秒
        
        # 确保有图片要粘贴
        if not self.current_images:
            QToolTip.showText(QCursor.pos(), "没有图片可粘贴")
            return
        
        # 依次处理每张图片
        def paste_next(index=0):
            if index >= len(self.current_images):
                QToolTip.showText(QCursor.pos(), "粘贴完成")
                return
            
            # 获取当前图片
            widget = self.current_images[index]
            image_layout = widget.layout()
            image_label = image_layout.itemAt(0).widget()
            pixmap = image_label.pixmap()
            
            if pixmap:
                # 压缩图片
                compressed_pixmap = self.compress_image(pixmap)
                
                # 复制到剪贴板
                self.clipboard.setPixmap(compressed_pixmap)
                QToolTip.showText(QCursor.pos(), f"正在粘贴第 {index+1} 张图片...")
                
                # 等待一小段时间确保剪贴板操作完成
                QThread.msleep(200)
                
                # 根据操作系统类型模拟粘贴快捷键
                if platform.system() == "Windows":
                    # Windows: Ctrl+V
                    ctypes.windll.user32.keybd_event(0x11, 0, 0, 0)  # Ctrl 按下
                    ctypes.windll.user32.keybd_event(0x56, 0, 0, 0)  # V 按下
                    ctypes.windll.user32.keybd_event(0x56, 0, 2, 0)  # V 释放
                    ctypes.windll.user32.keybd_event(0x11, 0, 2, 0)  # Ctrl 释放
                elif platform.system() == "Darwin":
                    # macOS: Command+V
                    import subprocess
                    script = '''
                    tell application "System Events"
                        keystroke "v" using command down
                    end tell
                    '''
                    subprocess.Popen(['osascript', '-e', script])
            
            # 递归处理下一张图片
            QTimer.singleShot(delay, lambda: paste_next(index + 1))
        
        # 开始粘贴过程，第一张图片也需要延迟
        QTimer.singleShot(delay, paste_next)
    
    def compress_image(self, pixmap):
        """压缩图片
        
        Args:
            pixmap: 原始 QPixmap 对象
            
        Returns:
            压缩后的 QPixmap 对象
        """
        # 将 QPixmap 转换为 QImage
        image = pixmap.toImage()
        
        # 获取原始尺寸
        width = image.width()
        height = image.height()
        
        # 如果图片太大，调整大小
        max_size = 1024
        if width > max_size or height > max_size:
            # 保持比例调整大小
            if width > height:
                new_width = max_size
                new_height = int(height * (max_size / width))
            else:
                new_height = max_size
                new_width = int(width * (max_size / height))
            
            image = image.scaled(new_width, new_height, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        
        # 转换回 QPixmap
        compressed_pixmap = QPixmap.fromImage(image)
        
        return compressed_pixmap


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = FloatClipboardWindow()
    window.show()
    sys.exit(app.exec())