from setuptools import setup, find_packages
import pathlib

here = pathlib.Path(__file__).parent.resolve()

# Get the long description from the README file
long_description = (here / "readme.md").read_text(encoding="utf-8")

setup(
    name='GISterical',
    version='0.5.2',
    license='MIT',
    author="Pavel Cherepanskiy",
    author_email='pavelcherepansky@gmail.com',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    url='https://github.com/pavelcherepan/gisterical',
    long_description=long_description,
    long_description_content_type="text/markdown",
    keywords='example project',
        classifiers=[
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3 :: Only",
    ],
    python_requires=">=3.9, <4",
    install_requires=[
          'loguru', 
          'SQLAlchemy>=1.4', 
          'GeoAlchemy2>=0.12',
          'exif',
          'attrs',
          'ImageHash',
          'Pillow',
          'psycopg2-binary>=2.8'
      ],
    entry_points={
        "console_scripts": [
            "gisterical=gisterical:gisterical",
        ],
    },
)