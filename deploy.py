#!/usr/bin/env python

"""Build script for GEO2Enrichr. Manages unit tests, building the Chrome
extension, building the Docker container, and pushing the container.
"""

import argparse
from ConfigParser import ConfigParser
import subprocess
import sys


# Parse user arguments and set defaults
# ============================================================================
ap = argparse.ArgumentParser()
ap.add_argument('--prod',
                help='deploy debug or production version',
                action='store_false')
ap.add_argument('--skiptests',
                help='skip unit tests',
                action='store_true')
ap.add_argument('--build',
                help='build Docker container',
                action='store_true')
ap.add_argument('--image',
                help='Docker image',
                default='maayanlab/g2e:latest')
ap.add_argument('--deploy',
                help='push Docker container',
                action='store_true')
opts = ap.parse_args()
print(opts)


# Run unit tests
# ============================================================================
if opts.skiptests:
    print('Skipping Python unit tests')
else:
    print('Running Python unit tests')
    return_code = subprocess.call('source venv/bin/activate && bash test.sh',
                                  shell=True)
    if return_code != 0:
        raise Warning('Unit tests failed')

# Check for debugger statements.
# ----------------------------------------------------------------------------
try:
    has_pdb_statements = True
    output = subprocess.check_output('grep -r "import pdb" g2e/*', shell=True)
except subprocess.CalledProcessError:
    has_pdb_statements = False
if has_pdb_statements:
    print(output)
    raise Warning('pdb statement(s) found')


# Create front end (if tests pass)
# ============================================================================

# Configure JS
# ----------------------------------------------------------------------------
CHROME_JS_CONFIG = 'g2e/extension/common/js/config-chrome.js'

with open(CHROME_JS_CONFIG, 'w+') as f:
    f.write('// This file is built by deploy.sh in the root directory.\n')
    if opts.prod:
        mode = 'prod'
        debug = 'false'
        server = 'http://amp.pharm.mssm.edu/g2e/'
        id_ = 'pcbdeobileclecleblcnadplfcicfjlp'
    else:
        mode = 'dev'
        debug = 'true'
        server = 'http://localhost:8083/g2e/'
        id_ = 'omkofmggjapmpfpijnnnnpclfejpfpmd'

    print('--------------------- %s ---------------------' % mode)
    f.write('var DEBUG = %s;\n' % debug)
    f.write('var SERVER = "%s";\n' % server)
    f.write('var IMAGE_PATH = "chrome-extension://%s/logo-50x50.png";\n' %
            id_)

# Build JS with Grunt
# ----------------------------------------------------------------------------
print('Building front-end')
return_code = subprocess.call('grunt --gruntfile=scripts/gruntfile.js build > '
                              '/dev/null', shell=True)
if return_code != 0:
    raise Warning('Grunt build failed')

# Manage Docker
# ============================================================================
print('Creating config.ini file.\n')

config_in = ConfigParser()

config_out = ConfigParser()
config_out.add_section('mode')
config_out.add_section('db')
config_out.add_section('cookies')

# Configuration, primarily database connection string.
# ----------------------------------------------------------------------------
if opts.prod:
    config_in.read('g2e/prod.ini')
    config_out.set('mode', 'debug', False)
else:
    config_in.read('g2e/dev.ini')
    config_out.set('mode', 'debug', True)

config_out.set('db', 'uri', config_in.get('db', 'uri'))
config_out.set('cookies', 'secret_key',
               config_in.get('cookies', 'secret_key'))

with open('g2e/config.ini', 'wb') as configfile:
    config_out.write(configfile)

subprocess.call('docker-machine start default', shell=True)
subprocess.call('eval "$(docker-machine env default)"', shell=True)

if opts.build:
    subprocess.call('docker build -t %s .' % opts.image, shell=True)

# Reset DB credentials so we can keep developing locally.
# ----------------------------------------------------------------------------
config_in = ConfigParser()
config_in.read('g2e/dev.ini')

config_out = ConfigParser()
config_out.add_section('mode')
config_out.add_section('db')
config_out.add_section('cookies')
config_out.set('db', 'uri', config_in.get('db', 'uri'))
config_out.set('mode', 'debug', True)
config_out.set('cookies', 'secret_key',
               config_in.get('cookies', 'secret_key'))

with open('g2e/config.ini', 'wb') as configfile:
    config_out.write(configfile)


# Deploy
# =============================================================================
if not opts.deploy:
    print('Not deploying')
    sys.exit(0)

# Push to Docker repo.
# ----------------------------------------------------------------------------
print('Pushing to Docker repo')
subprocess.call('docker push %s' % opts.image, shell=True)
