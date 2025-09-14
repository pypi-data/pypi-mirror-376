from setuptools import setup, find_packages

setup(
    name="pybytebeat",
    version="0.1.0",
    packages=find_packages(),
    install_requires=["numpy", "sounddevice"],
    author="Yousuf Yaqoob Awadh Ali Salam Al Hadhrami",
    author_email="gethdc92@gmail.com",
    description="Python bytebeat generator",
    long_description_content_type="text/markdown",
    url="https://github.com/Yousuf-Al-Hadhrami/PyByteBeat",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    license="CC0-1.0",
    python_requires='>=3.7',
)