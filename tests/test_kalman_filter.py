import numpy

from facefusion.kalman_filter import kalman_initiate, kalman_predict, kalman_update


def test_kalman_predict() -> None:
	mean, covariance = kalman_initiate(numpy.array([ 200.0, 360.0, 0.75, 240.0 ]))
	center_x = 200.0

	for _ in range(40):
		mean, covariance = kalman_predict(mean, covariance)
		center_x += 9.0
		mean, covariance = kalman_update(mean, covariance, numpy.array([ center_x, 360.0, 0.75, 240.0 ]))

	assert round(mean[4]) == 9
