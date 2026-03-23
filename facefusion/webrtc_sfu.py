import binascii
import hashlib
import os
import socket
import struct
import threading
import time
from typing import Dict, Optional, Tuple, TypeAlias

import pylibsrtp
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec
from OpenSSL import SSL

from facefusion import logger

SrtpSession : TypeAlias = pylibsrtp.Session
SrtpPolicy : TypeAlias = pylibsrtp.Policy

WHIP_PORT : int = 8890
ICE_UFRAG_LENGTH : int = 4
ICE_PWD_LENGTH : int = 22
RTP_HEADER_SIZE : int = 12

SRTP_PROFILES =\
[
	{
		'name': b'SRTP_AES128_CM_SHA1_80',
		'libsrtp': SrtpPolicy.SRTP_PROFILE_AES128_CM_SHA1_80,
		'key_len': 16,
		'salt_len': 14
	}
]

sessions : Dict[str, dict] = {}
server_cert = None
server_key = None
server_fingerprint : str = ''
udp_socket : Optional[socket.socket] = None
http_thread : Optional[threading.Thread] = None
udp_thread : Optional[threading.Thread] = None
running : bool = False


def generate_credentials() -> None:
	global server_cert, server_key, server_fingerprint

	server_key = ec.generate_private_key(ec.SECP256R1(), default_backend())
	name = x509.Name([x509.NameAttribute(x509.NameOID.COMMON_NAME, binascii.hexlify(os.urandom(16)).decode())])
	import datetime
	now = datetime.datetime.now(tz = datetime.timezone.utc)
	builder = x509.CertificateBuilder().subject_name(name).issuer_name(name).public_key(server_key.public_key()).serial_number(x509.random_serial_number()).not_valid_before(now - datetime.timedelta(days = 1)).not_valid_after(now + datetime.timedelta(days = 30))
	server_cert = builder.sign(server_key, hashes.SHA256(), default_backend())
	fp = server_cert.fingerprint(hashes.SHA256()).hex().upper()
	server_fingerprint = ':'.join(fp[i:i + 2] for i in range(0, len(fp), 2))


def generate_ice_credentials() -> Tuple[str, str]:
	ufrag = binascii.hexlify(os.urandom(ICE_UFRAG_LENGTH)).decode()
	pwd = binascii.hexlify(os.urandom(ICE_PWD_LENGTH)).decode()[:ICE_PWD_LENGTH]
	return ufrag, pwd


def parse_sdp_offer(sdp : str) -> dict:
	result = {'ice_ufrag': '', 'ice_pwd': '', 'fingerprint': '', 'setup': '', 'media': [], 'candidates': []}
	current_media = None

	for line in sdp.splitlines():
		line = line.strip()

		if line.startswith('a=ice-ufrag:'):
			result['ice_ufrag'] = line.split(':', 1)[1]
		if line.startswith('a=ice-pwd:'):
			result['ice_pwd'] = line.split(':', 1)[1]
		if line.startswith('a=fingerprint:'):
			result['fingerprint'] = line.split(' ', 1)[1] if ' ' in line else ''
		if line.startswith('a=setup:'):
			result['setup'] = line.split(':', 1)[1]
		if line.startswith('a=candidate:'):
			result['candidates'].append(line[12:])
		if line.startswith('m='):
			parts = line[2:].split()
			current_media = {'kind': parts[0], 'port': int(parts[1]), 'profile': parts[2], 'formats': parts[3:], 'codec_lines': [], 'mid': None}
			result['media'].append(current_media)
		if current_media:
			if line.startswith('a=rtpmap:') or line.startswith('a=fmtp:') or line.startswith('a=rtcp-fb:'):
				current_media['codec_lines'].append(line)
			if line.startswith('a=mid:'):
				current_media['mid'] = line.split(':', 1)[1]
			if line.startswith('a=extmap:'):
				current_media['codec_lines'].append(line)

	return result


