FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 5656

# Copy entrypoint script và set quyền
COPY entrypoint.sh .
RUN chmod +x entrypoint.sh

RUN addgroup --system appgroup \
	&& adduser --system --ingroup appgroup appuser \
	&& chown -R appuser:appgroup /app
USER appuser

ENTRYPOINT ["./entrypoint.sh"]
