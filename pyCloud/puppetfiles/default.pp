class { 'python' :
	version		=> 'system',
	pip		=> 'present',
	dev		=> 'absent',
	virtualenv	=> 'absent',
	gunicorn	=> 'absent',
}

node 'node-01' {
	include docker
	include python

	Python::Pip['backports.ssl-match-hostname'] -> Python::Pip['docker-compose']

	python::pip { 'backports.ssl-match-hostname' :
		pkgname		=> 'backports.ssl-match-hostname',
		ensure		=> '3.5.0.1',
	}

	python::pip { 'docker-compose' :
		pkgname		=> 'docker-compose',
		ensure		=> 'present',
#		virtualenv	=> '/var/www/project1',
#		owner		=> 'appuser',
#		install_args	=> '',
	}
}
