from setuptools import setup, find_packages

with open("README.md","r",encoding="utf-8") as f:
    description = f.read()

setup(
    name='vachanatts',
    version='0.0.3',
    packages=find_packages(),
    package_data={
        'vachanatts': ['data/*'],
    },
    include_package_data=True,
    install_requires=[
        "pythainlp",
        "ssg",
        "onnxruntime"
    ],
    long_description=description,
    long_description_content_type="text/markdown",
)
