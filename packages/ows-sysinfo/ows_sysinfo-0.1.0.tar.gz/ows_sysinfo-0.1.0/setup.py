from setuptools import setup, find_packages

setup(
    name="ows-sysinfo",
    version="0.1.0",
    description="Comprehensive system information collector & reporter",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    author="Your Name",
    packages=find_packages(),
    include_package_data=True,
    install_requires=["psutil>=5.9.0","py-cpuinfo>=8.0.0","requests>=2.28.0","rich>=12.0.0"],
    entry_points={"console_scripts":["ows-sysinfo=ows_sysinfo.cli:main"]},
    classifiers=["Programming Language :: Python :: 3","Operating System :: OS Independent"],
)
