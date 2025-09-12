from setuptools import setup, find_packages

setup(
    name="Odin-code-review-github-ai-partner",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "PyGithub>=1.77",
        "requests>=2.31"
    ],
    entry_points={
    "console_scripts": [
        "Odin-code-review-github-ai-partner=ai_code_review.cli:main"
    ]
    },

    python_requires=">=3.8",
    description="Automated AI-powered GitHub Pull Request code review",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="Yassine Laadraoui",
    url="https://github.com/Yassinelaadraoui/AI-Code-Review-Script",
    license="MIT"
)
