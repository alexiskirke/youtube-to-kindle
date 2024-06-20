from setuptools import setup, find_packages

setup(
    name='youtube-to-kindle',
    version='1.0.0',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'openai','tinytag','pydub','pytube','ebooklib','tiktoken'
    ],
    author='Alexis Kirke',
    author_email='alexiskirke2@gmail.com',
    description='A tool to convert YouTube content to Kindle format',
    long_description=open('README.txt').read(),
    long_description_content_type='text/plain',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',
)