def build_sdp_answer(offer : dict, local_ufrag : str, local_pwd : str, local_port : int) -> str:
	lines = []
	lines.append('v=0')
	lines.append('o=- ' + str(int(time.time())) + ' 1 IN IP4 127.0.0.1')
	lines.append('s=-')
	lines.append('t=0 0')

	mids = []
	for i, media in enumerate(offer.get('media', [])):
		mids.append(str(i))

	if mids:
		lines.append('a=group:BUNDLE ' + ' '.join(mids))

	lines.append('a=ice-lite')

	for i, media in enumerate(offer.get('media', [])):
		kind = media.get('kind')
		formats = media.get('formats', [])
		profile = media.get('profile', 'UDP/TLS/RTP/SAVPF')
		mid = media.get('mid', str(i))
		lines.append('m=' + kind + ' 9 ' + profile + ' ' + ' '.join(formats))
		lines.append('c=IN IP4 127.0.0.1')
		lines.append('a=rtcp:9 IN IP4 0.0.0.0')
		lines.append('a=ice-ufrag:' + local_ufrag)
		lines.append('a=ice-pwd:' + local_pwd)
		lines.append('a=ice-options:ice2')
		lines.append('a=fingerprint:sha-256 ' + server_fingerprint)
		lines.append('a=setup:passive')
		lines.append('a=mid:' + mid)
		lines.append('a=rtcp-mux')
		lines.append('a=recvonly')

		for codec_line in media.get('codec_lines', []):
			lines.append(codec_line)

		lines.append('a=candidate:1 1 udp 2130706431 127.0.0.1 ' + str(local_port) + ' typ host')
		lines.append('a=end-of-candidates')

	return '\r\n'.join(lines) + '\r\n'


def build_whep_answer(offer : dict, local_ufrag : str, local_pwd : str, local_port : int, ingest_offer : dict) -> str:
	lines = []
	lines.append('v=0')
	lines.append('o=- ' + str(int(time.time())) + ' 1 IN IP4 127.0.0.1')
	lines.append('s=-')
	lines.append('t=0 0')

	mids = []
	for i, media in enumerate(offer.get('media', [])):
		mid = media.get('mid', str(i))
		mids.append(mid)

	if mids:
		lines.append('a=group:BUNDLE ' + ' '.join(mids))

	lines.append('a=ice-lite')

	for i, media in enumerate(offer.get('media', [])):
		kind = media.get('kind')
		formats = media.get('formats', [])
		profile = media.get('profile', 'UDP/TLS/RTP/SAVPF')
		mid = media.get('mid', str(i))
		lines.append('m=' + kind + ' 9 ' + profile + ' ' + ' '.join(formats))
		lines.append('c=IN IP4 127.0.0.1')
		lines.append('a=rtcp:9 IN IP4 0.0.0.0')
		lines.append('a=ice-ufrag:' + local_ufrag)
		lines.append('a=ice-pwd:' + local_pwd)
		lines.append('a=ice-options:ice2')
		lines.append('a=fingerprint:sha-256 ' + server_fingerprint)
		lines.append('a=setup:passive')
		lines.append('a=mid:' + mid)
		lines.append('a=rtcp-mux')
		lines.append('a=sendonly')

		for codec_line in media.get('codec_lines', []):
			lines.append(codec_line)

		lines.append('a=candidate:1 1 udp 2130706431 127.0.0.1 ' + str(local_port) + ' typ host')
		lines.append('a=end-of-candidates')

	return '\r\n'.join(lines) + '\r\n'


def create_ssl_context() -> SSL.Context:
	ctx = SSL.Context(SSL.DTLS_METHOD)
	ctx.set_verify(SSL.VERIFY_PEER | SSL.VERIFY_FAIL_IF_NO_PEER_CERT, lambda *args: True)
	ctx.use_certificate(server_cert)
	ctx.use_privatekey(server_key)
	ctx.set_cipher_list(b'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES128-SHA')
	ctx.set_tlsext_use_srtp(b'SRTP_AES128_CM_SHA1_80')
	return ctx


