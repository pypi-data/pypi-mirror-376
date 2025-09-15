# setup.py
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name='Eurocybersecurite-AI-Cybersecurity',
    version='0.2.3',
    description='AI-powered cybersecurity application by Eurocybersecurite',
    long_description=long_description,
    long_description_content_type="text/markdown",

    # ✅ Auteur et contact
    author='Eurocybersecurite',
    author_email='mohamed.abdessemed@eurocybersecurite.fr',
    maintainer='Mohamed Abdessemed',
    maintainer_email='mohamed.abdessemed@eurocybersecurite.fr',

    # ✅ Homepage principale (ex: GitHub du projet)
    url='https://github.com/tuteur1/RooR',

    # ✅ Liens complémentaires
    project_urls={
        "Documentation": "https://eurocybersecurite.fr/auth/login.php",
        "Source": "https://github.com/tuteur1/RooR.git",
        "Issues": "https://github.com/tuteur1/RooR/issues",
    },

    license='MIT',
    packages=find_packages(where='RooR'),
    include_package_data=True,
    install_requires=[
        "flask",
        "transformers",
        "torch",
        "scikit-learn"
    ],
    entry_points={
        'console_scripts': [
            'cybersecurity=main:main',
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: Information Technology",
        "Topic :: Security",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    keywords='cybersecurity, audit, remediation, AI, machine-learning, flask, python, qwen, transformers',
    python_requires='>=3.9',
)
