import subprocess

from facefusion.installer import install

subprocess.call([ 'pip', 'install' , 'inquirer', '-q' ])


if __name__ == '__main__':
	install()