def create_session(stream_path : str) -> None:
	ufrag, pwd = generate_ice_credentials()
	sessions[stream_path] = {
		'ice_ufrag': ufrag,
		'ice_pwd': pwd,
		'ingest': None,
		'viewers': [],
		'ingest_offer': None,
		'rx_srtp': None,
		'tx_sessions': []
	}


def destroy_session(stream_path : str) -> None:
	sessions.pop(stream_path, None)


def handle_whip(stream_path : str, sdp_offer : str) -> Optional[str]:
	session = sessions.get(stream_path)

	if not session:
		return None

	offer = parse_sdp_offer(sdp_offer)
	session['ingest_offer'] = offer
	local_port = udp_socket.getsockname()[1] if udp_socket else WHIP_PORT
	answer = build_sdp_answer(offer, session.get('ice_ufrag'), session.get('ice_pwd'), local_port)
	return answer


def handle_whep(stream_path : str, sdp_offer : str) -> Optional[str]:
	session = sessions.get(stream_path)

	if not session:
		return None

	offer = parse_sdp_offer(sdp_offer)
	viewer_ufrag, viewer_pwd = generate_ice_credentials()
	local_port = udp_socket.getsockname()[1] if udp_socket else WHIP_PORT
	ingest_offer = session.get('ingest_offer', offer)
	answer = build_whep_answer(offer, viewer_ufrag, viewer_pwd, local_port, ingest_offer)
	session['viewers'].append({'offer': offer, 'ice_ufrag': viewer_ufrag, 'ice_pwd': viewer_pwd})
	return answer


def start() -> None:
	global running, udp_socket, http_thread

	generate_credentials()
	running = True

	udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	udp_socket.bind(('0.0.0.0', WHIP_PORT))
	udp_socket.settimeout(1.0)

	udp_thread_instance = threading.Thread(target = run_udp_loop, daemon = True)
	udp_thread_instance.start()

	http_thread = threading.Thread(target = run_http_server, daemon = True)
	http_thread.start()
	logger.info('webrtc sfu started on port ' + str(WHIP_PORT), __name__)


def stop() -> None:
	global running, udp_socket

	running = False

	if udp_socket:
		udp_socket.close()
		udp_socket = None


dtls_connections : Dict[tuple, dict] = {}


def run_udp_loop() -> None:
	while running:
		try:
			data, addr = udp_socket.recvfrom(2048)

			if not data:
				continue

			first_byte = data[0]

			if first_byte == 0 or first_byte == 1:
				handle_stun(data, addr)
			if first_byte > 19 and first_byte < 64:
				handle_dtls(data, addr)
			if first_byte > 127 and first_byte < 192:
				handle_srtp(data, addr)

		except socket.timeout:
			continue
		except Exception:
			if running:
				continue


def handle_dtls(data : bytes, addr : tuple) -> None:
	conn = dtls_connections.get(addr)

	if not conn:
		ctx = create_ssl_context()
		ssl_conn = SSL.Connection(ctx)
		ssl_conn.set_accept_state()
		conn = {'ssl': ssl_conn, 'encrypted': False, 'rx_srtp': None, 'tx_srtp': None}
		dtls_connections[addr] = conn

	ssl_conn = conn.get('ssl')
	ssl_conn.bio_write(data)

	try:
		if not conn.get('encrypted'):
			try:
				ssl_conn.do_handshake()
				conn['encrypted'] = True
				setup_srtp_session(conn)
				logger.info('dtls handshake complete with ' + str(addr), __name__)
			except SSL.WantReadError:
				pass
		else:
			try:
				ssl_conn.recv(1500)
			except SSL.ZeroReturnError:
				pass
			except SSL.Error:
				pass
	except Exception:
		pass

	flush_dtls(ssl_conn, addr)


