from setuptools import setup, find_packages

setup(
    name="AnChinSegmenter",  # 包名
    version="0.1",
    packages=find_packages(),  # 自动发现包含 __init__.py 的模块
    include_package_data=True,
    package_data={
        'AnChinSegmenter': ['model/*', 'data/*', 'pytorch_pretrained_bert/*', 'logs/*'],  # 使用相对路径
    },
    install_requires=[
        "torch==1.11.0",
        "tqdm",
        "pandas",
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
)
