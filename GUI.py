import json, sys
from datetime import datetime
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QListWidget, QPushButton, QDialog, QLineEdit, QLabel, QMessageBox, QFileDialog
)

# 保留原来的工具函数
def validate_datetime(date_text):
    try:
        datetime.strptime(date_text, "%Y-%m-%dT%H:%M:%S")
        return True
    except ValueError:
        return False

def convert_colon(text):
    return text.replace('：', ':')

def format_date(date_text):
    date_text = date_text.replace('/', '-')
    parts = date_text.split('-')
    if len(parts) == 3:
        return f"{parts[0]}-{parts[1].zfill(2)}-{parts[2].zfill(2)}"
    else:
        raise ValueError("日期格式错误")

# 对话框：添加/编辑考试信息
class ExamDialog(QDialog):
    def __init__(self, exam=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("考试信息" + ("编辑" if exam else "添加"))
        self.resize(350, 400)  # 扩大尺寸适合触控
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 考试科目名称
        layout.addWidget(QLabel("考试科目名称："))
        self.name_edit = QLineEdit()
        self.name_edit.setMinimumHeight(30)
        layout.addWidget(self.name_edit)
        
        # 考试日期
        layout.addWidget(QLabel("考试日期（格式：YYYY-MM-DD 或 YYYY/MM/DD）："))
        self.date_edit = QLineEdit()
        self.date_edit.setMinimumHeight(30)
        layout.addWidget(self.date_edit)
        
        # 考试开始时间
        layout.addWidget(QLabel("考试开始时间（格式：HH:MM:SS）："))
        self.start_edit = QLineEdit()
        self.start_edit.setMinimumHeight(30)
        layout.addWidget(self.start_edit)
        
        # 考试结束时间
        layout.addWidget(QLabel("考试结束时间（格式：HH:MM:SS）："))
        self.end_edit = QLineEdit()
        self.end_edit.setMinimumHeight(30)
        layout.addWidget(self.end_edit)
        
        # 确认按钮居中显示
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        self.confirm_btn = QPushButton("确认")
        self.confirm_btn.setMinimumHeight(40)
        self.confirm_btn.clicked.connect(self.accept)
        btn_layout.addWidget(self.confirm_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        # 预填数据（编辑模式）
        if exam:
            self.name_edit.setText(exam.get("name", ""))
            date_part = exam.get("start", "").split('T')
            if len(date_part) == 2:
                self.date_edit.setText(date_part[0])
                self.start_edit.setText(date_part[1])
            self.end_edit.setText(exam.get("end", "").split('T')[-1])
    
    def get_data(self):
        name = self.name_edit.text().strip()
        date = self.date_edit.text().strip()
        start_time = self.start_edit.text().strip()
        end_time = self.end_edit.text().strip()
        if not name or not date or not start_time or not end_time:
            QMessageBox.critical(self, "错误", "所有字段都不能为空，请重新输入。")
            return None
        try:
            date = format_date(date)
        except ValueError:
            QMessageBox.critical(self, "错误", "日期格式错误，请重新输入。")
            return None
        start = f"{date}T{convert_colon(start_time)}"
        end = f"{date}T{convert_colon(end_time)}"
        if not validate_datetime(start) or not validate_datetime(end):
            QMessageBox.critical(self, "错误", "时间格式错误，请重新输入。")
            return None
        return {"name": name, "start": start, "end": end}

# 对话框：保存到JSON配置
class SaveDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("保存到JSON")
        self.resize(300, 250)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("考试标题："))
        self.exam_name_edit = QLineEdit()
        layout.addWidget(self.exam_name_edit)
        layout.addWidget(QLabel("考试副标题："))
        self.message_edit = QLineEdit()
        layout.addWidget(self.message_edit)
        layout.addWidget(QLabel("考场号："))
        self.room_edit = QLineEdit()
        layout.addWidget(self.room_edit)
        btn_layout = QHBoxLayout()
        self.confirm_btn = QPushButton("确认")
        self.confirm_btn.clicked.connect(self.accept)
        btn_layout.addWidget(self.confirm_btn)
        layout.addLayout(btn_layout)
    
    def get_data(self):
        exam_name = self.exam_name_edit.text().strip()
        message = self.message_edit.text().strip()
        room = self.room_edit.text().strip()
        if not exam_name or not message or not room:
            QMessageBox.critical(self, "错误", "所有字段都不能为空，请重新输入。")
            return None
        return {"examName": exam_name, "message": message, "room": room}

# 主窗口
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.exam_infos = []
        self.setWindowTitle("考试看板配置生成")
        self.resize(600, 400)  # 调整窗口尺寸

        from PyQt6.QtWidgets import QSplitter, QFrame  # 新增局部导入

        # 使用 QSplitter 实现左右界面
        splitter = QSplitter()
        
        # 左侧：考试信息列表
        list_frame = QFrame()
        list_layout = QVBoxLayout(list_frame)
        self.list_widget = QListWidget()
        list_layout.addWidget(self.list_widget)
        
        # 右侧：控制按钮区域（垂直布局）
        btn_frame = QFrame()
        btn_layout = QVBoxLayout(btn_frame)
        btn_names = [
            ("添加考试信息", self.add_exam_info),
            ("编辑选中信息", self.edit_exam_info),
            ("删除选中信息", self.delete_exam_info),
            ("上移", self.move_up),
            ("下移", self.move_down),
            ("打开配置文件", self.open_config_file),
            ("保存到JSON", self.save_to_json)
        ]
        for text, slot in btn_names:
            btn = QPushButton(text)
            btn.setMinimumHeight(40)  # 放大按钮
            btn.clicked.connect(slot)
            btn_layout.addWidget(btn)
        btn_layout.addStretch()

        splitter.addWidget(list_frame)
        splitter.addWidget(btn_frame)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 1)
        
        central = QWidget()
        central_layout = QVBoxLayout(central)
        central_layout.addWidget(splitter)
        self.setCentralWidget(central)
    
    def update_exam_list(self):
        self.list_widget.clear()
        for info in self.exam_infos:
            self.list_widget.addItem(f"{info['name']} - {info['start']} to {info['end']}")

    def add_exam_info(self):
        dialog = ExamDialog(parent=self)
        if dialog.exec():
            data = dialog.get_data()
            if data:
                self.exam_infos.append(data)
                self.update_exam_list()

    def edit_exam_info(self):
        idx = self.list_widget.currentRow()
        if idx < 0:
            QMessageBox.critical(self, "错误", "请选择要编辑的项目信息。")
            return
        exam = self.exam_infos[idx]
        dialog = ExamDialog(exam, self)
        if dialog.exec():
            data = dialog.get_data()
            if data:
                self.exam_infos[idx] = data
                self.update_exam_list()
                QMessageBox.information(self, "成功", "考试信息已更新。")

    def delete_exam_info(self):
        idx = self.list_widget.currentRow()
        if idx < 0:
            QMessageBox.critical(self, "错误", "请选择要删除的项目。")
            return
        del self.exam_infos[idx]
        self.update_exam_list()
        QMessageBox.information(self, "成功", "考试信息已删除。")
    
    def move_up(self):
        idx = self.list_widget.currentRow()
        if idx <= 0:
            return
        self.exam_infos[idx], self.exam_infos[idx-1] = self.exam_infos[idx-1], self.exam_infos[idx]
        self.update_exam_list()
        self.list_widget.setCurrentRow(idx-1)
    
    def move_down(self):
        idx = self.list_widget.currentRow()
        if idx < 0 or idx >= len(self.exam_infos)-1:
            return
        self.exam_infos[idx], self.exam_infos[idx+1] = self.exam_infos[idx+1], self.exam_infos[idx]
        self.update_exam_list()
        self.list_widget.setCurrentRow(idx+1)

    def open_config_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "打开配置文件", "", "JSON files (*.json)")
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                config_data = json.load(f)
            self.exam_infos.clear()
            for info in config_data.get('examInfos', []):
                self.exam_infos.append(info)
            self.update_exam_list()
            QMessageBox.information(self, "成功", f"配置文件 {path} 已打开。")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"打开文件失败：{e}")

    def save_to_json(self):
        save_dialog = SaveDialog(self)
        if save_dialog.exec():
            exam_data = save_dialog.get_data()
            if not exam_data:
                return
            exam_data["examInfos"] = self.exam_infos
            # 可选择让用户选择保存路径
            save_path, _ = QFileDialog.getSaveFileName(self, "保存JSON", "exam_config.json", "JSON files (*.json)")
            if not save_path:
                return
            try:
                with open(save_path, "w", encoding="utf-8") as f:
                    json.dump(exam_data, f, ensure_ascii=False, indent=4)
                QMessageBox.information(self, "成功", f"JSON文件已生成：{save_path}")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"保存文件失败：{e}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
