FROM python:3.12-alpine

COPY . statistics_server
RUN pip install --upgrade pip
RUN pip install statistics_server/

EXPOSE 8081

ENTRYPOINT [ "gunicorn", "statistics_server.app:server", \
	"--bind", "0.0.0.0:8081", "--error-logfile" , "-" , \
	"--access-logfile", "-", "--log-level=info", "--access-logformat", \
	"[statistics-server] %(h)s %(l)s %(t)s '%(r)s' %(s)s %(b)s '%(f)s' '%(a)s'"\
	]