def flush_dtls(ssl_conn : SSL.Connection, addr : tuple) -> None:
	try:
		outdata = ssl_conn.bio_read(1500)

		if outdata:
			udp_socket.sendto(outdata, addr)
	except SSL.Error:
		pass


def setup_srtp_session(conn : dict) -> None:
	ssl_conn = conn.get('ssl')
	ssl_conn.get_selected_srtp_profile()
	key_len = 16
	salt_len = 14
	view = ssl_conn.export_keying_material(b'EXTRACTOR-dtls_srtp', 2 * (key_len + salt_len))
	server_key = view[key_len:2 * key_len] + view[2 * key_len + salt_len:]
	client_key = view[:key_len] + view[2 * key_len:2 * key_len + salt_len]

	rx_policy = SrtpPolicy(key = client_key, ssrc_type = SrtpPolicy.SSRC_ANY_INBOUND, srtp_profile = SrtpPolicy.SRTP_PROFILE_AES128_CM_SHA1_80)
	rx_policy.allow_repeat_tx = True
	rx_policy.window_size = 1024
	conn['rx_srtp'] = SrtpSession(rx_policy)

	tx_policy = SrtpPolicy(key = server_key, ssrc_type = SrtpPolicy.SSRC_ANY_OUTBOUND, srtp_profile = SrtpPolicy.SRTP_PROFILE_AES128_CM_SHA1_80)
	tx_policy.allow_repeat_tx = True
	tx_policy.window_size = 1024
	conn['tx_srtp'] = SrtpSession(tx_policy)


def is_rtcp(data : bytes) -> bool:
	if len(data) < 2:
		return False
	pt = data[1] & 0x7F
	return 64 <= pt <= 95


def handle_srtp(data : bytes, addr : tuple) -> None:
	conn = dtls_connections.get(addr)

	if not conn or not conn.get('rx_srtp'):
		return

	try:
		if is_rtcp(data):
			plain = conn.get('rx_srtp').unprotect_rtcp(data)
		else:
			plain = conn.get('rx_srtp').unprotect(data)

		forward_rtp(plain, addr)
	except Exception:
		pass


def forward_rtp(data : bytes, source_addr : tuple) -> None:
	for other_addr, conn in dtls_connections.items():
		if other_addr == source_addr:
			continue

		if not conn.get('tx_srtp'):
			continue

		try:
			if is_rtcp(data):
				encrypted = conn.get('tx_srtp').protect_rtcp(data)
			else:
				encrypted = conn.get('tx_srtp').protect(data)
			udp_socket.sendto(encrypted, other_addr)
		except Exception:
			pass


def handle_stun(data : bytes, addr : tuple) -> None:
	if len(data) < 20:
		return

	msg_type = struct.unpack('!H', data[0:2])[0]

	if msg_type != 0x0001:
		return

	msg_length = struct.unpack('!H', data[2:4])[0]
	transaction_id = data[8:20]

	username = None
	offset = 20

	while offset < 20 + msg_length:
		if offset + 4 > len(data):
			break
		attr_type = struct.unpack('!H', data[offset:offset + 2])[0]
		attr_length = struct.unpack('!H', data[offset + 2:offset + 4])[0]
		attr_value = data[offset + 4:offset + 4 + attr_length]

		if attr_type == 0x0006:
			username = attr_value.decode('utf-8', errors = 'ignore')

		padded = attr_length + (4 - attr_length % 4) % 4
		offset += 4 + padded

	if not username:
		return

	local_ufrag = username.split(':')[0] if ':' in username else username
	session_pwd = None

	for session in sessions.values():
		if session.get('ice_ufrag') == local_ufrag:
			session_pwd = session.get('ice_pwd')
			break

		for viewer in session.get('viewers', []):
			if viewer.get('ice_ufrag') == local_ufrag:
				session_pwd = viewer.get('ice_pwd')
				break

		if session_pwd:
			break

	if not session_pwd:
		return

	response = build_stun_response(transaction_id, addr, session_pwd)
	udp_socket.sendto(response, addr)


