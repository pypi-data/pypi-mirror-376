# -*- coding：utf-8 -*-
# 项目名称：pypi_zc_tools
# 编辑文件名：setup
# 系统日期：2025/9/13
# 编辑用户：ZC
from distutils.core import setup
from setuptools import find_packages

with open("README.md","r",encoding="utf-8") as f:
    long_description = f.read()

# 读取依赖
def parse_requirements(filename):
    with open(filename, 'r', encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip() and not line.startswith('#')]

setup(name="pypi_zc_tools",
      version='1.0.1',
      description="数据生成工具",
      long_description=long_description,
      long_description_content_type="text/markdown",
      author="jochen",
      author_email='1099560198@qq.com',
      url='https://gitee.com/zc_ceshi/pypi_zc_tools',
      install_requires=parse_requirements('requirements.txt'),
      license='MIT License',
      packages=find_packages(),
      platforms=['all'],
      entry_points={
        'console_scripts': [
            'pypi-zc-tools=pypi_zc_tools.create_excel_data:generate_data'
        ]
            },
      classifiers=[
          'Intended Audience :: Developers',
          'Operating System :: OS Independent',
          'Natural Language :: Chinese (Simplified)',
          'Programming Language :: Python',
          'Programming Language :: Python :: 3',
          'Programming Language :: Python :: 3.6',
          'Programming Language :: Python :: 3.7',
          'Programming Language :: Python :: 3.8',
          'Programming Language :: Python :: 3.9',
          'Programming Language :: Python :: 3.10',
          'Topic :: Software Development :: Libraries',
          'Topic :: Office/Business :: Financial :: Spreadsheet',
          'Topic :: Utilities'
      ],
      python_requires='>=3.6',
      )

if __name__ == "__main__":
    print("setup.py 语法检查通过！")