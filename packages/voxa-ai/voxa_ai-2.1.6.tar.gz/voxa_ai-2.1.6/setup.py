from setuptools import setup, find_packages

# Read the contents of your README file
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = fh.read().splitlines()

setup(
    name="voxa-ai",
    version="2.1.6",  # Increment the version!
    author="Zia Ur Rehman",
    author_email="ziaulrehman6349@gmail.com",
    description="Voxa AI - Hybrid Business Assistant",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Meharzain2010/Voxa-ai-Agent",
    packages=find_packages(),
    include_package_data=True,
    install_requires=requirements,
    entry_points={
        'console_scripts': [
            'voxa-ai=voxa_ai.demo_voxa:main',
        ],
    },
    scripts=[
        'voxa-ai.bat',    # Windows launcher
        'voxa-ai.sh'      # Linux/Mac launcher
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
)