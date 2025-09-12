import re

from setuptools import setup

EXTRAS_REQUIRE = {
    "docs": ("sphinx", "pallets-sphinx-themes"),
    "jwt": ("PyJWT>=2.0.0", "cryptography>=2.0.0"),
    "tests": ("coverage", "psycopg2-binary", "pytest"),
}
EXTRAS_REQUIRE["dev"] = (
    EXTRAS_REQUIRE["docs"] + EXTRAS_REQUIRE["tests"] + ("tox",)
)


def find_version(fname):
    """Attempts to find the version number in the file names fname.
    Raises RuntimeError if not found.
    """
    version = ""
    with open(fname) as fp:
        reg = re.compile(r'__version__ = [\'"]([^\'"]*)[\'"]')
        for line in fp:
            m = reg.match(line)
            if m:
                version = m.group(1)
                break
    if not version:
        raise RuntimeError("Cannot find version information")
    return version


setup(
    name="Flask-RESTy",
    version=find_version("flask_resty/__init__.py"),
    description="Building blocks for REST APIs for Flask",
    url="https://github.com/4Catalyzer/flask-resty",
    author="4Catalyzer",
    author_email="tesrin@gmail.com",
    license="MIT",
    python_requires=">=3.10",
    classifiers=[
        "Framework :: Flask",
        "Environment :: Web Environment",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3 :: Only",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    keywords="rest flask",
    packages=[
        "flask_resty",
    ],
    install_requires=(
        # core deps
        "flask~=3.0.0",
        "flask-sqlalchemy~=3.0",
        "sqlalchemy~=2.0.0",
        # misc
        "marshmallow>=3.20.0",
        "werkzeug>=3.0",
        "konch>=4.0",
    ),
    extras_require=EXTRAS_REQUIRE,
    entry_points={
        "pytest11": ("flask-resty = flask_resty.testing",),
        "flask.commands": ("shell = flask_resty.shell:cli",),
    },
)
