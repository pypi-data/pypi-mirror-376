from setuptools import setup, find_packages

setup(
    name='spark_submit_k8s_pod_operator',
    version='1.0.2',
    packages=find_packages(),
    install_requires=[
    ],
    entry_points={
        "console_scripts": [
            "spark-submit-k8s-pod-operator = spark_submit_k8s_pod_operator:hello",
        ],
    },
)
