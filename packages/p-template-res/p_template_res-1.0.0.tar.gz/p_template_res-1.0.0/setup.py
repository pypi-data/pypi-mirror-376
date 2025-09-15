import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()
setuptools.setup(
    name="p-template-res",
    version="1.0.0",
    author="pengjun",
    author_email="mr_lonely@foxmail.com",
    description="temple tools",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    py_modules=[],
    install_requires=[
        'requests',
        'mutagen',
    ],
    dependency_links=[],
    entry_points={
        'console_scripts':[
            'template_res = template_res.main:main'
        ]
    },
    python_requires='>=3.7',
)