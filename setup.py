from setuptools import setup

setup(name='modbus-cli',
      version='0.1.0',
      description='Command line tool to access Modbus devices',
      url='http://github.com/favalex/modbus-cli',
      author='Gabriele Favalessa',
      author_email='favalex@gmail.com',
      license='MPL 2.0',
      scripts=['bin/modbus'],
      install_requires=[ 'umodbus', ],
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
