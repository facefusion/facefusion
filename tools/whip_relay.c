#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <pthread.h>
#include <sys/time.h>
#include <signal.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <rtc/rtc.h>

#define MAX_SESSIONS 16
#define MAX_VIEWERS 8
#define MAX_TRACKS 4
#define SDP_BUF_SIZE 16384
#define HTTP_BUF_SIZE 65536

typedef struct
{
	int pc;
	int tracks[MAX_TRACKS];
	int track_count;
	int audio_track;
	int connected;
} Viewer;

typedef struct
{
	char path[256];
	int rtp_port;
	int rtp_fd;
	int audio_port;
	int audio_fd;
	Viewer viewers[MAX_VIEWERS];
	int viewer_count;
	int active;
	uint32_t audio_pts;
	pthread_mutex_t lock;
} Session;

typedef struct
{
	Session *session;
	int viewer_index;
	int gathering_done;
	pthread_mutex_t gather_lock;
	pthread_cond_t gather_cond;
} ViewerCtx;

static Session sessions[MAX_SESSIONS];
static pthread_mutex_t sessions_lock = PTHREAD_MUTEX_INITIALIZER;
static volatile int running = 1;
static int next_rtp_port = 15000;

static Session *find_session(const char *path)
{
	for (int i = 0; i < MAX_SESSIONS; i++)
	{
		if (sessions[i].active && strcmp(sessions[i].path, path) == 0)
		{
			return &sessions[i];
		}
	}
	return NULL;
}

static double get_elapsed_seconds(struct timeval *start)
{
	struct timeval now;
	gettimeofday(&now, NULL);
	return (now.tv_sec - start->tv_sec) + (now.tv_usec - start->tv_usec) / 1000000.0;
}

static void *rtp_receiver_thread(void *arg)
{
	Session *session = (Session *)arg;
	char buf[256 * 1024];
	struct timeval start_time;
	int started = 0;

	while (running && session->active)
	{
		struct sockaddr_in from;
		socklen_t fromlen = sizeof(from);
		int n = recvfrom(session->rtp_fd, buf, sizeof(buf), 0, (struct sockaddr *)&from, &fromlen);

		if (n <= 0)
		{
			continue;
		}

		if (!started)
		{
			gettimeofday(&start_time, NULL);
			started = 1;
		}

		double elapsed = get_elapsed_seconds(&start_time);
		uint32_t timestamp = (uint32_t)(elapsed * 90000.0);

		pthread_mutex_lock(&session->lock);

		for (int v = 0; v < session->viewer_count; v++)
		{
			Viewer *viewer = &session->viewers[v];

			if (!viewer->connected)
			{
				continue;
			}

			for (int t = 0; t < viewer->track_count; t++)
			{
				if (!rtcIsOpen(viewer->tracks[t]))
				{
					continue;
				}

				rtcSetTrackRtpTimestamp(viewer->tracks[t], timestamp);
				rtcSendMessage(viewer->tracks[t], buf, n);
			}
		}

		pthread_mutex_unlock(&session->lock);
	}

	return NULL;
}

static void *audio_receiver_thread(void *arg)
{
	Session *session = (Session *)arg;
	char buf[4096];

	while (running && session->active)
	{
		struct sockaddr_in from;
		socklen_t fromlen = sizeof(from);
		int n = recvfrom(session->audio_fd, buf, sizeof(buf), 0, (struct sockaddr *)&from, &fromlen);

		if (n <= 0)
		{
			continue;
		}

		uint32_t ts = session->audio_pts;
		session->audio_pts += 960;

		pthread_mutex_lock(&session->lock);

		for (int v = 0; v < session->viewer_count; v++)
		{
			Viewer *viewer = &session->viewers[v];

			if (!viewer->connected || viewer->audio_track <= 0)
			{
				continue;
			}

			if (!rtcIsOpen(viewer->audio_track))
			{
				continue;
			}

			rtcSetTrackRtpTimestamp(viewer->audio_track, ts);
			rtcSendMessage(viewer->audio_track, buf, n);
		}

		pthread_mutex_unlock(&session->lock);
	}

	return NULL;
}

