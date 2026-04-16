from setuptools import find_packages, setup
import os
from glob import glob

package_name = "ah_ros2_dynamixel"

setup(
    name=package_name,
    version="0.0.0",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages",
         ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
        (os.path.join("share", package_name, "config"), glob("config/*.yaml")),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="aratahorie",
    maintainer_email="aratahorie89@gmail.com",
    description="TODO: Package description",
    license="TODO: License declaration",
    extras_require={
        "test": ["pytest",],
    },
    entry_points={
        "console_scripts": [
            "dyna_handler_node = ah_ros2_dynamixel.dyna_handler_node:main",
            "dyna_handler_node_v2 = ah_ros2_dynamixel.dyna_handler_node_v2:main",
            "dyna_handler_sync_node = ah_ros2_dynamixel.dyna_handler_sync_node:main",
        ],
    },
)
