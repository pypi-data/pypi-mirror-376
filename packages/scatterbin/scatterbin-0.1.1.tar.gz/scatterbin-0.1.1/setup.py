from setuptools import setup, find_packages

setup(
    name='scatterbin',
    version='0.1.1',
    description='Adjustable binning of scatter plot data',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    author='Stephen Curran',
    author_email='scurran.astro@gmail.com',
    url='https://github.com/steviecurran/scatterbin',
    packages=find_packages(),
    install_requires=[
        'numpy',
        'matplotlib',
        'pandas',
        'scipy',
        'sys',
    ],
    classifiers=[
        'Programming Language :: Python :: 3',
        'Operating System :: OS Independent',
    ],
)
