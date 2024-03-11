from setuptools import setup, find_packages


long_description = open('README.md').read()

with open('requirements.txt') as f:
    requirements = f.read().splitlines()

version = '2.3.0'

setup(
    name='facefusion',
    version=version,
    install_requires=requirements,
    author='Henry Ruhs',
    author_email='hi@avi.im',
    packages=find_packages(),
    include_package_data=True,
    url='https://github.com/facefusion/facefusion',
    license='MIT',
    description='Next generation face swapper and enhancer.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    entry_points={
        'console_scripts': [
            'facefusion = facefusion.run:main_function',
        ]
    },
    classifiers=[],
)