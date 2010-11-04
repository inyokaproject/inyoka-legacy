import os, sys
import tempfile, shutil
from os import path

python_version = '2.7'
pil_version = '1.1.7'
cldr_version = '1.7.2'
xapian_version = '1.2.3'


def install_requirements(home_dir, requirements):
    if not requirements:
        return
    home_dir = os.path.abspath(home_dir)
    cmd = [os.path.join(home_dir, 'bin', 'pip')]
    cmd.extend(['install', '-r', os.path.join(home_dir, requirements)])
    call_subprocess(cmd)


def pil_install(home_dir):
    folder = tempfile.mkdtemp(prefix='virtualenv')

    call_subprocess(FETCH_CMD + ['http://effbot.org/downloads/Imaging-%s.tar.gz' % pil_version],
                    cwd=folder)
    call_subprocess(['tar', '-xzf', 'Imaging-%s.tar.gz' % pil_version],
                    cwd=folder)

    img_folder = path.join(folder, 'Imaging-%s' % pil_version)

    f1 = path.join(img_folder, 'setup_new.py')
    f2 = path.join(img_folder, 'setup.py')

    file(f1, 'w').write(file(f2).read().replace('import _tkinter',
                                                'raise ImportError()'))

    cmd = [path.join(home_dir, 'bin', 'python')]
    cmd.extend([path.join(os.getcwd(), f1), 'install'])
    call_subprocess(cmd)

    shutil.rmtree(folder)


def install_xapian(home_dir):
    folder = tempfile.mkdtemp(prefix='virtualenv')
    prefix = os.path.realpath(os.path.join(home_dir))
    pypath = path.join(prefix, 'bin', 'python')
    xapian_config = os.path.join(folder, 'xapian-core-' +
                    xapian_version, 'xapian-config')
    libpath = os.path.join(prefix, 'lib', 'python%s' % python_version)
    incpath = os.path.join(prefix, 'include', 'python%s' % python_version)

    call_subprocess(['wget', 'http://oligarchy.co.uk/xapian/%s/xapian-core-%s.tar.gz' %
                    (xapian_version, xapian_version)], cwd=folder)
    call_subprocess(['tar', '-xzf', 'xapian-core-%s.tar.gz' % xapian_version],
                    cwd=folder)
    call_subprocess(['wget', 'http://oligarchy.co.uk/xapian/%s/xapian-bindings-%s.tar.gz' %
                    (xapian_version, xapian_version)], cwd=folder)

    call_subprocess(['tar', '-xzf', 'xapian-bindings-%s.tar.gz' % xapian_version],
                    cwd=folder)

    core_folder = os.path.join(folder, 'xapian-core-' + xapian_version)
    call_subprocess(['./configure', '--prefix=%s' % prefix], cwd=core_folder)
    call_subprocess(['make'], cwd=core_folder)
    call_subprocess(['make', 'install'], cwd=core_folder)

    binding_folder = os.path.join(folder, 'xapian-bindings-' + xapian_version)
    call_subprocess(['./configure', '--with-python', '--prefix=%s' % prefix,
                    'PYTHON=%s' % pypath,
                    'XAPIAN_CONFIG=%s' % xapian_config,
                    'PYTHON_INC=%s' % incpath,
                    'PYTHON_LIB=%s' % libpath],
                    cwd=binding_folder)
    call_subprocess(['make'], cwd=binding_folder)
    call_subprocess(['make', 'install'], cwd=binding_folder)

    shutil.rmtree(folder)


def babel_svn_repo_install(home_dir):
    folder = tempfile.mkdtemp(prefix='virtualenv')
    pypath = path.join(home_dir, 'bin', 'python')

    # checkout cldr
    call_subprocess(FETCH_CMD + ['http://unicode.org/Public/cldr/%s/core.zip' % cldr_version],
                    cwd=folder)
    call_subprocess(['unzip', '-d', 'cldr', 'core.zip'], cwd=folder)
    cldr_folder = path.join(folder, 'cldr', 'common')

    # checkout babel and import/compile respective cldr
    call_subprocess(['svn', 'co', 'http://svn.edgewall.org/repos/babel/trunk/', 'babel'],
                    cwd=folder)
    babel_folder = path.join(folder, 'babel')
    cmd = [pypath]
    cmd.extend([path.join(os.getcwd(), babel_folder, 'scripts/import_cldr.py'),
                cldr_folder])
    call_subprocess(cmd)

    cmd = [path.abspath(path.join(home_dir, 'bin', 'python'))]
    cmd.extend([path.join(os.getcwd(), path.join(babel_folder, 'setup.py')),
                            'install'])
    call_subprocess(cmd, cwd=babel_folder)
    shutil.rmtree(folder)


def after_install(options, home_dir):
    easy_install('pip', home_dir)
    babel_svn_repo_install(home_dir)
    install_requirements(home_dir, options.requirements)
    pil_install(home_dir)
    install_xapian(home_dir)


def easy_install(package, home_dir, optional_args=None):
    optional_args = optional_args or []
    cmd = [path.join(home_dir, 'bin', 'easy_install')]
    cmd.extend(optional_args)
    # update the environment
    cmd.append('-U')
    cmd.append('-O2')
    cmd.append(package)
    call_subprocess(cmd)


def extend_parser(parser):
    parser.add_option('-r', '--requirements', dest='requirements',
                      default='',
                      help='Path to a requirements file usable with pip')


def adjust_options(options, args):
    global FETCH_CMD, logger

    verbosity = options.verbose - options.quiet
    logger = Logger([(Logger.level_for_integer(2-verbosity), sys.stdout)])

    dest_dir = path.abspath(args[0])

    try:
        call_subprocess(['which', 'wget'], show_stdout=False)
        FETCH_CMD = ['wget', '-c']
    except OSError:
        # wget does not exist, try curl instead
        try:
            call_subprocess(['which', 'curl'], show_stdout=False)
            FETCH_CMD = ['curl', '-L', '-O']
        except OSError:
            sys.stderr.write('\\nERROR: need either wget or curl\\n')
            sys.exit(1)

    # checkout python distribution
    call_subprocess(FETCH_CMD + ['http://python.org/ftp/python/%s/Python-%s.tar.bz2' % (python_version, python_version)],
                    cwd=dest_dir)
    call_subprocess(['tar', '-xjf', 'Python-%s.tar.bz2' % python_version],
                    cwd=dest_dir)

    python_folder = path.join(dest_dir, 'Python-%s' % python_version)

    # configure python
    call_subprocess(['./configure', '--prefix=%s' % dest_dir],
                    cwd=python_folder)
    call_subprocess(['make'], cwd=python_folder)
    call_subprocess(['make', 'install'], cwd=python_folder)

    options.python = path.join(python_folder, 'python')
    options.no_site_packages = True
    options.unzip_setuptools = True
    options.use_distribute = True
