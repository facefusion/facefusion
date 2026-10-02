import os
from unittest.mock import patch

from facefusion.apis.session_helper import extract_access_token, validate_api_key


def test_validate_api_key() -> None:
	with patch.dict(os.environ, clear = True):
		assert validate_api_key(None) is True
		assert validate_api_key('') is True
		assert validate_api_key('invalid') is False

	with patch.dict(os.environ, { 'FACEFUSION_API_KEY': 'TEST' }):
		assert validate_api_key('TEST') is True
		assert validate_api_key('invalid') is False
		assert validate_api_key('TEST ') is False
		assert validate_api_key(None) is False
		assert validate_api_key('') is False


def test_extract_access_token() -> None:
	assert extract_access_token(
	{
		'type': 'http',
		'headers': [ (b'authorization', b'Bearer abc') ]
	}) == 'abc'
	assert extract_access_token(
	{
		'type': 'http',
		'headers': [ (b'authorization', b'bearer abc') ]
	}) == 'abc'
	assert extract_access_token(
	{
		'type': 'http',
		'headers': [ (b'authorization', b'Basic abc') ]
	}) is None
	assert extract_access_token(
	{
		'type': 'http',
		'headers': [ (b'authorization', b'Bearer ') ]
	}) is None
	assert extract_access_token(
	{
		'type': 'http',
		'headers': [ (b'authorization', b'Bearer') ]
	}) is None
	assert extract_access_token(
	{
		'type': 'http',
		'headers': []
	}) is None
	assert extract_access_token(
	{
		'type': 'http',
		'headers': [ (b'sec-websocket-protocol', b'access_token.abc') ]
	}) is None
	assert extract_access_token(
	{
		'type': 'websocket',
		'headers': [ (b'sec-websocket-protocol', b'access_token.abc') ]
	}) == 'abc'
	assert extract_access_token(
	{
		'type': 'websocket',
		'headers': [ (b'sec-websocket-protocol', b'access_token.abc, binary') ]
	}) == 'abc'
	assert extract_access_token(
	{
		'type': 'websocket',
		'headers': [ (b'sec-websocket-protocol', b'refresh_token.abc') ]
	}) is None
	assert extract_access_token(
	{
		'type': 'websocket',
		'headers': [ (b'sec-websocket-protocol', b'access_token.') ]
	}) is None
	assert extract_access_token(
	{
		'type': 'websocket',
		'headers': [ (b'authorization', b'Bearer abc') ]
	}) is None
	assert extract_access_token(
	{
		'type': 'lifespan',
		'headers': [ (b'authorization', b'Bearer abc') ]
	}) is None
