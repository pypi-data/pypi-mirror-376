from setuptools import  setup,find_packages
import os
here = os.path.abspath(os.path.dirname(__file__))  

def load_requirements():
    """从requirements.txt文件读取依赖项"""
    with open('requirements.txt', 'r', encoding='utf-8-sig') as f:
        requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]
    return requirements



setup(
    name='siem_hkm_ai_smartcore',
    # packages=find_packages(),
    install_requires=load_requirements(),
    version='1.0.2',
    description="A Python library for intelligent building management with BACnet/OPC UA communication and HVAC optimization",
    long_description = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "README.md") , "r", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    author="lanzco's team",
    license='MIT',
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",  # 替换为你的许可证
        "Operating System :: OS Independent",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "Topic :: Home Automation",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    packages=find_packages(where="dist"),  # 从 dist 目录寻找包
    package_dir={"": "dist"},              # 声明包的根目录是 dist
    include_package_data=True
)


