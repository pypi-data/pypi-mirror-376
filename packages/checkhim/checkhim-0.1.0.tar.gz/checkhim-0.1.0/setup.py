from setuptools import setup, find_packages

setup(
    name="checkhim",
    version="0.1.0",
    description="Python SDK for phone number verification via checkhim.tech",
    long_description=open("README.md", encoding="utf-8").read() if __import__('os').path.exists('README.md') else '',
    long_description_content_type="text/markdown",
    author="CheckHim Tech",
    author_email="opensource@checkhim.tech",
    url="https://checkhim.tech",
    packages=find_packages(),
    install_requires=["requests>=2.25.0"],
    python_requires=">=3.7",
    license="MIT",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    include_package_data=True,
)
