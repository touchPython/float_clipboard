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
        self.btn_auto_paste.clicked.connect(self.copy_all_to_excel)
        paste_layout.addWidget(self.btn_auto_paste)
        
        self.main_layout.addLayout(paste_layout)
        

        


        # 剪贴板
        self.clipboard = QApplication.clipboard()
        self.current_images = []  # 存储图片控件的列表
        self.original_pixmaps = []  # 存储原始图片的列表

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
        self.original_pixmaps.clear()


    def copy_all_to_excel(self):
        """将当前列表中的所有图片路径打包成 HTML，以便 Excel 一键粘贴所有图"""
        if not self.current_images:
            QToolTip.showText(QCursor.pos(), "列表是空的")
            return

        html_content = "<html><body>"

        # 压缩比例 (0.8 表示压缩到原始大小的 80%)
        compression_ratio = 0.8

        # 遍历原始图片列表
        for i, pixmap in enumerate(self.original_pixmaps):
            if not pixmap.isNull():
                # 获取原始图片尺寸
                original_width = pixmap.width()
                original_height = pixmap.height()

                # 计算压缩后的尺寸
                compressed_width = int(original_width * compression_ratio)
                compressed_height = int(original_height * compression_ratio)

                # 对图片进行压缩
                compressed_pixmap = pixmap.scaled(
                    compressed_width, compressed_height, 
                    Qt.AspectRatioMode.KeepAspectRatio, 
                    Qt.TransformationMode.SmoothTransformation
                )

                # 将压缩后的 QPixmap 转换为 Base64 编码的字符串
                byte_array = QByteArray()
                buffer = QBuffer(byte_array)
                buffer.open(QIODevice.OpenModeFlag.WriteOnly)
                compressed_pixmap.save(buffer, "PNG")
                base64_data = byte_array.toBase64().data().decode()

                # 包装成 HTML 图片标签，指定压缩后的尺寸，使用 <div> 标签确保图片独立显示
                html_content += f'<div style="display: block; margin-bottom: 10px;"><img src="data:image/png;base64,{base64_data}" width="{compressed_width}" height="{compressed_height}"></div>'

        html_content += "</body></html>"

        # 创建 MimeData 并设置 HTML 格式
        mime_data = QMimeData()
        mime_data.setHtml(html_content)

        # 放入剪贴板
        self.clipboard.setMimeData(mime_data)
        QToolTip.showText(QCursor.pos(), "🚀 已打包！请直接在 Excel 按 Command+V")

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
        self.original_pixmaps.append(pixmap)



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
    



if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = FloatClipboardWindow()
    window.show()
    sys.exit(app.exec())