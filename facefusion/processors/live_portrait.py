from typing import Tuple

import numpy
import scipy

from facefusion.processors.types import LivePortraitExpression, LivePortraitPitch, LivePortraitRoll, LivePortraitRotation, LivePortraitYaw

EXPRESSION_MIN = numpy.array(
[
	[
		[ -2.88067125e-02, -8.12731311e-02, -1.70541159e-03 ],
		[ -4.88598682e-02, -3.32196616e-02, -1.67431499e-04 ],
		[ -6.75425082e-02, -4.28681746e-02, -1.98950816e-04 ],
		[ -7.23103955e-02, -3.28503326e-02, -7.31324719e-04 ],
		[ -3.87073644e-02, -6.01546466e-02, -5.50269964e-04 ],
		[ -6.38048723e-02, -2.23840728e-01, -7.13261834e-04 ],
		[ -3.02710701e-02, -3.93195450e-02, -8.24086510e-06 ],
		[ -2.95799859e-02, -5.39318882e-02, -1.74219604e-04 ],
		[ -2.92359516e-02, -1.53050944e-02, -6.30460854e-05 ],
		[ -5.56493877e-03, -2.34344602e-02, -1.26858242e-04 ],
		[ -4.37593013e-02, -2.77768299e-02, -2.70503685e-02 ],
		[ -1.76926646e-02, -1.91676542e-02, -1.15090821e-04 ],
		[ -8.34268332e-03, -3.99775570e-03, -3.27481248e-05 ],
		[ -3.40162888e-02, -2.81868968e-02, -1.96679524e-04 ],
		[ -2.91855410e-02, -3.97511162e-02, -2.81230678e-05 ],
		[ -1.50395725e-02, -2.49494594e-02, -9.42573533e-05 ],
		[ -1.67938769e-02, -2.00953931e-02, -4.00750607e-04 ],
		[ -1.86435618e-02, -2.48535164e-02, -2.74416432e-02 ],
		[ -4.61211195e-03, -1.21660791e-02, -2.93173041e-04 ],
		[ -4.10017073e-02, -7.43824020e-02, -4.42762971e-02 ],
		[ -1.90370996e-02, -3.74363363e-02, -1.34740388e-02 ]
	]
]).astype(numpy.float32)
EXPRESSION_MAX = numpy.array(
[
	[
		[ 4.46682945e-02, 7.08772913e-02, 4.08344204e-04 ],
		[ 2.14308221e-02, 6.15894832e-02, 4.85319615e-05 ],
		[ 3.02363783e-02, 4.45043296e-02, 1.28298725e-05 ],
		[ 3.05869691e-02, 3.79812494e-02, 6.57040102e-04 ],
		[ 4.45670523e-02, 3.97259220e-02, 7.10966764e-04 ],
		[ 9.43699256e-02, 9.85926315e-02, 2.02551950e-04 ],
		[ 1.61131397e-02, 2.92906128e-02, 3.44733417e-06 ],
		[ 5.23825921e-02, 1.07065082e-01, 6.61510974e-04 ],
		[ 2.85718683e-03, 8.32320191e-03, 2.39314613e-04 ],
		[ 2.57947259e-02, 1.60935968e-02, 2.41853559e-05 ],
		[ 4.90833223e-02, 3.43903080e-02, 3.22353356e-02 ],
		[ 1.44766076e-02, 3.39248963e-02, 1.42291479e-04 ],
		[ 8.75749043e-04, 6.82212645e-03, 2.76097053e-05 ],
		[ 1.86958015e-02, 3.84016186e-02, 7.33085908e-05 ],
		[ 2.01714113e-02, 4.90544215e-02, 2.34028921e-05 ],
		[ 2.46518422e-02, 3.29151377e-02, 3.48571630e-05 ],
		[ 2.22457591e-02, 1.21796541e-02, 1.56396593e-04 ],
		[ 1.72109623e-02, 3.01626958e-02, 1.36556877e-02 ],
		[ 1.83460284e-02, 1.61141958e-02, 2.87440169e-04 ],
		[ 3.57594155e-02, 1.80554688e-01, 2.75554154e-02 ],
		[ 2.17450950e-02, 8.66811201e-02, 3.34241726e-02 ]
	]
]).astype(numpy.float32)


def limit_expression(expression : LivePortraitExpression) -> LivePortraitExpression:
	return numpy.clip(expression, EXPRESSION_MIN, EXPRESSION_MAX)


def limit_euler_angles(target_pitch : LivePortraitPitch, target_yaw : LivePortraitYaw, target_roll : LivePortraitRoll, output_pitch : LivePortraitPitch, output_yaw : LivePortraitYaw, output_roll : LivePortraitRoll) -> Tuple[LivePortraitPitch, LivePortraitYaw, LivePortraitRoll]:
	pitch_min, pitch_max, yaw_min, yaw_max, roll_min, roll_max = calc_euler_limits(target_pitch, target_yaw, target_roll)
	output_pitch = numpy.clip(output_pitch, pitch_min, pitch_max)
	output_yaw = numpy.clip(output_yaw, yaw_min, yaw_max)
	output_roll = numpy.clip(output_roll, roll_min, roll_max)
	return output_pitch, output_yaw, output_roll


def calc_euler_limits(pitch : LivePortraitPitch, yaw : LivePortraitYaw, roll : LivePortraitRoll) -> Tuple[float, float, float, float, float, float]:
	pitch_min = -30.0
	pitch_max = 30.0
	yaw_min = -60.0
	yaw_max = 60.0
	roll_min = -20.0
	roll_max = 20.0

	if pitch < 0:
		pitch_min = min(pitch, pitch_min)
	else:
		pitch_max = max(pitch, pitch_max)
	if yaw < 0:
		yaw_min = min(yaw, yaw_min)
	else:
		yaw_max = max(yaw, yaw_max)
	if roll < 0:
		roll_min = min(roll, roll_min)
	else:
		roll_max = max(roll, roll_max)

	return pitch_min, pitch_max, yaw_min, yaw_max, roll_min, roll_max


def create_rotation(pitch : LivePortraitPitch, yaw : LivePortraitYaw, roll : LivePortraitRoll) -> LivePortraitRotation:
	rotation = scipy.spatial.transform.Rotation.from_euler('xyz', [ pitch, yaw, roll ], degrees = True).as_matrix()
	rotation = rotation.astype(numpy.float32)
	return rotation
