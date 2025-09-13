from setuptools import setup, find_packages

setup(
    name='vachanatts',
    version='0.0.1',
    packages=find_packages(),
    package_data={
        'vachanatts': ['data/*'],
    },
    include_package_data=True,
    install_requires=[
        "pythainlp",
        "ssg",
        "onnxruntime"
    ]
)
