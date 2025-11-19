from setuptools import setup, find_packages

setup(
    name="paddy_procurement",
    version="0.0.1",
    description="Paddy Procurement App for ERPNext v15",
    author="cool020",
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=["frappe"],
)
