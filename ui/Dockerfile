FROM nginx:alpine

# Copy HTML file
COPY index.html /usr/share/nginx/html/

# Expose port
EXPOSE 80

# Run nginx
CMD ["nginx", "-g", "daemon off;"]
