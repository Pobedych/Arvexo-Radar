FROM node:20-slim AS deps
WORKDIR /app
COPY package.json ./
RUN npm install

FROM deps AS builder
WORKDIR /app
COPY . .
# Next.js inlines NEXT_PUBLIC_* variables into the client bundle at build
# time, not at container start — docker-compose.prod.yml's env_file has no
# effect on this value. CD passes the real value as a --build-arg
# (see .github/workflows/cd.yml); this default only applies to `docker
# compose build web` in local dev.
ARG NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1
ENV NEXT_PUBLIC_API_BASE_URL=$NEXT_PUBLIC_API_BASE_URL
RUN npm run build

FROM node:20-slim AS runner
WORKDIR /app
ENV NODE_ENV=production
COPY --from=builder /app/package.json ./package.json
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/next.config.mjs ./next.config.mjs

EXPOSE 3000

# docker-compose.yml (dev) overrides this with `npm run dev` + bind mounts;
# this CMD is what actually runs in docker-compose.prod.yml.
CMD ["npm", "run", "start"]
