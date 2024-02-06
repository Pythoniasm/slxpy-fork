from pathlib import Path

import setuptools

cwd = Path(__file__).parent
package_dir = cwd / "slxpy"
package_data = [str(f.relative_to(package_dir)) for f in (package_dir / "include").glob("**/*") if f.is_file()] + [
    str(f.relative_to(package_dir)) for f in (package_dir / "templates").glob("**/*") if f.is_file()
]
long_description = (cwd / "README.md").read_text()

setuptools.setup(
    name="slxpy-fork",
    version="1.6.1.post3",
    description="Simulink Python binding generator.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    python_requires=">=3.8",
    license="MIT",
    keywords=["simulink", "c++", "gym", "gymnasium"],
    author="Jiang Yuxuan",
    author_email="jyx21@mails.tsinghua.edu.cn",
    url="https://github.com/Pythoniasm/slxpy-fork",
    classifiers=["Development Status :: 5 - Production/Stable", "Programming Language :: Python"],
    packages=[
        "slxpy",
        "slxpy.common",
        "slxpy.frontend",
        "slxpy.backend",
        "slxpy.cli",
    ],
    package_data={"slxpy": package_data},
    install_requires=[
        "pybind11",
        "pybind11-stubgen>=2.3",
        "Jinja2>=3.0",
        "tomli",
        "importlib_resources",
        "packaging",
        "click>=8.0",
        "numpy",
    ],
    extras_require={"gym": ["gymnasium"]},
    entry_points={
        "console_scripts": [
            "slxpy = slxpy.cli:entry_point",
        ],
    },
)
