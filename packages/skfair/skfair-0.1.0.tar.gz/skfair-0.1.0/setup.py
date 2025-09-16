from setuptools import setup, find_packages

setup(
    name='skfair',
    version='0.1.0',
    author='Justin Lange',
    author_email='langejustin@icloud.com',
    description='A package to capture FAIR-compliant provenance for scikit-learn workflows.',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/jjlange/skfair',
    packages=find_packages(),
    install_requires=[
        'scikit-learn',
        'pandas',
        'numpy',
        'joblib',
        'pyld',
        'requests',
    ],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.8',
    entry_points={
        'console_scripts': [
            'skfair=skfair.cli:main',
        ],
    },
)
