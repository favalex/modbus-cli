from setuptools import setup


def readme():
    with open('README.rst') as f:
        return f.read()


setup(name='modbus_cli',
      version='0.1.8',
      description='Command line tool to access Modbus devices',
      long_description=readme(),
      long_description_content_type='text/x-rst',
      url='http://github.com/favalex/modbus-cli',
      author='Gabriele Favalessa',
      author_email='favalex@gmail.com',
      license='MPL 2.0',
      packages=['modbus_cli'],
      scripts=['bin/modbus'],
      install_requires=['umodbus', 'colorama'],
      zip_safe=False,
      classifiers=[
          'Development Status :: 4 - Beta',
          'Environment :: Console',
          'Intended Audience :: End Users/Desktop',
          'License :: OSI Approved :: Mozilla Public License 2.0 (MPL 2.0)',
          'Operating System :: OS Independent',
          'Programming Language :: Python :: 3',
          'Topic :: Utilities',
      ])
