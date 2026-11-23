FROM ghcr.io/astral-sh/uv:0.13.9@sha256:d3b601f0c7b118bc1753febf7c41cc80981df678445e0254284eecf84db79a7d AS uv

FROM python:3.15-alpine3.24@sha256:0f9552bb28711333da16915ec146f5e6bb44a7fdac9ced15dc17c2e0206346dd AS builder

COPY --from=uv /uv /uvx /bin/
ENV UV_LINK_MODE=copy
ENV UV_PYTHON_DOWNLOADS=0

WORKDIR /app

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project --no-dev --no-editable

COPY pyproject.toml uv.lock LICENSE README.md ./
COPY src/ ./src/

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev --no-editable


FROM python:3.15-alpine3.24@sha256:0f9552bb28711333da16915ec146f5e6bb44a7fdac9ced15dc17c2e0206346dd
LABEL org.opencontainers.image.title="NetBox MCP Server" \
      org.opencontainers.image.description="A read-only MCP server for NetBox" \
      org.opencontainers.image.url="https://github.com/netboxlabs/netbox-mcp-server" \
      org.opencontainers.image.source="https://github.com/netboxlabs/netbox-mcp-server" \
      org.opencontainers.image.vendor="NetBox Labs" \
      org.opencontainers.image.licenses="Apache-2.0"
ENV PYTHONUNBUFFERED=1

RUN apk update && apk upgrade --no-cache \
    && python -m pip uninstall --root-user-action=ignore -y pip \
    && addgroup -g 10001 appuser \
    && adduser -D -u 10001 -G appuser appuser

COPY --from=builder /app/.venv /app/.venv

WORKDIR /app

USER 10001:10001

ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8000

CMD ["netbox-mcp-server"]