static Session *create_session_slot(const char *path)
{
	for (int i = 0; i < MAX_SESSIONS; i++)
	{
		if (!sessions[i].active)
		{
			memset(&sessions[i], 0, sizeof(Session));
			strncpy(sessions[i].path, path, sizeof(sessions[i].path) - 1);
			sessions[i].active = 1;
			sessions[i].rtp_port = next_rtp_port++;
			pthread_mutex_init(&sessions[i].lock, NULL);

			int fd = socket(AF_INET, SOCK_DGRAM, 0);
			struct sockaddr_in addr;
			memset(&addr, 0, sizeof(addr));
			addr.sin_family = AF_INET;
			addr.sin_addr.s_addr = inet_addr("127.0.0.1");
			addr.sin_port = htons(sessions[i].rtp_port);

			if (bind(fd, (struct sockaddr *)&addr, sizeof(addr)) < 0)
			{
				perror("bind rtp");
				close(fd);
				sessions[i].active = 0;
				return NULL;
			}

			struct timeval tv;
			tv.tv_sec = 1;
			tv.tv_usec = 0;
			setsockopt(fd, SOL_SOCKET, SO_RCVTIMEO, &tv, sizeof(tv));

			sessions[i].rtp_fd = fd;

			sessions[i].audio_port = next_rtp_port++;
			int afd = socket(AF_INET, SOCK_DGRAM, 0);
			struct sockaddr_in aaddr;
			memset(&aaddr, 0, sizeof(aaddr));
			aaddr.sin_family = AF_INET;
			aaddr.sin_addr.s_addr = inet_addr("127.0.0.1");
			aaddr.sin_port = htons(sessions[i].audio_port);
			bind(afd, (struct sockaddr *)&aaddr, sizeof(aaddr));
			setsockopt(afd, SOL_SOCKET, SO_RCVTIMEO, &tv, sizeof(tv));
			sessions[i].audio_fd = afd;
			sessions[i].audio_pts = 0;

			pthread_t tid;
			pthread_create(&tid, NULL, rtp_receiver_thread, &sessions[i]);
			pthread_detach(tid);

			pthread_t atid;
			pthread_create(&atid, NULL, audio_receiver_thread, &sessions[i]);
			pthread_detach(atid);

			return &sessions[i];
		}
	}
	return NULL;
}

static ViewerCtx viewer_contexts[MAX_SESSIONS * MAX_VIEWERS];
static int viewer_ctx_count = 0;

static void on_viewer_state(int pc, rtcState state, void *ptr)
{
	ViewerCtx *ctx = (ViewerCtx *)ptr;

	if (state == RTC_CONNECTED && ctx->session)
	{
		pthread_mutex_lock(&ctx->session->lock);

		if (ctx->viewer_index < ctx->session->viewer_count)
		{
			ctx->session->viewers[ctx->viewer_index].connected = 1;
		}

		pthread_mutex_unlock(&ctx->session->lock);
	}
}

static void on_viewer_gathering(int pc, rtcGatheringState state, void *ptr)
{
	ViewerCtx *ctx = (ViewerCtx *)ptr;

	if (state == RTC_GATHERING_COMPLETE)
	{
		pthread_mutex_lock(&ctx->gather_lock);
		ctx->gathering_done = 1;
		pthread_cond_signal(&ctx->gather_cond);
		pthread_mutex_unlock(&ctx->gather_lock);
	}
}

