from setuptools import setup, find_packages

with open('README.md', 'r', encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='py_template_expander',
    version='2025.9.131516',
    author='Eugene Evstafev',
    author_email='hi@eugene.plus',
    description='A simple Python library for expanding template strings with optional groups and character sets.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/chigwell/py_template_expander',
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