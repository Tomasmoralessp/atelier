# STAGE 1: Build
# Use an official Node image to build the React App
FROM node:24.14.0-alpine AS build

# Set the working directory in the container
WORKDIR /app

# Copy packages and install dependencies
COPY package.json ./
COPY package-lock.json ./

RUN npm install 


COPY . .

RUN npm run build

# STAGE 2: Serve
# Use a lightweight Ngix image to serve the static files
FROM nginx:1.31-alpine

# Copy the built static files from the build stage to the Nginx public html directory
COPY --from=build /app/dist /usr/share/nginx/html

# Copy our custom Nginx configuration file
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port 80 for incoming traffic
EXPOSE 80

# The default Nginx command will start the server
CMD ["nginx", "-g", "daemon off;"]
