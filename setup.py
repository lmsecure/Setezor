from setuptools import setup, find_packages
import os
import re


def package_files(directory):
    paths = []
    for (path, directories, filenames) in os.walk(directory):
        for filename in filenames:
            paths.append(os.path.join('..', path, filename))
    return paths

with open("debian/changelog", "r") as file:
    for line in file:
        result = re.findall(r"\((.*)\)", line)
        if result:
            version = result[0]
            break

with open("setezor/requirements.txt", "r") as file:
    requirements = [package.strip() for package in file]

extra_files = package_files('setezor/')

setup(
    name="setezor",
    version=version,
    url="https://github.com/lmsecure/Setezor",
    author="LMSecurity",
    author_email="lm.security@lianmedia.ru",
    description="Multitool for working with network",
    #    long_description=open('README.md').read(),
    #    long_description_content_type='text/markdown',
    license="MIT",
    keywords=['penetration testing', 'network',
              'network intellegence', 'network map'],
    packages=["setezor"],
    package_data={"": extra_files},
    install_requires=requirements,
    entry_points={
        "console_scripts": ["setezor = setezor.__init__:run_app"],
    },
    python_requires='>=3.11,<3.12',
)
