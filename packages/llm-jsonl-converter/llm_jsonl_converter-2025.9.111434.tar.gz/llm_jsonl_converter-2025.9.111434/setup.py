from setuptools import setup, find_packages

setup(
    name='llm_jsonl_converter',
    version='2025.9.111434',
    author='Eugene Evstafev',
    author_email='hi@eugene.plus',
    description='A Python package for converting unstructured text into JSONL format using LLMs.',
    long_description='A Python package for converting unstructured text into JSONL format using LLMs.',
    long_description_content_type='text/markdown',
    url='https://github.com/chigwell/llm_jsonl_converter',
    packages=find_packages(),
    install_requires=[
        'langchain-core',
        'langchain-llm7',
        'tqdm',
    ],
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 3',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',
    license='MIT',
)