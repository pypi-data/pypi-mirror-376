import os
from typing import Dict, List, Any
from .parser import XmlParser


class PythonGenerator:
    def __init__(self):
        self.parser = XmlParser()
        self.widget_mappings = {
            'Label': 'QLabel',
            'Button': 'QPushButton',
            'LineEdit': 'QLineEdit',
            'TextEdit': 'QTextEdit',
            'CheckBox': 'QCheckBox',
            'RadioButton': 'QRadioButton',
            'ComboBox': 'QComboBox',
            'SpinBox': 'QSpinBox',
            'Slider': 'QSlider',
            'ProgressBar': 'QProgressBar',
            
            'FluentWindow': 'FluentWindow',
            'TitleBar': 'TitleBar',
            'NavigationInterface': 'NavigationInterface',
            'PrimaryPushButton': 'PrimaryPushButton',
            'PushButton': 'PushButton',
            'TransparentPushButton': 'TransparentPushButton',
            'TogglePushButton': 'TogglePushButton',
            'DropDownPushButton': 'DropDownPushButton',
            'PrimaryToolButton': 'PrimaryToolButton',
            'ToolButton': 'ToolButton',
            'TransparentToolButton': 'TransparentToolButton',
            'ToggleToolButton': 'ToggleToolButton',
            'DropDownToolButton': 'DropDownToolButton',
            'RoundMenu': 'RoundMenu',
            'MenuAction': 'Action',
            'LineEdit': 'LineEdit',
            'TextEdit': 'TextEdit',
            'PlainTextEdit': 'PlainTextEdit',
            'SpinBox': 'SpinBox',
            'DoubleSpinBox': 'DoubleSpinBox',
            'DateTimeEdit': 'DateTimeEdit',
            'DateEdit': 'DateEdit',
            'TimeEdit': 'TimeEdit',
            'ComboBox': 'ComboBox',
            'CheckBox': 'CheckBox',
            'RadioButton': 'RadioButton',
            'SwitchButton': 'SwitchButton',
            'TogglePushButton': 'TogglePushButton',
            'Slider': 'Slider',
            'ProgressBar': 'QProgressBar',
            'InfoBar': 'InfoBar',
            'Toast': 'Toast',
            'MessageBox': 'MessageBox',
            'FileDialog': 'FileDialog',
            'FolderDialog': 'FolderDialog',
            'ColorDialog': 'ColorDialog',
            'FontDialog': 'FontDialog',
            
            'VBoxLayout': 'QVBoxLayout',
            'HBoxLayout': 'QHBoxLayout',
            'GridLayout': 'QGridLayout',
            'FormLayout': 'QFormLayout',
            'StackedLayout': 'QStackedLayout'
        }
    
    def generate(self, xml_file: str, output_dir: str = 'dist') -> str:
        parsed_data = self.parser.parse(xml_file)
        
        # 存储样式信息供后续使用
        self.styles = parsed_data.get('styles', {})
        
        imports = parsed_data.get('imports', {})
        widgets = parsed_data.get('widgets', {})
        layouts = parsed_data.get('layouts', {})
        events = parsed_data.get('events', {})
        actions = parsed_data.get('actions', {})
        window_props = parsed_data.get('window_properties', {})
        
        window_title = window_props.get('title', 'Generated Window')
        window_width = window_props.get('width', 800)
        window_height = window_props.get('height', 600)
        
        imports_code = self._generate_imports(imports)
        widgets_code = self._generate_widgets_creation(widgets)
        layouts_code = self._generate_layouts(layouts, widgets)
        styles_code = self._generate_styles_application(self.styles)
        events_binding_code = self._generate_events_binding(events)
        event_handlers_code = self._generate_event_handlers(events, actions)
        
        window_setup = self._generate_window_setup(window_props)
        
        class_code = self._generate_window_class(
            parsed_data={
                'imports': imports,
                'widgets': widgets,
                'layouts': layouts,
                'styles': self.styles,
                'events': events,
                'actions': actions,
                'window_properties': window_props
            },
            events_binding_code=events_binding_code,
            event_handlers_code=event_handlers_code
        )
        
        main_code = self._generate_main_function(window_props)
        
        python_code = f"""# 自动生成的代码，由 {xml_file} 转换而来
# 请勿手动修改此文件，所有更改应在XML文件中进行

{imports_code}

{class_code}

{main_code}
"""
        
        base_name = os.path.splitext(os.path.basename(xml_file))[0]
        output_file = os.path.join(output_dir, f"{base_name}.py")
        
        os.makedirs(output_dir, exist_ok=True)
        
        # 删除已存在的文件
        if os.path.exists(output_file):
            os.remove(output_file)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(python_code)
        
        return output_file
    
    def _generate_python_code(self, parsed_data: Dict[str, Any], xml_file: str) -> str:
        imports = self._generate_imports(parsed_data['imports'])
        
        window_class = self._generate_window_class(parsed_data)
        
        main_function = self._generate_main_function(parsed_data['window_properties'])
        
        python_code = f"""# 自动生成的代码，由 {xml_file} 转换而来
# 请勿手动修改此文件，所有更改应在XML文件中进行

{imports}

{window_class}

{main_function}
"""
        return python_code
    
    def _generate_imports(self, imports: List[str]) -> str:
        import_statements = [
            "import sys",
            "from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QLabel, QPushButton, QLineEdit, QTextEdit, QCheckBox, QRadioButton, QComboBox, QSpinBox, QSlider, QProgressBar, QVBoxLayout, QHBoxLayout, QGridLayout, QFormLayout, QStackedLayout",
            "from PyQt5.QtCore import Qt, QSize, QPoint, QRect, pyqtSignal, pyqtSlot",
            "from PyQt5.QtGui import QFont, QColor, QIcon, QPixmap"
        ]
        
        import_statements.append("from qfluentwidgets import *")
        
        for imp in imports:
            if imp.startswith('import ') or imp.startswith('from '):
                is_duplicate = False
                for existing in import_statements:
                    if imp.startswith('from ') and existing.startswith('from '):
                        imp_module = imp.split(' ')[1]
                        existing_module = existing.split(' ')[1]
                        if imp_module == existing_module:
                            is_duplicate = True
                            break
                    elif imp.startswith('import ') and existing.startswith('import '):
                        imp_module = imp.split(' ')[1]
                        existing_module = existing.split(' ')[1]
                        if imp_module == existing_module:
                            is_duplicate = True
                            break
                
                if not is_duplicate:
                    import_statements.append(imp)
            else:
                imp_statement = f"import {imp}"
                if imp_statement not in import_statements and imp not in ['sys', 'os']:
                    import_statements.append(imp_statement)
        
        return "\n".join(import_statements)
    
    def _generate_window_class(self, parsed_data: Dict[str, Any], events_binding_code: str = "pass", event_handlers_code: str = "") -> str:
        window_props = parsed_data['window_properties']
        window_title = window_props.get('title', 'Window')
        window_width = window_props.get('width', '800')
        window_height = window_props.get('height', '600')
        
        actions = parsed_data.get('actions', {})
        
        window_setup = self._generate_window_setup(window_props)
        
        class_code = f"""
class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("{window_title}")
        self.resize({window_width}, {window_height})
        
        {window_setup}
        
        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)
        
        self.init_ui()
        
        self.bind_events()
    
    def init_ui(self):
        {self._generate_widgets_creation(parsed_data['widgets'])}
        
        {self._generate_layouts(parsed_data['layouts'], parsed_data['widgets'])}
        
        {self._generate_styles_application(parsed_data['styles'])}
    
    def bind_events(self):
        {events_binding_code}
    
    {event_handlers_code}
"""
        return class_code
    
    def _generate_widgets_creation(self, widgets: Dict[str, Dict[str, Any]]) -> str:
        code_lines = []
        for widget_id, widget_info in widgets.items():
            widget_type = widget_info['type']
            
            pyqt_type = self.widget_mappings.get(widget_type, 'QWidget')
            
            if pyqt_type == 'QWidget' and widget_type != 'Widget':
                print(f"Warning: Unknown widget type '{widget_type}' for widget '{widget_id}', defaulting to QWidget")
            
            code_lines.append(f"self.{widget_id} = {pyqt_type}(self.central_widget)")
            
            for prop, value in widget_info['properties'].items():
                if prop != 'id':
                    if prop == 'text':
                        code_lines.append(f"self.{widget_id}.setText({self._format_property_value(value)})")
                    elif prop == 'placeholder':
                        code_lines.append(f"self.{widget_id}.setPlaceholderText({self._format_property_value(value)})")
                    elif prop == 'minimum':
                        code_lines.append(f"self.{widget_id}.setMinimum({self._format_property_value(value)})")
                    elif prop == 'maximum':
                        code_lines.append(f"self.{widget_id}.setMaximum({self._format_property_value(value)})")
                    elif prop == 'value':
                        code_lines.append(f"self.{widget_id}.setValue({self._format_property_value(value)})")
                    elif prop == 'styleSheet':
                        code_lines.append(f"self.{widget_id}.setStyleSheet({self._format_property_value(value)})")
                    elif prop == 'style':
                        style_name = self._format_property_value(value).strip('"\'')
                        if style_name in self.styles:
                            style_sheet = ""
                            for prop_name, prop_value in self.styles[style_name].items():
                                css_prop = prop_name.replace('_', '-')
                                style_sheet += f"{css_prop}: {prop_value}; "
                            code_lines.append(f"self.{widget_id}.setStyleSheet('{style_sheet}')")
                        else:
                            code_lines.append(f"self.{widget_id}.setStyleSheet({self._format_property_value(value)})")
                    else:
                        code_lines.append(f"self.{widget_id}.set{prop.capitalize()}({self._format_property_value(value)})")
        
        return "\n        ".join(code_lines)
    
    def _generate_layouts(self, layouts: Dict[str, Any], widgets: Dict[str, Any] = None) -> str:
        code = []
        
        if widgets is None:
            widgets = {}
        
        for layout_id, layout_info in layouts.items():
            layout_type = layout_info.get('type', 'VBoxLayout')
            
            if not layout_type.startswith('Q'):
                layout_type = 'Q' + layout_type
            
            code.append(f"        # 创建布局 {layout_id}")
            code.append(f"        self.{layout_id} = {layout_type}()")
            
            properties = layout_info.get('properties', {})
            for prop, value in properties.items():
                if prop not in ['id', 'type']:
                    if prop == 'spacing':
                        code.append(f"        self.{layout_id}.setSpacing({value})")
                    elif prop == 'margin':
                        code.append(f"        self.{layout_id}.setContentsMargins({value}, {value}, {value}, {value})")
                    elif prop == 'margins':
                        if isinstance(value, str) and ',' in value:
                            margins = [m.strip() for m in value.split(',')]
                            if len(margins) == 4:
                                code.append(f"        self.{layout_id}.setContentsMargins({margins[0]}, {margins[1]}, {margins[2]}, {margins[3]})")
                            elif len(margins) == 1:
                                code.append(f"        self.{layout_id}.setContentsMargins({margins[0]}, {margins[0]}, {margins[0]}, {margins[0]})")
                        else:
                            code.append(f"        self.{layout_id}.setContentsMargins({value}, {value}, {value}, {value})")
                    else:
                        code.append(f"        self.{layout_id}.setProperty('{prop}', '{value}')")
            
            code.append("")
        
        for layout_id, layout_info in layouts.items():
            children = layout_info.get('children', [])
            
            for child in children:
                if isinstance(child, dict):
                    child_id = child.get('id')
                    child_type = child.get('type')
                else:
                    child_id = child
                    child_type = None
                
                if child_type is None:
                    if child_id in widgets:
                        child_type = 'widget'
                    elif child_id in layouts:
                        child_type = 'layout'
                
                if child_type == 'widget' or (child_type in ['Label', 'Button', 'LineEdit', 'TextEdit', 'CheckBox', 'RadioButton', 'ComboBox', 'SpinBox', 'Slider', 'ProgressBar']):
                    code.append(f"        # 将控件 {child_id} 添加到布局 {layout_id}")
                    code.append(f"        self.{layout_id}.addWidget(self.{child_id})")
                elif child_type == 'layout' or (child_type in ['VBoxLayout', 'HBoxLayout', 'GridLayout', 'FormLayout', 'StackedLayout']):
                    code.append(f"        # 将布局 {child_id} 添加到布局 {layout_id}")
                    code.append(f"        self.{layout_id}.addLayout(self.{child_id})")
        
        main_layout_id = None
        for layout_id, layout_info in layouts.items():
            if layout_info.get('is_main', False):
                main_layout_id = layout_id
                break
        
        if main_layout_id is None and layouts:
            main_layout_id = next(iter(layouts.keys()))
        
        if main_layout_id:
            code.append(f"        # 设置主布局 (使用 {main_layout_id})")
            code.append(f"        self.central_widget.setLayout(self.{main_layout_id})")
        
        code.append("")
        return "\n".join(code)
    
    def _generate_styles_application(self, styles: Dict[str, Dict[str, str]]) -> str:
        if not styles:
            return "pass"
        
        code_lines = []
        for style_name, style_props in styles.items():
            style_sheet = ""
            for prop, value in style_props.items():
                css_prop = prop.replace('_', '-')
                style_sheet += f"{css_prop}: {value}; "
            
            if style_sheet:
                code_lines.append(f"if hasattr(self, '{style_name}'):")
                code_lines.append(f"    self.{style_name}.setStyleSheet('{style_sheet}')")
        
        return "\n        ".join(code_lines) if code_lines else "pass"
    
    def _generate_events_binding(self, events: Dict[str, Dict[str, str]]) -> str:
        if not events:
            return "pass"
        
        code_lines = []
        for widget_id, widget_events in events.items():
            for event_type, handler in widget_events.items():
                if event_type == 'click':
                    code_lines.append(f"self.{widget_id}.clicked.connect(self.{handler})")
                elif event_type == 'change':
                    code_lines.append(f"self.{widget_id}.textChanged.connect(self.{handler})")
                elif event_type == 'toggle':
                    code_lines.append(f"self.{widget_id}.checkedChanged.connect(self.{handler})")
                elif event_type == 'select':
                    code_lines.append(f"self.{widget_id}.currentIndexChanged.connect(self.{handler})")
                elif event_type == 'clicked':
                    code_lines.append(f"self.{widget_id}.clicked.connect(self.{handler})")
                else:
                    code_lines.append(f"# 未知事件类型: {event_type}")
                    code_lines.append(f"# self.{widget_id}.{event_type}.connect(self.{handler})")
        
        result = "\n        ".join(code_lines) if code_lines else "pass"
        return result
    
    def _generate_event_handlers(self, events: Dict[str, Dict[str, str]], actions: Dict[str, List[Dict[str, str]]]) -> str:
        if not events:
            return ""
        
        handlers = set()
        for widget_events in events.values():
            for handler in widget_events.values():
                handlers.add(handler)
        
        code_lines = []
        for handler in handlers:
            action_code = ""
            for widget_id, widget_events in events.items():
                for event_type, handler_name in widget_events.items():
                    if handler_name == handler:
                        key = f"{widget_id}.{event_type}"
                        if key in actions:
                            for action in actions[key]:
                                action_type = action['type']
                                target = action['target']
                                
                                if action_type == 'execute':
                                    action_code += f"""
        import subprocess
        import os
        
        target_path = '{target}'.replace('\\\\', '/')
        if target_path.lower().endswith(('.bat', '.cmd')):
            try:
                if not os.path.isabs(target_path):
                    target_path = os.path.join(os.getcwd(), target_path)
                
                subprocess.Popen([target_path], shell=True)
                if hasattr(self, 'result_label'):
                    self.result_label.setText(f"已执行: {{target_path}}")
            except Exception as e:
                if hasattr(self, 'result_label'):
                    self.result_label.setText(f"执行失败: {{str(e)}}")
        elif target_path.lower().endswith(('.exe', '.com')):
            try:
                subprocess.Popen([target_path], shell=True)
                if hasattr(self, 'result_label'):
                    self.result_label.setText(f"已启动: {{target_path}}")
            except Exception as e:
                if hasattr(self, 'result_label'):
                    self.result_label.setText(f"启动失败: {{str(e)}}")
        else:
            try:
                subprocess.Popen(target_path, shell=True)
                if hasattr(self, 'result_label'):
                    self.result_label.setText(f"已执行命令: {{target_path}}")
            except Exception as e:
                if hasattr(self, 'result_label'):
                    self.result_label.setText(f"执行失败: {{str(e)}}")
"""
                                elif action_type == 'open':
                                    action_code += f"""
        import subprocess
        import platform
        
        target_path = '{target}'.replace('\\\\', '/')
        try:
            if platform.system() == 'Windows':
                os.startfile(target_path)
            elif platform.system() == 'Darwin':
                subprocess.Popen(['open', target_path])
            else:
                subprocess.Popen(['xdg-open', target_path])
            if hasattr(self, 'result_label'):
                self.result_label.setText(f"已打开: {{target_path}}")
        except Exception as e:
            if hasattr(self, 'result_label'):
                self.result_label.setText(f"打开失败: {{str(e)}}")
"""
                                elif action_type == 'browse':
                                    action_code += f"""
        import webbrowser
        
        target_url = '{target}'.replace('\\\\', '/')
        try:
            webbrowser.open(target_url)
            if hasattr(self, 'result_label'):
                self.result_label.setText(f"已打开网页: {{target_url}}")
        except Exception as e:
            if hasattr(self, 'result_label'):
                self.result_label.setText(f"打开网页失败: {{str(e)}}")
"""
            
            code_lines.append(f"""
    def {handler}(self):
        print("事件处理函数: {handler} 被调用")
{action_code}""")
        
        return "\n".join(code_lines) if code_lines else ""
    
    def _generate_main_function(self, window_props: Dict[str, str]) -> str:
        return """
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
"""
    
    def _generate_window_setup(self, window_props: Dict[str, str]) -> str:
        code = []
        
        if window_props:
            code.append("        # 设置窗口属性")
            for prop, value in window_props.items():
                if prop == 'title':
                    continue
                elif prop == 'size':
                    if isinstance(value, str) and ',' in value:
                        width, height = [v.strip() for v in value.split(',')]
                        code.append(f"        self.resize({width}, {height})")
                    else:
                        code.append(f"        self.resize({value}, {value})")
                elif prop == 'width' or prop == 'height':
                    continue
                elif prop == 'x':
                    code.append(f"        self.move({value}, self.y())")
                elif prop == 'y':
                    code.append(f"        self.move(self.x(), {value})")
                elif prop == 'position':
                    if isinstance(value, str) and ',' in value:
                        x, y = [v.strip() for v in value.split(',')]
                        code.append(f"        self.move({x}, {y})")
                elif prop == 'resizable':
                    resizable = value.lower() in ['true', 'yes', '1']
                    if not resizable:
                        code.append("        self.setFixedSize(self.size())")
                elif prop == 'maximized':
                    if value.lower() in ['true', 'yes', '1']:
                        code.append("        self.showMaximized()")
                elif prop == 'minimized':
                    if value.lower() in ['true', 'yes', '1']:
                        code.append("        self.showMinimized()")
                elif prop == 'fullscreen':
                    if value.lower() in ['true', 'yes', '1']:
                        code.append("        self.showFullScreen()")
                else:
                    code.append(f"        self.setProperty('{prop}', '{value}')")
            code.append("")
        
        return "\n".join(code)
    
    def _format_property_value(self, value: str) -> str:
        if value.lower() in ('true', 'false'):
            return value.capitalize()
        
        try:
            int(value)
            return value
        except ValueError:
            pass
        
        try:
            float(value)
            return value
        except ValueError:
            pass
        
        return f'"{value}"'