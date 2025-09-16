from setuptools import setup, find_packages

setup(
    name="office-ruby-remover",
    version="0.1.0",
    description="Microsoft Office（Word/Excel）ドキュメントからルビ（ふりがな）を削除するツール",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    author="NTT DATA Corporation",
    author_email="your-email@example.com",
    url="https://github.com/yourusername/office-ruby-remover",
    packages=find_packages(),
    install_requires=[
        "python-docx>=0.8.11",
        "openpyxl>=3.0.0"
    ],
    entry_points={
        "console_scripts": [
            "remove-ruby=office_ruby_remover.cli:main"
        ]
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Information Technology",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Office/Business",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Text Processing :: Markup",
    ],
    python_requires=">=3.8",
    keywords=["office", "word", "excel", "ruby", "furigana", "document", "processing"],
    project_urls={
        "Bug Reports": "https://github.com/yourusername/office-ruby-remover/issues",
        "Source": "https://github.com/yourusername/office-ruby-remover",
    },
)