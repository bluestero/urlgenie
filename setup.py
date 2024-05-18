from setuptools import setup


def get_description():
    try:
        with open("README.md", encoding = "utf-8") as readme_file:
            long_description = readme_file.read()
        return long_description
    except:
        return None

setup(
    license = "MIT",
    name = "urlgenie",
    version = "1.0.0",
    packages = ["urlgenie"],
    author = "Ahmed Khatib",
    python_requires = ">=3.7",
    maintainer = "Ahmed Khatib",
    install_requires = ["tldextract"],
    long_description = get_description(),
    author_email = "ahmedkhatib99@gmail.com",
    maintainer_email = "ahmedkhatib99@gmail.com",
    long_description_content_type = "text/markdown",
    download_url = "https://github.com/bluestero/urlgenie/archive/refs/tags/1.0.0.tar.gz",
    description = "Tool to make URL extraction, generalization, validation, and filtration easy.",
    project_urls={
        "Documentation": "https://github.com/bluestero/urlgenie/blob/main/README.md",
        "Source": "https://github.com/bluestero/urlgenie",
        "Tracker": "https://github.com/bluestero/urlgenie/issues",
    },
    keywords = [
        "url-parsing",
        "data-cleaning",
        "data-curation",
        "generalization",
        "data-cleansing",
        "data-processing",
        "data-sanitization",
        "url-generalization",
    ],
    classifiers = [
        'Intended Audience :: Developers',
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        'License :: OSI Approved :: MIT License',
        'Development Status :: 5 - Production/Stable',
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
)