FROM amsterdam/panorama_image_processing:latest
MAINTAINER datapunt.ois@amsterdam.nl

RUN apt-get update \
	&& apt-get install -y \
		gdal-bin \
		libgeos-dev \
		netcat \
 	&& apt-get clean \
	&& rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* \
	&& adduser --system datapunt \
	&& mkdir -p /static \
	&& chown datapunt /static \
	&& pip install uwsgi

WORKDIR /app
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

USER datapunt
COPY panorama /app/
CMD /app/docker-entrypoint.sh