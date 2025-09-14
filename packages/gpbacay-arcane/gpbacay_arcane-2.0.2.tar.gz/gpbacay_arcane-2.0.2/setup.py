from setuptools import setup, find_packages

setup(
    name='gpbacay-arcane',
    version='2.0.2',
    author='Gianne P. Bacay',
    author_email='giannebacay2004@gmail.com',
    description='A neuromimetic language foundation model library with biologically-inspired neural mechanisms including spiking neural networks, Hebbian learning, and homeostatic plasticity',
    long_description=open('README.md', encoding='utf-8').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/gpbacay/gpbacay_arcane',
    packages=find_packages(),
    install_requires=[
        'numpy==1.23.5',
        'tensorflow',
        'keras',
        'matplotlib',
    ],
    py_modules=['gpbacay_arcane'],
    entry_points={
        'console_scripts': [
            'gpbacay-arcane-about = gpbacay_arcane.cli_commands:about',
            'gpbacay-arcane-list-models = gpbacay_arcane.cli_commands:list_models',
            'gpbacay-arcane-list-layers = gpbacay_arcane.cli_commands:list_layers',
            'gpbacay-arcane-version = gpbacay_arcane.cli_commands:version',
        ],
    },
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
)
