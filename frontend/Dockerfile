# ---- build stage ----
FROM node:22-slim AS build

WORKDIR /app
RUN corepack enable

COPY package.json pnpm-lock.yaml pnpm-workspace.yaml .npmrc ./
RUN pnpm install --frozen-lockfile

COPY . .

# Base URL the browser will use to reach the backend.
ARG VITE_API_BASE=http://localhost:8000
ENV VITE_API_BASE=$VITE_API_BASE

RUN pnpm build

# ---- runtime stage ----
FROM node:22-slim AS runner

WORKDIR /app
ENV NODE_ENV=production \
    PORT=3000 \
    HOST=0.0.0.0

# adapter-node produces a self-contained server bundle.
COPY --from=build /app/build ./build

EXPOSE 3000

CMD ["node", "build/index.js"]
