node 'node-01' {
	include docker

	docker::run { 'nginx' :
		image		=> 'nginx',
		ports		=> ['80', '80'],
		hostname	=> 'nginx',
	}
}
