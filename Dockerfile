FROM nginx:alpine

# Copy your index.html to Nginx's default HTML directory
COPY index.html /usr/share/nginx/html/index.html

# Expose port 80
EXPOSE 80