def build_stun_response(transaction_id : bytes, addr : tuple, password : str) -> bytes:
	import hmac
	import zlib

	magic_cookie = 0x2112A442
	magic_bytes = struct.pack('!I', magic_cookie)

	xport = addr[1] ^ (magic_cookie >> 16)
	ip_int = struct.unpack('!I', socket.inet_aton(addr[0]))[0]
	xip = struct.pack('!I', ip_int ^ magic_cookie)
	xor_addr_value = struct.pack('!BBH', 0, 0x01, xport) + xip
	xor_addr_attr = struct.pack('!HH', 0x0020, len(xor_addr_value)) + xor_addr_value

	attrs_before_integrity = xor_addr_attr
	integrity_dummy_len = len(attrs_before_integrity) + 4 + 20
	header_for_hmac = struct.pack('!HH', 0x0101, integrity_dummy_len) + magic_bytes + transaction_id
	key = password.encode('utf-8')
	integrity = hmac.new(key, header_for_hmac + attrs_before_integrity, hashlib.sha1).digest()
	integrity_attr = struct.pack('!HH', 0x0008, 20) + integrity

	attrs_before_fp = attrs_before_integrity + integrity_attr
	fp_dummy_len = len(attrs_before_fp) + 4 + 4
	header_for_fp = struct.pack('!HH', 0x0101, fp_dummy_len) + magic_bytes + transaction_id
	crc = zlib.crc32(header_for_fp + attrs_before_fp) ^ 0x5354554E
	fingerprint_attr = struct.pack('!HHI', 0x8028, 4, crc & 0xFFFFFFFF)

	all_attrs = attrs_before_integrity + integrity_attr + fingerprint_attr
	header = struct.pack('!HH', 0x0101, len(all_attrs)) + magic_bytes + transaction_id
	return header + all_attrs


def run_http_server() -> None:
	from http.server import HTTPServer, BaseHTTPRequestHandler

	class WhipWhepHandler(BaseHTTPRequestHandler):
		def log_message(self, format, *args) -> None:
			pass

		def do_POST(self) -> None:
			path = self.path
			content_length = int(self.headers.get('Content-Length', 0))
			body = self.rfile.read(content_length).decode('utf-8') if content_length else ''

			if path.endswith('/whip'):
				stream_path = path[1:].rsplit('/whip', 1)[0]
				answer = handle_whip(stream_path, body)

				if answer:
					self.send_response(201)
					self.send_header('Content-Type', 'application/sdp')
					self.send_header('Location', path)
					self.send_header('Access-Control-Allow-Origin', '*')
					self.end_headers()
					self.wfile.write(answer.encode('utf-8'))
					return

				self.send_response(404)
				self.end_headers()
				return

			if path.endswith('/whep'):
				stream_path = path[1:].rsplit('/whep', 1)[0]
				answer = handle_whep(stream_path, body)

				if answer:
					self.send_response(201)
					self.send_header('Content-Type', 'application/sdp')
					self.send_header('Location', path)
					self.send_header('Access-Control-Allow-Origin', '*')
					self.end_headers()
					self.wfile.write(answer.encode('utf-8'))
					return

				self.send_response(404)
				self.end_headers()
				return

			self.send_response(404)
			self.end_headers()

		def do_OPTIONS(self) -> None:
			self.send_response(200)
			self.send_header('Access-Control-Allow-Origin', '*')
			self.send_header('Access-Control-Allow-Methods', 'POST, DELETE, OPTIONS')
			self.send_header('Access-Control-Allow-Headers', 'Content-Type')
			self.end_headers()

	server = HTTPServer(('0.0.0.0', WHIP_PORT), WhipWhepHandler)
	server.timeout = 1

	while running:
		server.handle_request()
