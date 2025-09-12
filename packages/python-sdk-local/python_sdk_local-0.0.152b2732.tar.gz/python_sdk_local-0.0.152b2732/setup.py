import setuptools

PACKAGE_NAME = "python-sdk-local"
package_dir = PACKAGE_NAME.replace("-", "_")

# used by python -m build
# python -m build needs pyproject.toml or setup.py
setuptools.setup(
    name=PACKAGE_NAME,
    version='0.0.152b2732',  # Look on the latest published version in https://pypi.org/project/python-sdk-local and increase the patch part of the vertsion
    author="Circles",
    author_email="info@circlez.ai",
    description="PyPI Package for Circles Python SDK Local Python",
    long_description="This is a package for sharing common functions used in different repositories",
    long_description_content_type="text/markdown",
    url=f"https://github.com/circles-zone/{PACKAGE_NAME}-python-package",
    packages=[package_dir],
    package_dir={package_dir: f'{package_dir}/src'},
    package_data={package_dir: ['*.py']},
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: Other/Proprietary License",
        "Operating System :: OS Independent",
    ],
    install_requires=[
        "requests",
        "python-dotenv",
        "pyjwt",
        "python-sdk-remote",
        "user-context-remote",
    ]
)