static int create_viewer_pc(Session *session, const char *offer_sdp, char *answer_buf, int answer_size)
{
	if (session->viewer_count >= MAX_VIEWERS)
	{
		return -1;
	}

	rtcConfiguration config;
	memset(&config, 0, sizeof(config));
	config.forceMediaTransport = true;
	config.enableIceUdpMux = true;

	int pc = rtcCreatePeerConnection(&config);

	if (pc < 0)
	{
		return -1;
	}

	ViewerCtx *ctx = &viewer_contexts[viewer_ctx_count++];
	ctx->session = session;
	ctx->viewer_index = session->viewer_count;
	ctx->gathering_done = 0;
	pthread_mutex_init(&ctx->gather_lock, NULL);
	pthread_cond_init(&ctx->gather_cond, NULL);

	Viewer *viewer = &session->viewers[session->viewer_count];
	viewer->pc = pc;
	viewer->connected = 0;
	viewer->track_count = 0;

	rtcSetUserPointer(pc, ctx);
	rtcSetGatheringStateChangeCallback(pc, on_viewer_gathering);
	rtcSetStateChangeCallback(pc, on_viewer_state);

	int video_track = rtcAddTrack(pc,
		"m=video 9 UDP/TLS/RTP/SAVPF 96\r\n"
		"a=rtpmap:96 VP8/90000\r\n"
		"a=sendonly\r\na=mid:0\r\na=rtcp-mux\r\n");

	if (video_track >= 0)
	{
		rtcPacketizerInit packetizer;
		memset(&packetizer, 0, sizeof(packetizer));
		packetizer.ssrc = 42;
		packetizer.cname = "video";
		packetizer.payloadType = 96;
		packetizer.clockRate = 90000;
		packetizer.maxFragmentSize = 1200;
		rtcSetVP8Packetizer(video_track, &packetizer);
		rtcChainRtcpSrReporter(video_track);
		rtcChainRtcpNackResponder(video_track, 512);

		viewer->tracks[viewer->track_count++] = video_track;
	}

	int audio_track = rtcAddTrack(pc,
		"m=audio 9 UDP/TLS/RTP/SAVPF 111\r\n"
		"a=rtpmap:111 opus/48000/2\r\n"
		"a=sendonly\r\na=mid:1\r\na=rtcp-mux\r\n");

	if (audio_track >= 0)
	{
		rtcPacketizerInit audio_packetizer;
		memset(&audio_packetizer, 0, sizeof(audio_packetizer));
		audio_packetizer.ssrc = 43;
		audio_packetizer.cname = "audio";
		audio_packetizer.payloadType = 111;
		audio_packetizer.clockRate = 48000;
		rtcSetOpusPacketizer(audio_track, &audio_packetizer);
		rtcChainRtcpSrReporter(audio_track);
		viewer->audio_track = audio_track;
	}

	rtcSetRemoteDescription(pc, offer_sdp, "offer");

	struct timespec ts;
	clock_gettime(CLOCK_REALTIME, &ts);
	ts.tv_sec += 5;

	pthread_mutex_lock(&ctx->gather_lock);

	while (!ctx->gathering_done)
	{
		if (pthread_cond_timedwait(&ctx->gather_cond, &ctx->gather_lock, &ts) != 0)
		{
			break;
		}
	}

	pthread_mutex_unlock(&ctx->gather_lock);

	int len = rtcGetLocalDescription(pc, answer_buf, answer_size);

	if (len < 0)
	{
		return -1;
	}

	pthread_mutex_lock(&session->lock);
	session->viewer_count++;
	pthread_mutex_unlock(&session->lock);

	return 0;
}

static void parse_http_request(const char *buf, int len, char *method, char *path, char *body, int *body_len)
{
	method[0] = 0;
	path[0] = 0;
	body[0] = 0;
	*body_len = 0;

	sscanf(buf, "%15s %255s", method, path);

	const char *body_start = strstr(buf, "\r\n\r\n");

	if (body_start)
	{
		body_start += 4;
		*body_len = len - (body_start - buf);

		if (*body_len > 0)
		{
			memcpy(body, body_start, *body_len);
			body[*body_len] = 0;
		}
	}
}

static void send_http_response(int fd, int status, const char *content_type, const char *body, int body_len)
{
	char header[1024];
	const char *status_text = status == 201 ? "Created" : status == 200 ? "OK" : "Not Found";

	int hlen = snprintf(header, sizeof(header),
		"HTTP/1.1 %d %s\r\n"
		"Content-Type: %s\r\n"
		"Content-Length: %d\r\n"
		"Access-Control-Allow-Origin: *\r\n"
		"Access-Control-Allow-Methods: POST, DELETE, OPTIONS, GET\r\n"
		"Access-Control-Allow-Headers: Content-Type\r\n"
		"Connection: close\r\n"
		"\r\n",
		status, status_text, content_type, body_len);

	write(fd, header, hlen);

	if (body_len > 0)
	{
		write(fd, body, body_len);
	}
}

