FROM python:3.12-slim

# GeoDjango needs GDAL/GEOS/PROJ system libraries — this is why local dev
# is meant to run through Docker rather than a bare virtualenv. See
# ../CLAUDE.md and ../docs/tech-stack-options.md.
RUN apt-get update && apt-get install -y --no-install-recommends \
    gdal-bin \
    libgdal-dev \
    libgeos-dev \
    libproj-dev \
    binutils \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
