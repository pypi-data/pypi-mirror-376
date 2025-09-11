from setuptools import setup, find_packages

setup(
    name="pwpy_db",
    version="0.1.0",
    author="Kamlesh Kumar",
    author_email="kamlesh.kumar2@pw.live",
    description="Secure Trino connector for Python with pandas output",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/kamlesh1114/pwpy_db",
    packages=find_packages(),
    install_requires=[
        "trino>=0.319",
        "pandas>=1.0",
        "python-dotenv>=1.0",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.8',
)
