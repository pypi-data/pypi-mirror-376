from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name='cursofiap-luisa',
    version='1.0.0',
    packages=find_packages(),
    description='Descricao da sua lib cursofiap',
    author='Luisa Sousa',
    author_email='luisa.sousa@example.com',
    url='https://github.com/luisaoliveira1/cursofiap',
    license='MIT',
    long_description=long_description,
    long_description_content_type='text/markdown'
)
