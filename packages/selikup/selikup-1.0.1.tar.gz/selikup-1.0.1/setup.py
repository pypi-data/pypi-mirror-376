from setuptools import setup

setup(
    name="selikup",
    version="1.0.1",
    description="Kernel indirip kurmaya yardımcı araç",
    author="Fatih Önder",
    author_email="fatih@algyazilim.com",
    py_modules=["selikup"],  # sadece selikup.py
    entry_points={
        "console_scripts": [
            "selikup=selikup:main",  # selikup.py içindeki main() fonksiyonunu çağıracak
        ],
    },
)

