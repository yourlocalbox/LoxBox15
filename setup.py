from setuptools import setup, find_packages

setup(
    name="localbox",
    version="1.6.0",
    packages=find_packages(),
    data_files=[
        ('/usr/bin/', ['scripts/localbox.sh']),
        ('/etc/systemd/system/', ['scripts/localbox.service']),
    ],
    include_package_data=True,
    description='Backend implementation of LocalBox',
    author="De Staat der Nederlanden",
    maintainer="De Staat der Nederlanden",
    author_email="info@yourlocalbox.org",
    maintainer_email="info@yourlocalbox.org",
    url="https://yourlocalbox.org",
    license="EUPL"
)
