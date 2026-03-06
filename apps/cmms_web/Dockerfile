FROM nginx:1.27-alpine
RUN printf '<html><body><h1>ManPlan CMMS (placeholder)</h1><p>API: <span id="api"></span></p><script>document.getElementById("api").innerText=(window.VITE_API_BASE_URL||"");</script></body></html>' > /usr/share/nginx/html/index.html
EXPOSE 80