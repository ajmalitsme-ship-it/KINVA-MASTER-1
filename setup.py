from setuptools import setup, find_packages

setup(
    name="mx",
    version="1.0.0",
    author="MX Language Team",
    description="MX Programming Language with runprint as main function",
    packages=find_packages(),
    py_modules=['mx_interpreter'],
    entry_points={
        'console_scripts': [
            'mx=mx_interpreter:main',
        ],
    },
    python_requires='>=3.6',
)
