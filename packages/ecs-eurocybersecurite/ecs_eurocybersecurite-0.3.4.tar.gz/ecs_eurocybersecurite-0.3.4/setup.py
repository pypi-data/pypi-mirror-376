from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name='ecs-eurocybersecurite',
    version='0.3.4',
    description='Cybersecurity and AI tools by Eurocybersecurite',
    long_description=long_description,
    long_description_content_type="text/markdown",
    author='Mohamed Redha Abdessemed',
    author_email='mohamed.abdessemed@eurocybersecurite.fr',
    url='https://github.com/tuteur1/RooR',
    project_urls={
        "Documentation": "https://eurocybersecurite.fr/auth/login.php",
        "Source": "https://github.com/tuteur1/RooR.git",
        "Issues": "https://github.com/tuteur1/RooR/issues",
    },
    license='MIT',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "flask",
        "transformers",
        "torch",
        "scikit-learn"
    ],
    entry_points={
        'console_scripts': [
            'ecs-greet=ecs.core:greet',
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Security",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    keywords='cybersecurity, AI, tools, python',
    python_requires='>=3.9',
)
