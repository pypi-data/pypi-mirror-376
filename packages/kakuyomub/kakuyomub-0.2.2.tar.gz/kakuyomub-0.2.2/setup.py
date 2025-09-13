from setuptools import setup, find_packages        
from pathlib import Path
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding='utf-8')
setup(
    name = "kakuyomub",      #name of the package
    version = "0.2.2",   #version of the package, change it when I update your package
    keywords = ("kakuyomu", "epub"),
    description = "Convert kakuyomu articles to one epub file",
    long_description = long_description,
    long_description_content_type='text/markdown',
    license = "MIT Licence",

    url = "https://github.com/XHLin-gamer/kakuyomub",     # project home page
    author = "XHLin-gamer",
    author_email = "earllin@shu.edu.cn",

    packages = find_packages(),
    include_package_data = True,
    platforms = "any",
    install_requires = [
            'grequests',
            'loguru',
            'bs4',
            'jinja2',
            'requests',
            'ebooklib',
            'PrettyPrintTree'
        ]          # the packages that my package depends on
)