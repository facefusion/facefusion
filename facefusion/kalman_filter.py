from functools import lru_cache
from typing import Tuple

import numpy
import scipy.linalg

from facefusion.types import KalmanCovariance, KalmanMatrix, KalmanMean, KalmanMeasurement


def kalman_initiate(kalman_measurement : KalmanMeasurement) -> Tuple[KalmanMean, KalmanCovariance]:
	kalman_mean = numpy.r_[kalman_measurement, numpy.zeros_like(kalman_measurement)]
	standard_weight_position = 1.0 / 20
	standard_weight_velocity = 1.0 / 160
	standard_deviation =\
	[
		2 * standard_weight_position * kalman_measurement[3],
		2 * standard_weight_position * kalman_measurement[3],
		1e-2,
		2 * standard_weight_position * kalman_measurement[3],
		10 * standard_weight_velocity * kalman_measurement[3],
		10 * standard_weight_velocity * kalman_measurement[3],
		1e-5,
		10 * standard_weight_velocity * kalman_measurement[3]
	]
	kalman_covariance = numpy.diag(numpy.square(standard_deviation))
	return kalman_mean, kalman_covariance


def kalman_predict(kalman_mean : KalmanMean, kalman_covariance : KalmanCovariance) -> Tuple[KalmanMean, KalmanCovariance]:
	height = kalman_mean[3]
	standard_weight_position = 1.0 / 20
	standard_weight_velocity = 1.0 / 160
	standard_deviation_position = [ standard_weight_position * height, standard_weight_position * height, 1e-2, standard_weight_position * height ]
	standard_deviation_velocity = [ standard_weight_velocity * height, standard_weight_velocity * height, 1e-5, standard_weight_velocity * height ]
	motion_covariance = numpy.diag(numpy.square(numpy.r_[standard_deviation_position, standard_deviation_velocity]))
	motion_matrix = create_static_motion_matrix()
	kalman_mean = numpy.dot(kalman_mean, motion_matrix.T)
	kalman_covariance = numpy.linalg.multi_dot((motion_matrix, kalman_covariance, motion_matrix.T)) + motion_covariance
	return kalman_mean, kalman_covariance


def kalman_project(kalman_mean : KalmanMean, kalman_covariance : KalmanCovariance) -> Tuple[KalmanMeasurement, KalmanCovariance]:
	standard_weight_position = 1.0 / 20
	standard_deviation =\
	[
		standard_weight_position * kalman_mean[3],
		standard_weight_position * kalman_mean[3],
		1e-1,
		standard_weight_position * kalman_mean[3]
	]
	innovation_covariance = numpy.diag(numpy.square(standard_deviation))
	update_matrix = numpy.eye(4, 8)
	projected_mean = numpy.dot(update_matrix, kalman_mean)
	projected_covariance = numpy.linalg.multi_dot((update_matrix, kalman_covariance, update_matrix.T))
	return projected_mean, projected_covariance + innovation_covariance


def kalman_update(kalman_mean : KalmanMean, kalman_covariance : KalmanCovariance, kalman_measurement : KalmanMeasurement) -> Tuple[KalmanMean, KalmanCovariance]:
	projected_mean, projected_covariance = kalman_project(kalman_mean, kalman_covariance)
	chol_factor, lower = scipy.linalg.cho_factor(projected_covariance, lower = True, check_finite = False)
	update_matrix = numpy.eye(4, 8)
	kalman_gain = scipy.linalg.cho_solve((chol_factor, lower), numpy.dot(kalman_covariance, update_matrix.T).T, check_finite = False).T
	innovation = kalman_measurement - projected_mean
	kalman_mean = kalman_mean + numpy.dot(innovation, kalman_gain.T)
	kalman_covariance = kalman_covariance - numpy.linalg.multi_dot((kalman_gain, projected_covariance, kalman_gain.T))
	return kalman_mean, kalman_covariance


@lru_cache()
def create_static_motion_matrix() -> KalmanMatrix:
	motion_matrix = numpy.eye(8, 8)

	for index in range(4):
		motion_matrix[index, 4 + index] = 1.0
	return motion_matrix
