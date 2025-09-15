from setuptools import setup, find_packages
with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()
setup(
    name='ecs-eurocybersecurite',
    version='0.2.0',
    description='Cybersecurity and AI tools by Eurocybersecurite',
    long_description=long_description,
    long_description_content_type="text/markdown",
    author='Mohamed Redha Abdessemed',
    author_email='mohamed.abdessemed@eurocybersecurite.fr',
    url='https://github.com/tuteur1/RooR',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "flask",
        "transformers",
        "torch",
        "scikit-learn"
    ],
    python_requires='>=3.9',
)