static void handle_client(int client_fd)
{
	char buf[HTTP_BUF_SIZE];
	int total = 0;
	int n;

	while (total < HTTP_BUF_SIZE - 1)
	{
		n = read(client_fd, buf + total, HTTP_BUF_SIZE - 1 - total);

		if (n <= 0)
		{
			break;
		}

		total += n;

		if (strstr(buf, "\r\n\r\n"))
		{
			int content_length = 0;
			char *cl = strstr(buf, "Content-Length:");

			if (!cl)
			{
				cl = strstr(buf, "content-length:");
			}

			if (cl)
			{
				content_length = atoi(cl + 15);
			}

			char *body_start = strstr(buf, "\r\n\r\n") + 4;
			int header_len = body_start - buf;
			int body_so_far = total - header_len;

			while (body_so_far < content_length && total < HTTP_BUF_SIZE - 1)
			{
				n = read(client_fd, buf + total, HTTP_BUF_SIZE - 1 - total);

				if (n <= 0)
				{
					break;
				}

				total += n;
				body_so_far = total - header_len;
			}

			break;
		}
	}

	buf[total] = 0;

	char method[16], path[256], body[SDP_BUF_SIZE];
	int body_len;
	parse_http_request(buf, total, method, path, body, &body_len);

	if (strcmp(method, "OPTIONS") == 0)
	{
		send_http_response(client_fd, 200, "text/plain", "", 0);
		close(client_fd);
		return;
	}

	if (strcmp(method, "GET") == 0 && strcmp(path, "/health") == 0)
	{
		send_http_response(client_fd, 200, "text/plain", "ok", 2);
		close(client_fd);
		return;
	}

	if (strcmp(method, "POST") == 0 && strstr(path, "/create"))
	{
		char stream_path[256];
		strncpy(stream_path, path + 1, sizeof(stream_path) - 1);
		char *create_pos = strstr(stream_path, "/create");

		if (create_pos)
		{
			*create_pos = 0;
		}

		pthread_mutex_lock(&sessions_lock);
		Session *session = find_session(stream_path);

		if (!session)
		{
			session = create_session_slot(stream_path);
		}

		pthread_mutex_unlock(&sessions_lock);

		if (session)
		{
			char port_str[64];
			snprintf(port_str, sizeof(port_str), "%d,%d", session->rtp_port, session->audio_port);
			send_http_response(client_fd, 200, "text/plain", port_str, strlen(port_str));
		}
		else
		{
			send_http_response(client_fd, 500, "text/plain", "failed", 6);
		}

		close(client_fd);
		return;
	}

	if (strcmp(method, "GET") == 0 && strncmp(path, "/session/", 9) == 0)
	{
		const char *check_path = path + 9;
		pthread_mutex_lock(&sessions_lock);
		Session *s = find_session(check_path);
		pthread_mutex_unlock(&sessions_lock);

		if (s)
		{
			send_http_response(client_fd, 200, "text/plain", "ok", 2);
		}
		else
		{
			send_http_response(client_fd, 404, "text/plain", "no", 2);
		}

		close(client_fd);
		return;
	}

	if (strcmp(method, "POST") != 0 || !strstr(path, "/whep"))
	{
		send_http_response(client_fd, 404, "text/plain", "not found", 9);
		close(client_fd);
		return;
	}

	char stream_path[256];
	char *whep_pos = strstr(path + 1, "/whep");
	int plen = whep_pos - path - 1;
	strncpy(stream_path, path + 1, plen);
	stream_path[plen] = 0;

	char answer[SDP_BUF_SIZE];

	pthread_mutex_lock(&sessions_lock);
	Session *session = find_session(stream_path);
	pthread_mutex_unlock(&sessions_lock);

	if (!session)
	{
		send_http_response(client_fd, 404, "text/plain", "no session", 10);
		close(client_fd);
		return;
	}

	int rc = create_viewer_pc(session, body, answer, SDP_BUF_SIZE);

	if (rc < 0)
	{
		send_http_response(client_fd, 500, "text/plain", "failed", 6);
	}
	else
	{
		send_http_response(client_fd, 201, "application/sdp", answer, strlen(answer));
	}

	close(client_fd);
}

static void signal_handler(int sig)
{
	running = 0;
}

int main(int argc, char *argv[])
{
	int port = 8891;

	if (argc > 1)
	{
		port = atoi(argv[1]);
	}

	signal(SIGINT, signal_handler);
	signal(SIGTERM, signal_handler);

	rtcInitLogger(RTC_LOG_WARNING, NULL);

	memset(sessions, 0, sizeof(sessions));

	int server_fd = socket(AF_INET, SOCK_STREAM, 0);

	if (server_fd < 0)
	{
		perror("socket");
		return 1;
	}

	int opt = 1;
	setsockopt(server_fd, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt));

	struct sockaddr_in addr;
	memset(&addr, 0, sizeof(addr));
	addr.sin_family = AF_INET;
	addr.sin_addr.s_addr = INADDR_ANY;
	addr.sin_port = htons(port);

	if (bind(server_fd, (struct sockaddr *)&addr, sizeof(addr)) < 0)
	{
		perror("bind");
		close(server_fd);
		return 1;
	}

	if (listen(server_fd, 16) < 0)
	{
		perror("listen");
		close(server_fd);
		return 1;
	}

	fprintf(stderr, "whip_relay listening on port %d\n", port);

	while (running)
	{
		struct sockaddr_in client_addr;
		socklen_t client_len = sizeof(client_addr);

		int client_fd = accept(server_fd, (struct sockaddr *)&client_addr, &client_len);

		if (client_fd < 0)
		{
			continue;
		}

		handle_client(client_fd);
	}

	close(server_fd);
	rtcCleanup();
	return 0;
}
