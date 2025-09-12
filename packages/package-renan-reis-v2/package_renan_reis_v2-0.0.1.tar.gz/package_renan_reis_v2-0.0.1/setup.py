from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as f:
    page_description = f.read()

with open("requirements.txt") as f:
    requirements = f.read().splitlines()

setup(
    name="package-renan-reis-v2",  # precisa ser único
    version="0.0.1",
    author="Renan Reis",
    author_email="renanreis.gomes@gmail.com",
    description="Pacote simples de processamento de imagens",
    long_description=page_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Nanre-33/simple-package-template",  # vírgula aqui ✅
    packages=find_packages(),
    install_requires=requirements,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],

    python_requires=">=3.8",
    
)
