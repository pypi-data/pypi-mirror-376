from setuptools import setup, find_packages

with open('README.md', 'r', encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='llm_jsonl_converter',
    version='2025.9.111721',
    author='Eugene Evstafev',
    author_email='hi@eugene.plus',
    description='A Python package for converting unstructured text into JSONL format using LLMs.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/chigwell/llm_jsonl_converter',
    packages=find_packages(),
    install_requires=[
        'langchain-core',
        'langchain-llm7',
        'llmatch-messages==2025.9.111720',
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