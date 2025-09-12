from setuptools import setup, find_packages

setup(
    name="ClassicalSplit",  # 包名
    version="1.3",
    packages=find_packages(),  # 自动发现包含 __init__.py 的模块
    include_package_data=True,
    package_data={
        'AnChinSegmenter': ['model/*', 'data/*', 'pytorch_pretrained_bert/*', 'logs/*'],  # 使用相对路径
    },
    install_requires=[
        "torch>=1.11,<2.0",
        "huggingface_hub>=0.16.4",
        "tqdm",
        "pandas",
        "requests>=2.30.0",
        "boto3",
        "requests",
        "regex",
        "seqeval",
        "psutil",
        "matplotlib"
    ],
    entry_points={
        'console_scripts': [
            'segmenter = AnChinSegmenter.segmenter:main',  # 可选：命令行调用
        ]
    },
    author="TANG, Xuemei",
    description="一个古汉语分词工具",
    python_requires='>=3.8',
    url="https://github.com/tangxuemei1995/Ancient-chinese-segmenter",
    license="MIT",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
)
