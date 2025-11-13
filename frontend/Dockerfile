FROM node:20-alpine AS builder

WORKDIR /app

COPY front/package*.json front/angular.json front/tsconfig*.json ./

RUN npm ci

COPY front ./

RUN npm run build


FROM nginx:1.27-alpine

COPY --from=builder /app/dist/front/browser /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
