from setuptools import setup

from src.sdk.version import sdk_version

setup(
    name="WebexCompassSDK",
    version=sdk_version,
    author="Won Zhou",
    author_email="wanzhou@cisco.com",
    description="A SDK for troubleshooting Webex Meetings",
    py_modules=["sdk/__init__", "sdk/WebexCompassClient","sdk/version", "sdk/ws"],
    data_files=[("", ["README.md"])],
    package_dir={'': 'src'}
)
