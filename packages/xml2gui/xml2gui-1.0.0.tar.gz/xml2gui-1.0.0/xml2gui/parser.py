import xml.etree.ElementTree as ET
from typing import Dict, List, Any, Optional, Tuple


class XmlParser:
    def __init__(self):
        self.widgets = {}
        self.layouts = {}
        self.events = {}
        self.styles = {}
        self.imports = set()
        self.window_properties = {}
        self.actions = {}
    
    def parse(self, xml_file: str) -> Dict[str, Any]:
        try:
            tree = ET.parse(xml_file)
            root = tree.getroot()
            
            self._parse_window_properties(root)
            self._parse_imports(root)
            self._parse_styles(root)
            self._parse_layouts_and_widgets(root)
            self._parse_events(root)
            self._parse_actions(root)
            
            return {
                'window_properties': self.window_properties,
                'imports': list(self.imports),
                'styles': self.styles,
                'widgets': self.widgets,
                'layouts': self.layouts,
                'events': self.events,
                'actions': self.actions
            }
        except Exception as e:
            print(f"解析XML文件时出错: {e}")
            return {}
    
    def _parse_window_properties(self, root):
        if root.tag == 'window':
            for attr, value in root.attrib.items():
                self.window_properties[attr] = value
        else:
            window = root.find('window')
            if window is not None:
                for attr, value in window.attrib.items():
                    self.window_properties[attr] = value
    
    def _parse_imports(self, root):
        imports = root.find('imports')
        if imports is not None:
            for imp in imports.findall('import'):
                module = imp.get('module', '')
                if not module and imp.text:
                    module = imp.text.strip()
                if module:
                    self.imports.add(module)
    
    def _parse_styles(self, root):
        styles = root.find('styles')
        if styles is not None:
            for style in styles.findall('style'):
                name = style.get('name', '')
                if name:
                    self.styles[name] = {}
                    for prop in style:
                        self.styles[name][prop.tag] = prop.text
    
    def _parse_layouts_and_widgets(self, root):
        layouts = root.find('layouts')
        
        if layouts is None:
            layout = root.find('layout')
            if layout is not None:
                layouts = [layout]
        
        if layouts is None:
            special_tags = ['imports', 'styles', 'events', 'actions', 'window']
            for child in root:
                child_type = child.get('type', child.tag)
                if child_type in ['VBoxLayout', 'HBoxLayout', 'QGridLayout', 'QFormLayout', 'QStackedLayout', 'FormLayout'] and child.tag not in special_tags:
                    layouts = root
                    break
        
        if layouts is not None:
            layouts_to_process = list(layouts)
            processed_layouts = set()
            layout_counter = 0
            
            while layouts_to_process:
                layout = layouts_to_process.pop(0)
                layout_id = layout.get('id', '')
                layout_type = layout.get('type', layout.tag)
                
                if not layout_id:
                    layout_id = f"layout_{layout_counter}"
                    layout_counter += 1
                
                if layout_id not in processed_layouts:
                    self.layouts[layout_id] = {
                        'type': layout_type,
                        'properties': dict(layout.attrib),
                        'children': []
                    }
                    print(f"Added layout: {layout_id} of type {layout_type}")
                    processed_layouts.add(layout_id)
                    
                    for child in layout:
                        child_id = child.get('id', '')
                        child_type = child.get('type', child.tag)
                        if child_id and child_type in ['VBoxLayout', 'HBoxLayout', 'QGridLayout', 'QFormLayout', 'QStackedLayout', 'FormLayout']:
                            layouts_to_process.append(child)
            
            for layout_id in processed_layouts:
                layout_xml = None
                for layout in layouts:
                    if layout.get('id', '') == layout_id or (not layout.get('id', '') and layout_id.startswith('layout_') and layout_id == f"layout_{list(self.layouts.keys()).index(layout_id)}"):
                        layout_xml = layout
                        break
                
                if layout_xml is None:
                    for parent_layout in layouts:
                        for child in parent_layout:
                            if child.get('id', '') == layout_id or (not child.get('id', '') and layout_id.startswith('layout_') and layout_id == f"layout_{list(self.layouts.keys()).index(layout_id)}"):
                                layout_xml = child
                                break
                
                if layout_xml is not None:
                    for child in layout_xml:
                        child_id = child.get('id', '')
                        child_type = child.get('type', child.tag)
                        print(f"Found child: {child_id} of type {child_type} in layout {layout_id}")
                        
                        if not child_id:
                            if child_type in ['VBoxLayout', 'HBoxLayout', 'QGridLayout', 'QFormLayout', 'QStackedLayout', 'FormLayout']:
                                child_id = f"{child_type.lower()}_{layout_counter}"
                                layout_counter += 1
                            else:
                                child_id = f"{child_type.lower()}_{len(self.widgets)}"
                        
                        if child_type in ['VBoxLayout', 'HBoxLayout', 'QGridLayout', 'QFormLayout', 'QStackedLayout', 'FormLayout']:
                            if child_id not in self.layouts:
                                self.layouts[child_id] = {
                                    'type': child_type,
                                    'properties': dict(child.attrib),
                                    'children': []
                                }
                                print(f"Added nested layout: {child_id} to layout {layout_id}")
                            self.layouts[layout_id]['children'].append(child_id)
                            
                            for nested_child in child:
                                nested_child_id = nested_child.get('id', '')
                                nested_child_type = nested_child.get('type', nested_child.tag)
                                print(f"Found nested child: {nested_child_id} of type {nested_child_type} in layout {child_id}")
                                
                                if not nested_child_id:
                                    if nested_child_type in ['VBoxLayout', 'HBoxLayout', 'QGridLayout', 'QFormLayout', 'QStackedLayout', 'FormLayout']:
                                        nested_child_id = f"{nested_child_type.lower()}_{layout_counter}"
                                        layout_counter += 1
                                    else:
                                        nested_child_id = f"{nested_child_type.lower()}_{len(self.widgets)}"
                                
                                if nested_child_type in ['VBoxLayout', 'HBoxLayout', 'QGridLayout', 'QFormLayout', 'QStackedLayout', 'FormLayout']:
                                    if nested_child_id not in self.layouts:
                                        self.layouts[nested_child_id] = {
                                            'type': nested_child_type,
                                            'properties': dict(nested_child.attrib),
                                            'children': []
                                        }
                                        print(f"Added nested layout: {nested_child_id} to layout {child_id}")
                                    self.layouts[child_id]['children'].append(nested_child_id)
                                else:
                                    properties = dict(nested_child.attrib)
                                    properties.pop('id', None)
                                    properties.pop('type', None)
                                    
                                    for prop in nested_child.findall('property'):
                                        prop_name = prop.get('name', '')
                                        if prop_name and prop.text:
                                            properties[prop_name] = prop.text
                                    
                                    nested_child_info = {
                                        'type': nested_child_type,
                                        'properties': properties,
                                        'parent_layout': child_id
                                    }
                                    self.widgets[nested_child_id] = nested_child_info
                                    print(f"Added widget: {nested_child_id} of type {nested_child_type} to layout {child_id}")
                        else:
                            properties = dict(child.attrib)
                            properties.pop('id', None)
                            properties.pop('type', None)
                            
                            for prop in child.findall('property'):
                                prop_name = prop.get('name', '')
                                if prop_name and prop.text:
                                    properties[prop_name] = prop.text
                            
                            child_info = {
                                'type': child_type,
                                'properties': properties,
                                'parent_layout': layout_id
                            }
                            self.widgets[child_id] = child_info
                            self.layouts[layout_id]['children'].append(child_id)
                            print(f"Added widget: {child_id} of type {child_type} to layout {layout_id}")
    
    def _parse_events(self, root):
        events = root.find('events')
        if events is not None:
            for event in events.findall('event'):
                widget_id = event.get('widget', '')
                event_type = event.get('type', '')  # 使用 'type' 属性
                handler = event.get('handler', '')
                
                if widget_id and event_type and handler:
                    if widget_id not in self.events:
                        self.events[widget_id] = {}
                    
                    self.events[widget_id][event_type] = handler
    
    def _parse_actions(self, root):
        actions = root.find('actions')
        if actions is not None:
            for action in actions.findall('action'):
                widget_id = action.get('widget', '')
                event_type = action.get('event', '')
                action_type = action.get('type', '')
                target = action.get('target', '')
                
                if widget_id and event_type and action_type and target:
                    key = f"{widget_id}.{event_type}"
                    if key not in self.actions:
                        self.actions[key] = []
                    
                    self.actions[key].append({
                        'type': action_type,
                        'target': target
                    })