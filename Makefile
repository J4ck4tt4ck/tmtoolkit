sdist:
	python setup.py sdist

wheel:
	python setup.py bdist_wheel --universal

#pypi_upload:
#	python setup.py sdist bdist_wheel upload --universal

#pypi_testregister:
#	python setup.py register -r https://testpypi.python.org/pypi

#pypi_testupload:
#	python setup.py sdist bdist_wheel upload -r https://testpypi.python.org/pypi

