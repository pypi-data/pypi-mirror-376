from setuptools import find_packages, setup

with open('README.md', 'r') as r:
	long_description = r.read()

setup(
	name='frpy',
	version='0.3.0',
	description="An api wrapper for Free Rider HD",
	long_description=long_description,
	long_description_content_type='text/markdown',
	author='Calculamatrise',
	url="https://github.com/Calculamatrise/frpy",
	project_urls={
        "Source": "https://github.com/Calculamatrise/frpy",
        "Bug Tracker": "https://github.com/Calculamatrise/frpy/issues",
    },
	keywords=[
		'api',
		'bot',
		'frhd',
		'frhd-api',
		'freeriderhd',
		'freeriderhd-api'
	],
	license='GPL-3.0 license',
	classifiers=[
		"Intended Audience :: Developers",
		"Programming Language :: Python :: 3",
		"Programming Language :: Python :: 3.8",
		"Programming Language :: Python :: 3.9",
		"Programming Language :: Python :: 3.10",
		"Programming Language :: Python :: 3.11",
		"Programming Language :: Python :: 3.12",
		"License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
	],
	packages=find_packages(),
	python_requires='>=3.8',
	install_requires=['requests']
)

# python -m build
# python -m twine upload -r testpypi dist/*
# python -m twine upload -r pypi dist/*