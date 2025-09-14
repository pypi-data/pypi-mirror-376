# from setuptools import setup, find_packages
#
# setup(
#     name="api_go_lib",  # ← ИМЕННО ТАК БУДЕТ НАЗЫВАТЬСЯ ПАКЕТ
#     version="0.1.0",
#     description="Простой и удобный HTTP-клиент для работы с API",
#     author="Ваше Имя",
#     author_email="ваш@email.com",
#     packages=find_packages(),
#     install_requires=[
#         "requests>=2.28.0",
#     ],
#     python_requires=">=3.7",
# )

from setuptools import setup, find_packages

setup(
    name="api-go-client",
    version="0.1.0",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    install_requires=["requests>=2.28.0"],
    python_requires=">=3.7",
)