from setuptools import setup, find_packages
import os

here = os.path.abspath(os.path.dirname(__file__))

# Prefer a long description from README if available
try:
    with open(os.path.join(here, 'README.md'), 'r', encoding='utf-8') as f:
        long_description = f.read()
except FileNotFoundError:
    long_description = ''

setup(
    name='llm_formats',
    version='2025.9.11135',
    author='Eugene Evstafev',
    author_email='hi@eugene.plus',
    description='Minimal llm_formats package exposing a single public function',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/chigwell/llm_formats',
    packages=find_packages(),
    install_requires=[],
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 3',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',
    license='MIT',
    tests_require=['unittest'],
    test_suite='test',
)