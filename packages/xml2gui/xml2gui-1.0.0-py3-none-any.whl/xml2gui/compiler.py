import os
import sys
import subprocess
import shutil
from typing import Optional


class Compiler:
    """编译器，用于将Python代码编译为可执行文件"""
    
    def __init__(self):
        self.nuitka_available = self._check_nuitka()
    
    def _check_nuitka(self) -> bool:
        """检查Nuitka是否可用"""
        try:
            result = subprocess.run([sys.executable, "-m", "nuitka", "--version"], 
                                  capture_output=True, text=True)
            return result.returncode == 0
        except FileNotFoundError:
            return False
    
    def compile_to_exe(self, python_file: str, output_dir: str = 'output', 
                      icon_file: Optional[str] = None, 
                      company_name: Optional[str] = None,
                      product_name: Optional[str] = None,
                      file_version: Optional[str] = None) -> str:
        """将Python文件编译为可执行文件"""
        if not self.nuitka_available:
            print("错误: Nuitka未安装。请先安装Nuitka: pip install nuitka")
            return ""
        
        if not os.path.exists(python_file):
            print(f"错误: 文件 {python_file} 不存在")
            return ""
        
        os.makedirs(output_dir, exist_ok=True)
        
        
        cmd = [sys.executable, "-m", "nuitka", 
               "--standalone", 
               "--follow-imports",
               "--plugin-enable=pyqt5",
               "--include-package=qfluentwidgets",
               "--include-package=PyQt5",
               "--include-data-dir=.venv/Lib/site-packages/qfluentwidgets=qfluentwidgets",
               "--include-data-dir=.venv/Lib/site-packages/PyQt5=PyQt5",
               "--output-dir=" + output_dir]
        
        if icon_file and os.path.exists(icon_file):
            cmd.append(f"--windows-icon-from-ico={icon_file}")
        
        if company_name or product_name or file_version:
            version_info = []
            if company_name:
                version_info.append(f'company_name="{company_name}"')
            if product_name:
                version_info.append(f'product_name="{product_name}"')
            if file_version:
                version_info.append(f'file_version="{file_version}"')
            
            if version_info:
                cmd.append(f"--windows-file-version={file_version or '1.0.0.0'}")
                cmd.append(f"--windows-product-version={file_version or '1.0.0.0'}")
                cmd.append(f"--windows-company-name={company_name or 'Unknown'}")
                cmd.append(f"--windows-product-name={product_name or 'Application'}")
        
        cmd.append(python_file)
        
        try:
            print("开始编译...")
            print("命令:", " ".join(cmd))
            
            result = subprocess.run(cmd, check=True)
            
            
            base_name = os.path.splitext(os.path.basename(python_file))[0]
            exe_dir = os.path.join(output_dir, f"{base_name}.dist")
            
            if os.path.exists(exe_dir):
                exe_file = os.path.join(exe_dir, f"{base_name}.exe")
                
                
                final_exe_path = os.path.join(output_dir, f"{base_name}.exe")
                if os.path.exists(exe_file):
                    shutil.copy2(exe_file, final_exe_path)
                    print(f"编译成功! 可执行文件已保存到: {final_exe_path}")
                    return final_exe_path
                else:
                    print("错误: 未找到生成的可执行文件")
                    return ""
            else:
                print("错误: 编译失败，未生成输出目录")
                return ""
        
        except subprocess.CalledProcessError as e:
            print(f"编译失败: {e}")
            return ""
        except Exception as e:
            print(f"编译过程中发生错误: {e}")
            return ""