from setuptools import setup, find_packages

setup(
    name='pkq1',
    version='0.1.0',
    packages=find_packages(),
    install_requires=[
        'numpy>=1.19.0',
        'matplotlib>=3.3.0',
    ],
    author='CETQAP',
    author_email='info@thecetqap.com',
    description='A quantum circuit simulator for beginners, the first from Pakistan!',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/CETQAP/pkq1',  # Optional
    license='MIT',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',
)
