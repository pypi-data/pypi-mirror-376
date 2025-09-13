from setuptools import setup, find_packages

setup(
    name="cidwrap", 
    version="0.1.0",  
    description="A FastAPI wrapper for logging correlation events",
    long_description=open("README.md").read(), 
    long_description_content_type="text/markdown",  
    author="Lathiesh",
    author_email="lathieshmahendran24@gmail.com",
    packages=find_packages(where="src"), 
    package_dir={"": "src"},  
    install_requires=[
        "fastapi>=0.111", 
        "asgi-correlation-id>=4.3",
    ],
    classifiers=[  
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",  
)
