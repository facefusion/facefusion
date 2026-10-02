from facefusion.sanitizer import sanitize_int_range, sanitize_job_id


def test_sanitize_job_id() -> None:
	assert sanitize_job_id('job-1') == 'job-1'
	assert sanitize_job_id('job1') == 'job1'
	assert sanitize_job_id('job_1') == '78a95b1969751b433ac41b1e455c528bc43aa2c0'
	assert sanitize_job_id('../../etc/passwd') == '936d7c04cd83ef945f6eac2c4d41e65deb49ce43'
	assert sanitize_job_id('-') == '3bc15c8aae3e4124dd409035f32ea2fd6835efc9'
	assert sanitize_job_id('') == 'da39a3ee5e6b4b0d3255bfef95601890afd80709'


def test_sanitize_int_range() -> None:
	assert sanitize_int_range(0, [ 0, 1, 2 ]) == 0
	assert sanitize_int_range(2, [ 0, 1, 2 ]) == 2
	assert sanitize_int_range(-1, [ 0, 1 ]) == 0
	assert sanitize_int_range(3, [ 0, 1 ]) == 0
	assert sanitize_int_range(3, [ 1, 2 ]) == 1
	assert sanitize_int_range('2', [ 1, 2 ]) == 2
	assert sanitize_int_range(1.9, [ 0, 1, 2 ]) == 1
	assert sanitize_int_range('invalid', [ 1, 2 ]) == 1
	assert sanitize_int_range(None, range(5, 10)) == 5
	assert sanitize_int_range(9, range(5, 10)) == 9
	assert sanitize_int_range(10, range(5, 10)) == 5
